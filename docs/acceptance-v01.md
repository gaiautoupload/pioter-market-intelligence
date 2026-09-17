# v0.1 驗收標準

1. 每次分析前必須成功呼叫 vLLM `/v1/models`；不可寫死失效模型。
2. 模型引用的 metric ID、value、observed_at 必須與同一 snapshot 完全一致。
3. TWSE 每日股票資料可寫入 SQLite，並輸出 `dist/data/market.json`。
4. 缺少官方資料時保留舊公開檔，記錄錯誤，不把舊值改成今日。
5. 排行與策略均由固定公式產生；同一輸入必須得到同一結果。
6. 所有行情畫面顯示資料日期；盤後資料不得標示為即時。
7. 網頁支援 360px 手機寬度、鍵盤搜尋、字體縮放與瀏覽器雙指縮放。
8. 自選與持股不離開使用者裝置；GitHub Pages 不含私人持股資料。
9. GitHub Pages 發布檔不得包含 `.env`、SQLite、原始抓取檔或 API key。
10. 工作排程固定為 Asia/Taipei 08:00 與 18:00；重疊執行會被 lock 阻擋。
11. 券商分點、即時行情及新聞授權未完成時必須明確顯示 Integration/License Required。
12. `python scripts/test_integrity.py`、Python compile 與 `node --check dist/app.js` 必須通過。
