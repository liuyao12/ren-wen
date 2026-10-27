# 太史公跨篇身份修正的固定發布來源

預設輸入與無輸入時的 fallback 固定為 CBR 提交 `b319c5af3c6313a2312ba3bb9c6d6f36530d7c0c`，見 [CBR PR #601](https://github.com/liuyao12/chinese-biographical-repository/pull/601)。此為資料與閱讀器的來源提交，與 ren-wen 工作流程提交分別記錄。

本次來源撤除七十二個按篇建立的太史公重複人物，將八十五處既有提及接回司馬遷；司馬談保持獨立，原文、註層、提及 ID 及字位保留。卷九十六篇末未定署稱仍保留未定。來源本機完整 Python 測試四千六百二十九項、相關三十四項測試及其餘必要驗證通過，桌面／手機候選驗收一百三十四項通過；GitHub 檢查及正式發布以實際工作流程結果為準。

沿用既有三百六十分鐘時限、全部資料與程式驗證、瀏覽器驗收、部署權限、Pages 環境及原人文網址。發布流程仍自行驗證確切來源提交，不省略任何檢查。不包含伏羲草稿 PR #600 或後續朝臣、褚先生及中古家族候選。

本檔記錄固定的發布來源，不能當作網站已更新的證明。完成後須核對 [deployment.json](https://liuyao12.github.io/ren-wen/deployment.json) 的 CBR 提交、工作流程提交與 run ID，並在 [既有人物目錄](https://liuyao12.github.io/ren-wen/cbr.html) 驗收兩位太史公的區分、人物頁來源與舊端點撤除。
