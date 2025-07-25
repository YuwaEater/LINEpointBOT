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

# 記録フラグと一時保存データ
#合計をまとめるための箱を用意
recording = False
recorded_scores = []

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

    #開始と終了の合図を設計
    # 記録モードの開始・終了（ステップ2）
    global recording, recorded_scores
    if text == "麻雀開始":
        recording = True
        recorded_scores = []
        reply = "試合スタートです！たくさんお金を失うのはどの子かな～？"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return
    if text == "麻雀終了":
        recording = False
        if not recorded_scores:
            reply = "まだ一試合もしてないですよ！"
        else:
            totals = {}
            play_counts = {}

            # スコア合計と参加回数を集計
            for entry in recorded_scores:
                for key, value in entry.items():
                    totals[key] = totals.get(key, 0) + value
                    play_counts[key] = play_counts.get(key, 0) + 1

            # 円換算の表示
            yen_lines = ["【今日の結果はこうなりました！】"]
            sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)
            for i, (key, total) in enumerate(sorted_totals, start=1):
                name = name_map.get(key, key)
                match_count = play_counts.get(key, 0)
                base_score = 25000 * match_count
                yen = int((total - base_score) * 0.05)
                sign = "" if yen >= 0 else "-"
                yen_lines.append(f"{i}位　{name}　{sign}{abs(yen)}円")

            reply = "\n".join(yen_lines)

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    #特定のワードで返信できるようにする
    #初期状態
    reply = None
    if "きょうこ" in text:
        reply = "その話はまずいですよ！"
    elif "千佳ちゃんかわいいね" in text:
        reply = "でへへ～もっと褒めて～"
    elif "千佳ちゃん賢いね" in text:
        reply = "IQ3でも任せなさ～い！"
    elif "千佳ちゃん" in text:
        reply = "何ですか～？"
    elif "ゆのか" in text:
        reply = "ゆのかちゃんはもういないんです！"
    elif "ありさ" in text:
        reply = "あと半年、早ければなぁ～。"
    elif "ゆな" in text:
        reply = "一年後には必ず！きっと、、！おそらく、、、。"
    elif "ひなこ" in text:
        reply = "過去を悔いたって仕方ないのです！"
    elif "たいが誕生日おめでとう" in text:
        reply = "たいがくん！誕生日おめでとなのです！"
    elif "しょうえい誕生日おめでとう" in text:
        reply = "しょうえいくん！誕生日おめでとなのです！"
    elif "ゆういち誕生日おめでとう" in text:
        reply = "ゆういちくん！誕生日おめでとなのです！"
    elif "たくろう誕生日おめでとう" in text:
        reply = "たくろうくん！誕生日おめでとなのです！"
    elif "慰めて" in text:
        reply = "まったく～、仕方のない子ですね～"
    elif "褒めて" in text:
        reply = "わぁ～！素晴らしいですね！"
    elif "本気" in text:
        reply = "どーんだYO！"
    elif "喰らい尽くす！" in text:
        reply = "ゴッドイーター！！！"
    elif "運命の一撃を" in text:
        reply = "叩き込め～！"
    elif "BONUS確定！" in text:
        reply = "EXTRA！！！"
    elif "千佳ちゃん歌って" in text:
        reply = "いつだって　誰だって　恋したらヒロイン～"
    elif "千佳ちゃん踊って" in text:
        reply = "しゃらら～ん"
    elif "困った" in text:
        reply = "ラブ探偵千佳に任せなさ～い！"
    elif "喧嘩" in text:
        reply = "仲良し警察です！喧嘩する悪い子はここですか！？"
    elif "浪人" in text:
        reply = "何田君と何永君の話ですか～？"
    elif "留年" in text:
        reply = "何永君の話ですか～？"
    elif "宮崎" in text:
        reply = "宮崎って素晴らしいですよね～！"
    elif "山形" in text:
        reply = "山形って、、、ロシアでしたっけ？"
    elif "広島" in text:
        reply = "先の時代の敗北者じゃけぇ！"
    elif "岩手" in text:
        reply = "リアス海岸でしたっけ？それ以外に何かあるんですか～？"
    elif "千葉" in text:
        reply = "関東の序列は埼玉の下ですよね？"
    #ここからはLINEで返信するためのコード
    if reply:
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return
    
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

    #開始以降の点数を保存
    if recording:
        recorded_scores.append(final_scores.copy())


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
