# Pioter 每日數據通道清單

調研與實測日期：2026-09-15。網站／API 是否可取得、資料觀測日是否新鮮、是否允許所需用途，是三件不同的事。

## 建議結論

**主架構採官方 JSON / XML / CSV，每天定時下載；網頁讀正規化快照；vLLM 讀同一份快照。**

不用讓模型自己憑記憶報行情。避免優先爬畫面 DOM。保留原始檔、SHA-256、擷取時間、來源日期、市場時段與轉換公式。此版有 28 個指標欄位；請以執行後 `latest.json` 的狀態為準。

## 1. 已實作、已實際連線

| 圖上需求 | 每日通道 | 口徑／注意 | 本次處理 |
|---|---|---|---|
| 美國 30Y / 10Y / 5Y | [美國財政部 XML](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026) | 日終公債平價殖利率，非盤中報價；使用 BC_30YEAR / BC_10YEAR / BC_5YEAR | 已串接、歷史與 bp 變化 |
| VIX | [Cboe 日收盤 CSV](https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv) | CLOSE 欄；不是 VIX 期貨 | 已串接；使用／重發布須遵守 Cboe 條款 |
| Brent 原油 | [FRED / EIA DCOILBRENTEU CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU) | Brent 現貨 USD/bbl，有發布落差，非期貨連續合約 | 已串接，日期獨立顯示 |
| EUR/USD、USD/JPY、USD/KRW | [ECB 90 日 XML](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml) | EUR 基準；USD/JPY=JPY÷USD，USD/KRW=KRW÷USD，均用同日 | 本環境 TLS 憑證鏈失敗，不降低驗證 |
| 匯率備援 | [Fed H.10 / FRED CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSEU,DEXJPUS,DEXKOUS) | DEXUSEU、DEXJPUS、DEXKOUS；聯準會參考匯率，時點與 ECB 不同 | 備援已實際取得；以 proxy 顯示 |
| 外資台指多／空／淨未平倉 | [TAIFEX 分契約法人日報](https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate) | ContractCode=臺股期貨，Item=外資及陸資；取 OpenInterest(Long/Short/Net)，不是交易量 | 已串接；三欄分開 |
| 全市場 Put/Call Ratio | [TAIFEX PutCallRatio](https://openapi.taifex.com.tw/v1/PutCallRatio) | PutCallOIRatio% 與交易量 PCR 不同；PutOI、CallOI 同時保留 | 已串接，帶歷史 |
| 外資 Call / Put | [TAIFEX 買賣權分計日報](https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDetailsOfCallsAndPutsBytheDate) | 外資臺指選擇權、CALL/PUT、未平倉淨額；這是日報，不是原圖夜盤交易量 | 已串接並標明口徑 |
| 台指期夜盤點位／漲跌 | [TAIFEX DailyMarketReportFut](https://openapi.taifex.com.tw/v1/DailyMarketReportFut) | Contract=TX、TradingSession=盤後，最新資料日近月，保存契約月、Last、Change、% | 已串接，避免混日盤／跨月價差 |
| USD/TWD、USD/HKD | [TAIFEX DailyForeignExchangeRates](https://openapi.taifex.com.tw/v1/DailyForeignExchangeRates) | USD/NTD、USD/HKD；期交所收盤洗價參考，不是銀行間收盤 | 已串接，標 proxy |
| 外資現貨買賣超 | [TWSE BFI82U JSON](https://www.twse.com.tw/fund/BFI82U?response=json) | 上市外陸資，不含外資自營商，不含上櫃；元÷1億 | 已串接 |
| 借券賣出餘額、當日賣出 | [TWSE TWT93U JSON](https://www.twse.com.tw/exchangeReport/TWT93U?response=json) | 嚴格驗欄：第9–13欄屬借券賣出，前段是融券；股數÷1億 | 已串接；附前10大股數集中度 |
| 全部借券餘額 | [TWSE TWT72U JSON](https://www.twse.com.tw/exchangeReport/TWT72U?response=json) | 證交所系統＋證商／證金營業處所；有市場別，涵蓋上市櫃，含 ETF | 已串接；附借入／還券、日變化及前10大市值占比 |
| HIBOR O/N、1M | [HKMA HIBOR fixing JSON](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily?segment=hibor.fixing&pagesize=100) | ir_overnight / ir_1m，利率 %；可存同源 3M 等其他期限 | API 可讀，但本次最新日期過舊，標 stale |

官方文件：[Treasury XML 規格](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)、[期交所 OpenAPI](https://openapi.taifex.com.tw/)、[Cboe VIX 歷史資料](https://www.cboe.com/tradable_products/vix/vix_historical_data)、[HKMA API 文件](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/)。

## 2. 可以每日取數，但需要選定授權供應商

| 指標 | 可行通道 | 費用／權限 | 不可偷換的口徑 |
|---|---|---|---|
| 黃金现貨 USD/oz | [Twelve Data 商品 API](https://twelvedata.com/commodities)，查 `/commodities` 後使用 XAU/USD 的 `/time_series` 日頻 | 需 API key；實際商品權限、個人／商用／再發布依方案確認。本次未申請、未付費 | 聚合現貨、LBMA 定盤價、COMEX 黃金期貨是不同資料 |
| 黄金定盤價 | [LBMA / IBA 資料](https://www.lbma.org.uk/prices-and-data) | 官方定盤與歷史使用可能需授權 | 若採用必須標 LBMA AM / PM，不標即時現貨 |
| LME 三個月銅 | [LME 授權資料與分銷商](https://www.lme.com/market-data/market-data-licensing) | 申請歷史／延遲資料或授權分銷商；報價依用途確認，本次未採購 | COMEX HG 是另一交易所與商品；期貨換月也不可直接串成 LME 3M |
| DXY | [ICE 美元指數資料](https://www.ice.com/fixed-income-data-services/index-solutions/currency-indices) | ICE 或授權供應商 API；確認指數值 vs DX 期貨，以及再發布權限 | Fed 廣義美元指數 DTWEXBGS 不能寫成 DXY |

DXY、LME 三個月銅兩個欄位保留 `value=null / status=license_required`。不用未授權的隱藏端點、登入繞過或不明 Yahoo 非正式介面作核心正式通道。供應商權限確認後，可新增 adapter，不需改網頁或模型資料格式。

## 3. 已找到來源、尚未實作的原圖補齊項目

| 需求 | 來源 | 下一步與限制 |
|---|---|---|
| 原圖外資夜盤 Call / Put 買方、賣方、差額 | [期交所夜盤選擇權法人查詢](https://www.taifex.com.tw/cht/3/optContractsDateAh)、[期交所買賣權日報](https://www.taifex.com.tw/cht/3/callsAndPutsDate) | 需確認專屬夜盤買賣權分計下載，再寫 HTML／CSV parser；日報不得冒充夜盤。優先與期交所確認對外下載接口 |
| 選擇權履約價、OI 移轉、結算區 | [TAIFEX DailyMarketReportOpt](https://openapi.taifex.com.tw/v1/DailyMarketReportOpt) | 以契約月／週、履約價、買賣權、交易時段分組；存連續多日。API 已存在，尚未加 adapter |
| USD/TWD 銀行間收盤（原圖口徑） | [中央銀行匯率資訊](https://www.cbc.gov.tw/)、[期交所匯率口徑說明](https://www.taifex.com.tw/cht/3/dlDailyFXRateView) | 選定央行／台北外匯經紀官方發布表並確認自動下載；臺銀牌告現金／即期買賣價不能冒充銀行間收盤 |
| 更及時 USD/HKD | [HKMA 每日匯率 JSON](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily?pagesize=30) | 本次試取的資料同樣落後；現用期交所參考值。必須判斷 freshness |
| 更及時 HIBOR | [香港銀行公會](https://www.hkab.org.hk/)／授權供應商 | 核對取用條款與每日 fixing 日期；HKMA 成功回應不代表今日已發布 |
| 上櫃外資現貨 | [櫃買中心 OpenAPI](https://www.tpex.org.tw/openapi/) | 與上市各自保留市場別與交易日，再決定是否合併；目前只顯示上市 |
| 個股月營收／財報／公告 | [證交所 OpenAPI](https://openapi.twse.com.tw/v1/swagger.json)、[公開資訊觀測站](https://mops.twse.com.tw/) | 按上市／上櫃／興櫃選來源；存公告時刻與資料所屬期間，不用最新報表回填過去 |
| 策略共振與券商分點 | 使用者 GitHub JSON/CSV/cache；官方或授權分點資料 | 需要 repository 或靜態資料 URL；附文只有名稱，無法定位唯一來源。沒有資料不能推測主力習性 |

## 4. 政治與地緣政治：來源發現 → 原文 → 事件證據

這一層不宜當數字報價處理。建議每日拉取來源標題與時間、去重，再取官方原文核對「發布時間」「事件時間」「生效時間」。

- 美國貨幣政策：[Federal Reserve RSS](https://www.federalreserve.gov/feeds/feeds.htm)。
- 國際事件發現：[GDELT 官方專案與 API](https://www.gdeltproject.org/)。多國媒體用於找事件，不是事實驗證來源；重複報導不當成多個獨立事件。
- 美國貿易／出口政策：USTR、BIS、Federal Register 官方公告。
- 中國：商務部、人民銀行官方公告；歐盟：European Commission、EUR-Lex；日本：BOJ、METI；韓國：BOK、MOTIE；台灣：央行、經濟部、金管會及公開資訊觀測站。

目前尚未接事件擷取器，`events=[]`。模型被要求不能憑訓練記憶補「最新」事件。建議事件 schema：`id, title, source_url, source_name, published_at, event_at, effective_at, countries, category, factual_summary, verification_status, transmission_channels`。傳導路徑可列能源、利率、匯率、供應鏈；模型推論與原文事實要分開。

## 5. 每日運作

建議 07:30 開始準備早報、18:30 開始準備晚報（台北時間），不是對所有市場的發布時刻保證。美國夏令／冬令、週末、台灣／香港休市都可能讓最新交易日不同。

1. HTTP timeout 25 秒，最多三次重試；按來源保存原始回應，不繞過封鎖。
2. schema 改變時停止該來源解析；其他來源繼續。
3. 每筆驗證日期、有限數值、單位、契約與時段。
4. 留存歷史，計算變化時只對同一指標與來源口徑。利率使用 bp。
5. 標記過期／缺失；目前一般4日、EIA7日是「日曆天寬限」，不是嚴格逐市場交易日判定，長假需覆核。
6. 輸出同一 snapshot_id 的 JSON、Markdown，再呼叫 vLLM。
7. 模型 JSON 驗證成功才寫 analysis.json。證據值／日期不符時不發布結論。

**排程腳本已備妥，但未啟用。線上 Sites 是發布快照，不會因本機排程執行而自動更新。** 持續線上更新另需配置同步／部署管線。

## 6. 目前可交付與仍缺資訊

- 可交付：每日擷取程式、28 指標正規化格式、原始證據保存、歷史快照、手機網頁、JSON/Markdown 匯出、本地模型串接與實測結果。
- 仍缺：DXY 與 LME 報價的適用取數權限、策略 GitHub URL、專用夜盤買賣權 parser、事件來源擷取器、精確逐市場行事曆、線上自動更新管線。

這份文件列出可每天擷取的通道，不表示每個通道都已無條件授權或全部整合完成。

## 2026-09-15 補充：第三方爬蟲與 TradingView

- TradingView XAUUSD 頁面使用 OANDA 報價。官方明示禁止自動擷取，且條款限制機器分析等 non-display 使用，因此不將其隱藏接口、WebSocket 或畫面爬蟲作為每日分析通道。[官方說明](https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/)；[使用條款](https://www.tradingview.com/policies/)。
- **黃金已實際接入免費 Gold API**：[GET /price/XAU](https://api.gold-api.com/price/XAU)，返回 price、symbol、updatedAt。每天一次或兩次低頻下載並留存，本次已成功試取。不需 API key；第三方來源品質標為 proxy，不能冒充 LBMA 定盤。[API 文件](https://gold-api.com/docs)；[條款](https://gold-api.com/terms)載明可用於商用網頁／App，禁止濫用。此項取代前表的黃金待授權狀態。
- **LME 三個月銅找到 Westmetall 公開日表**：[Copper 表格](https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Cu_cash)。頁面分開 Cash-Settlement、3-month 和庫存，技術上可用 HTML 表格 parser 每日取最新列。但其[法律聲明](https://www.westmetall.com/en/impressum.html)對內容再利用有限制，未見明確可供本系統自動分析／再發布的開放授權；列為候選，尚未啟用。
- **DXY**：尚未確認可無帳號且允許每日機器分析的原始指數免費通道。可詢問 ICE 授權分銷商，或另加標明名称的 Fed 廣義美元指數作輔助；不把代理序列改名 DXY。
