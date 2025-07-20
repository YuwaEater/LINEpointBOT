from flask import Flask, request, abort
import os
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient  # ApiClient を追加
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# LINE BOT SDK v3 の設定（修正済み）
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
api_client = ApiClient(configuration)  # ← 修正ポイント
messaging_api = MessagingApi(api_client)  # ← 修正ポイント
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
        reply = "3麻はやらない主義なのです！"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    total = sum(players.values())
    if total != 100000:
        reply = "点棒も数えられないんですか～？"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    # 順位付けとスコア調整
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    scores = [score for _, score in sorted_players]
    adjustments = [0, 0, 0, 0]

    if scores[0] == scores[1]:
        adjustments[0] = 10000
        adjustments[1] = 10000
    elif scores[1] == scores[2]:
        adjustments = [0, 0, 0, 0]
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

    result_lines.append("")

    # 円換算表示
    yen_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        name = name_map.get(key, key)
        yen = int((score - 25000) * 0.05)
        sign = "" if yen >= 0 else "-"
        yen_lines.append(f"{i}位　{name}　{sign}{abs(yen)}円")

    reply_text = "\n".join(result_lines + yen_lines)

    # 正しい形式で返信
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

# Render対応：ポート設定
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
