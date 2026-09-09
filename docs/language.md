# 介面語言 / Interface language

人文以中文讀者為主要對象，預設使用繁體中文（`zh-Hant`）。閱讀器、人物頁及著作頁的頂部均有 **中文 / English** 按鈕。English 模式保留中文姓名、籍貫、字號、書名及中曆年號、干支，並非把歷史資訊改成純英語。

## 介面與原文分開

切換語言僅影響導覽、標籤、操作說明、懸浮卡和圖表標示。**ECCP 英文、《清史稿》中文、引用文字、姓名及題名保持原樣**；不自動翻譯原文，不做簡繁轉換，不改動 JSON 記錄、標註編號、版本及校驗碼。自由撰寫的考證說明與來源摘錄可能仍使用原有語言。

籍貫仍按資料模型處理，不因介面語言而改成出生地。公曆年、中曆年與虛歲計算也不因語言切換而變更。

## 使用與儲存

- 選擇儲存在 `localStorage['ren-wen:language:v1']`，於三個頁面之間及重新開啟時沿用。
- 儲存被禁用時仍可在當頁切換；初次開啟預設中文，不依瀏覽器地區推測偏好。
- 切換不重載文本，不改變 URL、當前人物、原文段落、年份、地圖視角或待審輸入。
- 全頁 `lang` 反映介面語言；原文段落保留各自的 `lang`。

## 給開發者與代理

`assets/i18n.js` 提供 `t(key, params)`、`ui(key, params)` 及 `bindText(node, key, params)`。英文訊息為穩定鍵，中文對照置於 `assets/locale-zh.js`。以 `data-i18n` 明確標示可翻譯的介面文字，`data-i18n-aria-label` 等屬性支援輔助技術。插入值一律跳脫，不把譯文當成可執行 HTML。

只更新明確標記的 UI 節點，**不要對整個 DOM 進行字串替換**。`data-source-text`、閱讀器原文段落、`data-original` 引文、程式碼及輸入文字受保護。新增介面應採用上述函式，不在語言切換時重建輸入表單。

圖表在 `renwen:languagechange` 事件中更新標示並保留幾何視角。地圖中文模式優先用已錄中文地名；英文模式用既有英文顯示名稱，不創造新的歷史名稱。

`assets/locale-init.js` 在樣式載入前設定已儲存的頁面語言；它不處理文獻內容。無模型、翻譯服務或外部字型依賴。

## English summary

The UI defaults to Traditional Chinese. A persistent top-bar switch selects Chinese or English across the reader, people, and works pages. Source texts, quotations, canonical Chinese identities, source titles and historical calendar assertions are not translated or altered. Some editorial prose and evidence notes retain their original language.

Live switching updates explicitly bound labels in place. It preserves the active source and passage, map view, historical year, profile identity, open record sections and draft proposals. Tests include protected text, escaping, Chinese-calendar invariance, both languages, browser-storage restrictions, and persistence between page fixtures.

Language tagging references: https://www.w3.org/WAI/WCAG22/Understanding/language-of-page and https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts .
