# 集合社 Collective Society

GitHub Pages website for **集合社 (Collective Society)**.

**Live site** (after enabling Pages):  
https://KelvinHoKaHim.github.io/collective-society/

## Pages

| Page | File | Description |
|------|------|-------------|
| 主頁 | `index.html` | Home / introduction |
| 過往活動 | `events.html` | Past events |
| 筆記 | `notes.html` | Notes & PDFs (linked from Google Drive) |

## How to enable GitHub Pages

1. Go to the repository **Settings** → **Pages**
2. Under **Build and deployment** → **Source**, choose **Deploy from a branch**
3. Branch: `main` / folder: `/ (root)`
4. Click **Save**
5. Wait 1–2 minutes, then visit the URL above

## Adding / updating notes (Google Drive PDFs)

1. Upload the PDF to Google Drive
2. Right-click → **Share** → General access: **Anyone with the link** → Viewer
3. Copy the link (or just the File ID)
4. Edit `notes.html` and add a new card using the pattern already there:

```html
<article class="note-card">
  <div class="note-meta">2026-XX-XX · 分類</div>
  <h3>筆記標題</h3>
  <p>簡短描述……</p>
  <a class="btn" href="https://drive.google.com/file/d/YOUR_FILE_ID/view" target="_blank" rel="noopener">開啟 PDF</a>
</article>
```

You can also change `/view` to `/preview` if you prefer the Drive preview player, or embed a whole folder with the iframe example at the bottom of `notes.html`.

## Local development

Just open the HTML files in a browser, or use any static server:

```bash
npx serve .
```

## License

Feel free to use and modify for 集合社.
