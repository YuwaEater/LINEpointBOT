from flask import Flask, request, abort
import os
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging.models import TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# LINE BOT SDK v3 の設定
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
messaging_api = MessagingApi(configuration)
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

@handler.add(MessageEvent)
def handle_message(event):
    if not isinstance(event.message, TextMessageContent):
        return

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
        reply = "プレイヤーが4人未満です。正しく入力してください。"
        messaging_api.reply_message(event.reply_token, [TextMessage(text=reply)])
        return

    total = sum(players.values())
    if total != 100000:
        reply = "点数の合計が100000になっていません。入力を確認してください。"
        messaging_api.reply_message(event.reply_token, [TextMessage(text=reply)])
        return

    # 順位付けとスコア調整
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    scores = [score for _, score in sorted_players]
    adjustments = [0, 0, 0, 0]

    # 同点処理（条件付き加点・減点）
    if scores[0] == scores[1]:
        adjustments[0] = 10000
        adjustments[1] = 10000
    elif scores[1] == scores[2]:
        pass  # 加点なし
    elif scores[2] == scores[3]:
        adjustments[2] = -10000
        adjustments[3] = -10000
    else:
        adjustments = [15000, 5000, -5000, -15000]

    # スコア調整後
    final_scores = {}
    for (key, score), diff in zip(sorted_players, adjustments):
        final_scores[key] = score + diff

    # 再度順位付け
    sorted_final = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # 点数表示（最終点数）
    result_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        name = name_map.get(key, key)
        result_lines.append(f"{i}位　{name}　{score}")

    result_lines.append("")  # 改行行

    # 円換算表示
    yen_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        name = name_map.get(key, key)
        yen = int((score - 25000) * 0.05)
        sign = "" if yen >= 0 else "-"
        yen_lines.append(f"{i}位　{name}　{sign}{abs(yen)}円")

    # 全体返信
    reply_text = "\n".join(result_lines + yen_lines)
    messaging_api.reply_message(event.reply_token, [TextMessage(text=reply_text)])
