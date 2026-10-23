# CBR #571 預設發布來源與時限修復

預設輸入及無輸入時的 fallback 固定為 CBR #571 的提交 `326b5eabdee68dcfafa8327fbe55dd13552475d9`。GitHub 官方記錄顯示，此 PR 已於 `2026-10-23T01:59:34Z` 合併，該確切提交的三項 CI 全部成功。此為 CBR 來源提交，不是 ren-wen 的工作流程提交；不包含 #572 或其後資料。

[Pages 工作 39879879881](https://github.com/liuyao12/ren-wen/actions/runs/39879879881) 使用上述確切來源，但其工作流程仍來自 ren-wen main `f8bfc7974cee5e3db03be6935756c2ae04148bb5`，時限為120分鐘。[官方 job 記錄](https://github.com/liuyao12/ren-wen/actions/runs/39879879881/job/120174425477) 顯示：

- 工作從 `2026-10-23T00:44:19Z` 至 `02:44:44Z`，結果為 `completed/cancelled`。
- 完整驗證 `00:45:14Z–02:33:10Z` 成功；日誌記錄4,261項 Python 與519項 JavaScript 測試通過。
- 瀏覽器支援安裝 `02:33:10Z–02:44:40Z` 被取消；官方 annotation 明載 `The job has exceeded the maximum execution time of 2h0m0s`。最後安裝輸出為下載 `fonts-noto-cjk`，不能據此宣稱測試失敗或已證實網路故障。
- Stage、部署與發布後驗收全部跳過，該工作沒有發布 #571。

本 PR 保留已提出的180分鐘工作時限，僅把兩處預設來源從 #569 更新為上述 #571。完整驗證、步驟、依賴安裝、權限、環境、並行設定及既有人文網址不變；手動指定來源輸入的能力保留。歷史 #567/#569 發布記錄保留。

此文件記錄修復候選，不宣稱 #571 已上線。PR #17 的新確切提交仍須取得明確主分支合併授權，再由既有流程發布並核對 `deployment.json` 與實際網站；舊 head 的待批問題不涵蓋本次新提交。
