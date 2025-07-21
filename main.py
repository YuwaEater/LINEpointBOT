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
    #スタンプや画像を無視するようにする
    if not isinstance(event.message, TextMessageContent):
        return
    #前後の空白を消去
    text = event.message.text.strip()
    #4行確認および-の数値も計算できるように
    valid_lines = [line for line in text.splitlines() if len(line) >=2 and line[1:].lstrip("-").isdigit()]
    if len(valid_lines) <4:
        return
    #各行を1つずつ処理
    lines = text.splitlines()
    #空の辞書をつくり名前と点数の保存
    players = {}

    #点数を空の辞書へ
    for line in lines:
        #規定通りでない場合はスキップ
        if len(line) < 2:
            continue
        #最初の一文字をプレイヤー記号として取り出す
        key = line[0]
        #名前と数値を対応
        try:
            score = int(line[1:])
            players[key] = score
        except ValueError:
            continue
    #3人の時の返事
    if len(players) == 3:
        reply = "3麻はやらない主義なのです！"
        #ここからはLINEで返信するためのコード
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return
    #5人の時の返事
    if len(players) == 5:
        reply = "どこの国の麻雀なんですか～！"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return
    #合計100000かどうかの確認
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
    #点数が大きい順に並べる
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    #点数だけのリストを作成
    scores = [score for _, score in sorted_players]
    #順位点を調整するための箱を準備
    adjustments = [0, 0, 0, 0]

    if scores[0] == scores[1] and scores[2] == scores[3]:
        adjustments = [10000, 10000, -10000, -10000]
    elif scores[0] == scores[1]:
        adjustments = [10000, 10000, -5000, -15000]
    elif scores[1] == scores[2]:
        adjustments = [15000, 0, 0, -15000]
    elif scores[2] == scores[3]:
        adjustments = [15000, 5000, -10000, -10000]
    else:
        adjustments = [15000, 5000, -5000, -15000]

    # スコア調整後
    final_scores = {}
    for (key, score), diff in zip(sorted_players, adjustments):
        final_scores[key] = score + diff

    # 再度順位付け
    sorted_final = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # 点数表示（最終点数)
    #LINEで送るメッセージの1行ずつをリストとして準備
    result_lines = []
    #1位から順に順位をつける
    for i, (key, score) in enumerate(sorted_final, start=1):
        #名前を取り出す
        name = name_map.get(key, key)
        #順位、名前、点数の順で表示させる
        result_lines.append(f"{i}位　{name}　{score}")
    #空行を設ける
    result_lines.append("")

    # 円換算表示
    #お金表示のリスト
    yen_lines = []
    for i, (key, score) in enumerate(sorted_final, start=1):
        #名前を取り出す
        name = name_map.get(key, key)
        #計算
        yen = int((score - 25000) * 0.05)
        #マイナスの時-をつける
        sign = "" if yen >= 0 else "-"
        #順位、名前、値段を表示
        yen_lines.append(f"{i}位　{name}　{sign}{abs(yen)}円")
    #今までの分を表示
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
