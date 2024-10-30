import requests
import json
import io
from pydub import AudioSegment
from pydub.playback import play
import openai
import os
import speech_recognition as sr

# 環境変数からAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# VOICEVOXをインストールしたPCのホスト名を指定してください
HOSTNAME = 'localhost'
speaker = 3  # 話者ID

# ChatGPTとの対話関数
def chat_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは元気で親しみやすいウサギのマスコットです。必ず日本語で返答してください。スーパーマーケットでお客様が商品を見つけられるように案内します。カジュアルな口調で、簡潔でわかりやすい日本語で返答してください。また、できるだけ短めな返答を意識してください"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    return response['choices'][0]['message']['content']

# VOICEVOXで音声再生する関数
def play_with_voicevox(text):
    # audio_query (音声合成用のクエリを作成するAPI)
    res1 = requests.post(f'http://{HOSTNAME}:50021/audio_query',
                         params={'text': text, 'speaker': speaker})
    # synthesis (音声合成するAPI)
    res2 = requests.post(f'http://{HOSTNAME}:50021/synthesis',
                         params={'speaker': speaker},
                         data=json.dumps(res1.json()))

    # バイナリデータをAudioSegmentに変換して即時再生
    audio_data = AudioSegment.from_file(io.BytesIO(res2.content), format="wav")
    play(audio_data)

# メイン関数
def main():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1  # 話の間の無音が1秒以上でも続ける
    recognizer.phrase_threshold = 0.3  # 話し始めと判断する時間

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("音声認識を開始します。終了するには '終了' または '終わり' と言ってください。")

        while True:
            print("話しかけてください...")
            audio = recognizer.listen(source)

            try:
                user_input = recognizer.recognize_google(audio, language="ja-JP")
                print(f"あなたの質問: {user_input}")
                
                # 終了条件
                if user_input.lower() in ["終了", "終わり"]:
                    print("終了します。")
                    break
                
                # ChatGPTからの応答
                answer = chat_with_gpt(user_input)
                print(f"ChatGPT: {answer}")

                # VOICEVOXで応答を再生
                play_with_voicevox(answer)

            except sr.UnknownValueError:
                print("聞き取れませんでした。もう一度お願いします。")
            except sr.RequestError as e:
                print(f"音声認識サービスにアクセスできません: {e}")

if __name__ == "__main__":
    main()
