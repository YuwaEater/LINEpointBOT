from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 表示名対応表
name_map = {
    "し": "たくぴぴ",
    "ま": "まっすー",
    "も": "正義超人森永",
    "お": "ぱすた",
    "い": "しょさん"
}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    lines = text.splitlines()
    players = {}

    # 入力を解析
    for line in lines:
        if len(line) < 2:
            continue
        key = line[0]
        try:
            score = int(line[1:])
            players[key] = score
        except ValueError:
            continue

    # 点数が4人分未満の場合は無視
    if len(players) < 4:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="プレイヤーが4人未満です。正しく入力してください。")
        )
        return

    # 合計点のチェック
    total = sum(players.values())
    if total != 100000:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="点数の合計が100000になっていません。入力を確認してください。")
        )
        return

    # ソートして順位付け
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)

    result_lines = []
    for i, (key, score) in enumerate(sorted_players, start=1):
        name = name_map.get(key, key)
        result_lines.append(f"{i}位　{name}　{score}")

    reply_text = "\n".join(result_lines)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
