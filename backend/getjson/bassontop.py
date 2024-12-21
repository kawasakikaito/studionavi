import os
import re
import requests
import json

# 保存先ディレクトリとファイルパス
SAVE_DIR = "./json"
FILE_NAME = "bassontop"
HTML_FILE = os.path.join(SAVE_DIR, FILE_NAME + ".html")
RESULT_FILE = os.path.join(SAVE_DIR, FILE_NAME + ".json")

# 保存先ディレクトリを作成
os.makedirs(SAVE_DIR, exist_ok=True)

# セッションを作成
session = requests.Session()

# HTMLを取得
print("HTMLを取得中...")
response = session.get("https://studi-ol.com/shop/680")
if response.status_code != 200 or not response.text.strip():
    print("HTMLの取得に失敗しました。処理を終了します。")
    exit(1)

# HTMLを保存
with open(HTML_FILE, "w", encoding="utf-8") as file:
    file.write(response.text)

# トークンを抽出
print("トークンを抽出中...")
match = re.search(r'name="_token" value="([^"]+)"', response.text)
if not match:
    print("トークンの抽出に失敗しました。処理を終了します。")
    exit(1)
TOKEN = match.group(1)

# POSTリクエストのデータとヘッダー
print("トークンを使用してリクエストを送信中...")
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    # "x-requested-with": "XMLHttpRequest",
    # "Referer": "https://studi-ol.com/shop/674",
    # "Origin": "https://studi-ol.com",
    # "Accept": "*/*",
    # "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
}
data = {
    "_token": TOKEN,
    "shop_id": "674",  #ここが店舗ごとに異なる
    "start": "2024-12-10 12:00:00",
    "end": "2024-12-12 07:00:00",
}

# POSTリクエストの送信
response = session.post("https://studi-ol.com/get_schedule_shop", headers=headers, data=data)
if response.status_code != 200 or not response.text.strip():
    print("リクエストが失敗しました。処理を終了します。")
    exit(1)

# response.text を Python のオブジェクトに変換
data = json.loads(response.text)

# オブジェクトを扱う処理例
for entry in data:
    print(f"タイトル: {entry['roomId']}, 開始時刻: {entry['start']}")

# 必要に応じて、オブジェクトをファイルに保存する場合
with open(RESULT_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print(f"処理が完了しました。結果は {RESULT_FILE} に保存されました。")
