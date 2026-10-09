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

def market_cap(t, last_close):
    try:
        v = t.fast_info["market_cap"]
        if v: return float(v)
    except Exception:
        pass
    try:
        v = t.info.get("marketCap")
        if v: return float(v)
    except Exception:
        pass
    try:
        return float(t.fast_info["shares"]) * last_close
    except Exception:
        return None

result = {}
for code, (name, sector) in STOCKS.items():
    try:
        t = yf.Ticker(code + ".T")
        df = t.history(period="1y", interval="1d", auto_adjust=False).dropna()
        candles = [[d.strftime("%Y-%m-%d"), round(r.Open, 1), round(r.High, 1),
                    round(r.Low, 1), round(r.Close, 1)] for d, r in df.iterrows()]
        if len(candles) < 20:
            raise ValueError("データ不足")
        result[code] = {"name": name, "sector": sector,
                        "marketcap": market_cap(t, candles[-1][4]), "candles": candles}
        print("OK", code, name)
    except Exception as e:
        print("NG", code, name, e)
        if code in old:
            result[code] = old[code]  # 失敗時は前回のデータを残す
    time.sleep(1)

if len(result) < 20:
    sys.exit("取得できた銘柄が少なすぎるため、stocks.json は更新しません")
json.dump(result, open("stocks.json", "w", encoding="utf-8"), ensure_ascii=False)
