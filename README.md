# Pioter 資金戰情室

參考原圖重建的響應式網頁，以及可每日執行的官方資料擷取、研究包輸出和 vLLM 分析管線。

## 使用

在本專案目錄執行（Python 3.12，標準函式庫，無需 pip 安裝）：

```powershell
python -X utf8 scripts/daily.py
python -X utf8 scripts/serve.py
```

本機開啟 http://127.0.0.1:8765。第一次執行需要可連外網路。

- `daily.py`：擷取、格式檢查、歷史保存、輸出 JSON／Markdown、查詢 vLLM 當下模型、產生並核對分析。
- `collect.py`：只擷取和匯出，不呼叫模型。
- `analyze.py`：使用目前的研究包重新分析，每次都查 `/v1/models`。
- 網頁「重新載入」只讀最新快照；不會偷偷觸發網路爬蟲。
- 網頁本機版「執行本地分析」呼叫固定設定的模型服務；線上靜態版可匯入相同 snapshot_id 的分析結果。

## vLLM

已於 2026-09-15 實測：

- API 根路徑：`https://vllm-a5000.iii-ei-stack.com/v1`
- 當時模型：`cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`
- `/v1/models` 回報 `max_model_len=200000`。
- 不將模型名稱寫死；每次執行重新發現，若設 `VLLM_MODEL` 則確認它仍在服務清單。

以程序環境變數設定 `VLLM_BASE_URL`、選填 `VLLM_MODEL`、`VLLM_API_KEY`。`.env.example` 只是範例，不會自動載入。認證資訊不得放到網頁 JavaScript。服務網址雖經 HTTPS 對外提供，仍依使用者指定視為其 vLLM 服務；本專案只傳送本研究包。

## 產出

| 路徑 | 用途 |
|---|---|
| `dist/data/latest.json` | 網頁及模型共用研究包，包含數值、日期、時段、來源、品質、歷史 |
| `dist/data/brief.md` | 人與模型皆可閱讀的清單 |
| `dist/data/analysis.json` | 與 snapshot_id 綁定的已核對模型輸出 |
| `data/raw/<run>/` | 每次原始回應與 SHA-256 稽核清單，僅本機保留 |
| `data/snapshots/` | 歷次完整快照 |
| `data/analysis/` | 歷次模型結果 |
| `dist/data-sources.md` | 全部指標的每日資料通道與尚待接入項目 |
| `docs/model-contract.md` | 輸入、輸出與驗證規則 |

## 每日排程（尚未啟用）

已提供可安裝的 Windows 工作排程腳本，預設不會修改系統。需要每日自動跑時執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-daily-task.ps1 -Install
```

台北時間 07:30、18:30 執行。電腦需開機、登入且有網路；未使用無人登入帳密。工作不會自動將新資料發布到 Sites，線上版是最後發布時的快照；要持續線上更新需再串接部署或獨立同步機制。

## 實際限制

- DXY、LME 三個月銅待合適授權通道；黃金已接 Gold API 免費第三方參考報價；不以不同商品冒名填入。
- HKMA HIBOR 通道目前回傳较舊日期，網頁標示過期且模型不得用作當日證據。
- ECB 在本環境發生憑證鏈驗證問題，沒有關閉 TLS 驗證；備援使用 FRED 的聯準會 H.10 日參考匯率。
- USD/TWD 現為期交所洗價參考，與央行銀行間收盤口徑不同。
- 外資日報選擇權已串接；原圖的外資夜盤買賣權尚待專用解析器。
- 地緣政治和個股策略來源尚未接入，沒有自動生成新聞、策略共振、主力習性或個股排名。
- 交易日行事曆尚未完整串接。現採來源日曆天門檻標記過期；長假可能需要人工覆核。
- 模型輸出的 evidence 會核對指標、數值和日期；敘述與預測仍需人為審閱，不是經回測的買賣策略。

## 驗證

```powershell
python -X utf8 scripts/test_integrity.py
node --check dist/app.js
```

資料擷取採超時、3 次重試、五路最大並行、逐來源故障隔離、原始檔保存及原子寫入。失敗不會把舊值標成新值。歷史以指標＋來源口徑合併；夜盤跨月不拼成未調整連續序列。

實測發現目前 vLLM 偶爾把小幅殖利率變化形容為急升，或提出未回測門檻。系統會標記 review_flags，頂部顯示「待覆核」；保留模型草稿供審閱，不能將數字核對等同推論驗證。
