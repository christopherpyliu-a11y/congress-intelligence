# CONGRESS.IQ

美國國會新聞暨台美關係公開資訊監測網站。

## 已接入的新聞擷取機制

- `scripts/fetch_news.py` 使用公開 RSS 蒐集 The Hill（House / Senate）、Roll Call、Defense News（Congress）、Politico（Congress）的新聞。
- `.github/workflows/update-news.yml` 由 GitHub Actions 每小時執行一次，也支援手動觸發。
- `news.json` 為靜態網站使用的共享資料檔，包含來源、原文連結、實際發布日期、標題、原始摘要及分類。
- `news-status.json` 顯示最近執行時間、擷取數量、失敗來源及故障資訊。
- 當次無新增新聞，保留最近五日內已取得、附有有效原文連結的資料；超過五日自動移除。
- 所有資料為公開 RSS 擷取，**尚未提供 AI 中文翻譯或已核實的政策分析**；來源摘要會保持原語言。RSS 服務可能變更或封鎖擷取，請依 `news-status.json` 檢查狀態。來源覆蓋範圍不等於整個國會的完整新聞。

## 首次啟用

1. 開啟 GitHub Repository → Actions → Refresh congressional news。
2. 按 **Run workflow** 觸發首次同步。之後依排程每小時更新（GitHub Actions 排程可能延遲）。
3. 如需公開網址，在 Settings → Pages 設定 Deploy from a branch、main、/(root)。
4. 同步完成後，查看 `news.json` 與 `news-status.json` 檢查實際取得的新聞和失敗來源。

## 後續擴充

Congress.gov 官方法案 API、委員會議程及議員聲明尚須各自建立擷取器；AI 中文摘要、翻譯、Email 通知及保護內部資料的後端也尚未啟用。

請勿將 API keys、個人或內部業務資料提交到公開 Repository。
