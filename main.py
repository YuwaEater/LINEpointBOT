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

    for line in lines:
        if len(line) < 2:
            continue
        key = line[0]
        try:
            score = int(line[1:])
            players[key] = score
        except ValueError:
            continue

    if len(players) < 4:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="プレイヤーが4人未満です。正しく入力してください。")
        )
        return

    total = sum(players.values())
    if total != 100000:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="点数の合計が100000になっていません。入力を確認してください。")
        )
        return

    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)

    # 順位と点数調整
    adjustments = [0, 0, 0, 0]
    scores = [score for _, score in sorted_players]

    if scores[0] == scores[1]:
        adjustments[0] = 10000
        adjustments[1] = 10000
    elif scores[1] == scores[2]:
        pass  # 変化なし
    elif scores[2] == scores[3]:
        adjustments[2] = -10000
        adjustments[3] = -10000
    else:
        adjustments = [15000, 5000, -5000, -15000]

    final_scores = {
        key: score + adj for (key, score), adj in zip(sorted_players, adjustments)
    }

    # 順位付け
    sorted_final = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    result_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        name = name_map.get(key, key)
        result_lines.append(f"{i}位　{name}　{score}")

    result_lines.append("")

    # 円換算（25000引いて0.05倍）
    yen_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        name = name_map.get(key, key)
        yen = int((score - 25000) * 0.05)
        sign = "-" if yen < 0 else ""
        yen_lines.append(f"{i}位　{name}　{sign}{abs(yen)}円")

    reply_text = "\n".join(result_lines + yen_lines)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
