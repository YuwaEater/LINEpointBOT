from flask import Flask, request, abort
import os
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest
from linebot.v3.models import TextMessageContent, MessageEvent, TextMessage

app = Flask(__name__)

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
messaging_api = MessagingApi(channel_access_token)

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
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
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
        reply = "麻雀は4人でしようや。3麻て、、ここからがマグマなんですか笑"
        messaging_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)]))
        return

    if sum(players.values()) != 100000:
        reply = "点数の合計が100000じゃない。点棒も数えられない人がいるの？"
        messaging_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)]))
        return

    # ソートと順位点計算
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    values = [v for _, v in sorted_players]
    adjustment = [0, 0, 0, 0]

    if values[0] == values[1]:
        adjustment[0] = 10000
        adjustment[1] = 10000
    elif values[1] == values[2]:
        pass  # 何もしない
    elif values[2] == values[3]:
        adjustment[2] = -10000
        adjustment[3] = -10000
    else:
        adjustment = [15000, 5000, -5000, -15000]

    # 調整後の点数
    final_scores = {}
    for (key, score), adj in zip(sorted_players, adjustment):
        final_scores[key] = score + adj

    # 円換算用
    yen_scores = {}
    for key, score in final_scores.items():
        score -= 25000
        yen = int(score * 0.05)
        yen_scores[key] = yen

    # 出力整形
    result_lines = []
    sorted_final = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    for i, (key, score) in enumerate(sorted_final, start=1):
        result_lines.append(f"{i}位　{name_map.get(key, key)}　{score}")

    result_lines.append("")  # 空行
    for i, (key, score) in enumerate(sorted_final, start=1):
        result_lines.append(f"{i}位　{name_map.get(key, key)}　{yen_scores[key]}円")

    reply_text = "\n".join(result_lines)
    messaging_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)]))
