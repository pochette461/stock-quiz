import json, os, sys, time
import yfinance as yf

# コード: (社名, セクター)  ← 銘柄を変えたいときはここを編集
STOCKS = {
 "7203": ("トヨタ自動車", "自動車"),
 "7267": ("ホンダ", "自動車"),
 "6301": ("小松製作所", "機械"),
 "7011": ("三菱重工業", "機械"),
 "6758": ("ソニーグループ", "電機"),
 "6861": ("キーエンス", "電機"),
 "6501": ("日立製作所", "電機"),
 "8035": ("東京エレクトロン", "半導体"),
 "6857": ("アドバンテスト", "半導体"),
 "285A": ("キオクシア", "半導体"),
 "8306": ("三菱UFJ FG", "銀行"),
 "8766": ("東京海上HD", "保険"),
 "8058": ("三菱商事", "商社"),
 "8001": ("伊藤忠商事", "商社"),
 "9983": ("ファーストリテイリング", "小売"),
 "3382": ("セブン&アイ", "小売"),
 "9432": ("NTT", "通信"),
 "9433": ("KDDI", "通信"),
 "9984": ("ソフトバンクG", "通信・投資"),
 "4502": ("武田薬品", "医薬"),
 "4519": ("中外製薬", "医薬"),
 "4568": ("第一三共", "医薬"),
 "2802": ("味の素", "食品"),
 "2914": ("日本たばこ産業", "食品"),
 "2503": ("キリンHD", "食品"),
 "9020": ("JR東日本", "運輸"),
 "9202": ("ANA HD", "運輸"),
 "8801": ("三井不動産", "不動産"),
 "6098": ("リクルートHD", "サービス"),
 "4661": ("オリエンタルランド", "サービス"),
 "7974": ("任天堂", "エンタメ"),
 "4063": ("信越化学工業", "素材"),
 "5401": ("日本製鉄", "素材"),
 "593A": ("ティアフォー", "IT・自動運転"),
 "3350": ("メタプラネット", "投資・暗号資産"),
 "215A": ("タイミー", "人材サービス"),
 "581A": ("GO", "IT・モビリティ"),
}

old = {}
if os.path.exists("stocks.json"):
    try:
        old = json.load(open("stocks.json", encoding="utf-8"))
    except Exception:
        pass

# 発行済株式数を手動で指定したい銘柄(株式分割のあとなどで、yfinance の時価総額がずれる銘柄用)
# 時価総額 = 株数 × 直近の終値 で計算します。数字は「分割後」の株数にしてください。
# 数字は決算資料やYahoo!ファイナンスの「発行済株式数」で確認して、必要なら直してください。
SHARES = {
    # 2026年10月1日に株式分割した銘柄。株数は2026-10-16時点の発行済株式数(Yahoo!ファイナンスで確認)
    "285A": 1_645_917_102,    # キオクシア(1株→3株)
    "8035": 2_340_163_665,    # 東京エレクトロン(1株→5株)
    "8766": 29_010_000_000,   # 東京海上HD(1株→15株)
    # 増資・自社株買い・分割などで株数が変わったら、ここの数字を更新してください。
}

def market_cap(code, t, last_close):
    """(使う時価総額, 確認用のメモ) を返します。
    yfinance には時価総額が2種類あります。
      info["marketCap"]       … Yahooが提供している時価総額(こちらを優先して使います)
      fast_info["market_cap"] … yfinanceが「終値×株数」で計算した値(株数が古いとずれます)
    """
    mc_info = mc_fast = None
    try:
        v = t.info.get("marketCap")
        if v: mc_info = float(v)
    except Exception:
        pass
    try:
        v = t.fast_info["market_cap"]
        if v: mc_fast = float(v)
    except Exception:
        pass
    note = ""
    if mc_info: note += " info=%.2f兆" % (mc_info / 1e12)
    if mc_fast: note += " fast=%.2f兆" % (mc_fast / 1e12)
    if mc_info and mc_fast and max(mc_info, mc_fast) / min(mc_info, mc_fast) > 1.2:
        note += " ★2つの値が大きく違います"
    if code in SHARES:
        return SHARES[code] * last_close, " [手動の株数を使用]" + note
    mc = mc_info or mc_fast
    if not mc:
        try:
            mc = float(t.fast_info["shares"]) * last_close
        except Exception:
            mc = None
    return mc, note

result = {}
for code, (name, sector) in STOCKS.items():
    try:
        t = yf.Ticker(code + ".T")
        df = t.history(period="1y", interval="1d", auto_adjust=False).dropna()
        candles = [[d.strftime("%Y-%m-%d"), round(r.Open, 1), round(r.High, 1),
                    round(r.Low, 1), round(r.Close, 1)] for d, r in df.iterrows()]
        if len(candles) < 20:
            raise ValueError("データ不足")
        mc, note = market_cap(code, t, candles[-1][4])
        result[code] = {"name": name, "sector": sector,
                        "marketcap": mc, "candles": candles}
        # 確認用:実際の株価・時価総額と見比べられるように表示します
        if mc:
            print("OK", code, name, "終値", candles[-1][4],
                  "時価総額 %.2f兆円" % (mc / 1e12),
                  "(株数 %.0f百万株)" % (mc / candles[-1][4] / 1e6) + note)
        else:
            print("OK(時価総額なし)", code, name)
    except Exception as e:
        print("NG", code, name, e)
        if code in old:
            result[code] = old[code]  # 失敗時は前回のデータを残す
    time.sleep(1)

if len(result) < 20:
    sys.exit("取得できた銘柄が少なすぎるため、stocks.json は更新しません")
json.dump(result, open("stocks.json", "w", encoding="utf-8"), ensure_ascii=False)
