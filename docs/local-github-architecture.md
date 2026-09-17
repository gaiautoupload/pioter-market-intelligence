# 純地端資料管線與 GitHub Pages 架構

## 執行流程

```text
Windows 工作排程（08:00 / 18:00，Asia/Taipei）
  → collect.py：全球與台股資金資料
  → equity.py：TWSE 盤後行情、估值、公司資料
  → SQLite：地端歷史與管線紀錄
  → analyze.py：先查詢 /v1/models，再把結構化資料送入 vLLM
  → 驗證 evidence / snapshot_id / 日期 / 數值
  → dist/data/*.json：純靜態網站資料
  → publish_github.py：只提交公開輸出並推送 GitHub
  → GitHub Pages workflow：發布 dist/
```

GitHub Actions 不呼叫地端 vLLM，也不保存 vLLM 金鑰。電腦必須在排程時間開機、有網路，GitHub remote 必須已完成驗證。

## v0.1 功能

| 功能 | 狀態 | 資料方式 |
|---|---|---|
| 全球／台股資金戰情室 | Functional | 官方 API、官方 CSV、明確標示的第三方參考價 |
| 上市股票搜尋 | Functional | TWSE OpenAPI `STOCK_DAY_ALL` |
| 成交額、成交量、漲跌、殖利率排行 | Functional | 本機 deterministic 計算 |
| 條件策略 | Functional | 本機 deterministic 計算，可回溯定義 |
| 個股行情與估值 Workspace | Functional | TWSE OpenAPI |
| 自選／持股 | Functional | 瀏覽器 localStorage，只留在使用者裝置 |
| vLLM 市場分析 | Functional | 每次先查 `/v1/models`，數值證據逐筆核對 |
| Data Health | Functional | 顯示來源、列數、狀態、資料日與限制 |
| SQLite 歷史 | Functional | `data/pioter.sqlite3`，不公開到 GitHub Pages |
| 上櫃／興櫃 | Integration Required | TPEx 官方 API／CSV Provider |
| 大戶散戶 | Integration Required | TDCC `/v1/opendata/1-5`，每週資料 |
| 法人個股排行 | Integration Required | TWSE／TPEx 官方法人資料 |
| 券商分點／主力成本／八大行庫 | License Required | 官方資料商品或正式授權 Provider |
| 真正即時行情／盤中 K | License Required | 有再散布權的行情商 |
| 新聞全文 | License Required | 授權 Feed 或可再利用 RSS/API |
| 多裝置帳號與投資組合 | Integration Required | 需後端、登入、資料庫與權限隔離；GitHub Pages 無法單獨完成 |

## 資料原則

- LLM 不計算股價、排行、技術指標或法人張數；只解釋已驗證 JSON。
- 缺值不等於 0，過期不等於最新，授權未完成不以爬蟲繞過。
- 每筆核心資料保留來源 URL、擷取時間、資料日期與原始回應 SHA-256。
- 靜態網站只公開研究所需 JSON；SQLite、原始檔、認證資訊留在地端。

## 後續功能階段

1. TPEx 上櫃／興櫃與 TDCC 股權分散。
2. 法人、融資券、當沖、技術指標與歷史排行。
3. ETF 發行商 PCF adapters、NAV 與持股變化。
4. 授權分點與即時行情。
5. 若需要登入／跨裝置，再增加後端；靜態 Pages 保留公開研究頁。
