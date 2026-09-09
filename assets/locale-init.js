/* Synchronous language hint before styles render; works when browser storage is blocked. */
(() => {
  let language = 'zh-Hant';
  try { if (localStorage.getItem('ren-wen:language:v1') === 'en') language = 'en'; } catch { /* Chinese default. */ }
  document.documentElement.lang = language;
})();
