#!/usr/bin/env python3
"""
Generate notes.html from a Google Drive folder and (optionally) commit it.

Designed to run inside GitHub Actions.
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------- Configuration (can be overridden by env) ----------
FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "").strip()
OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH", "notes.html"))
# Only include these mime types (empty list = include everything that has a webViewLink)
ALLOWED_MIME_TYPES = {
    "application/pdf",
    # Uncomment if you also want Google Docs, Sheets, etc.
    # "application/vnd.google-apps.document",
    # "application/vnd.google-apps.spreadsheet",
    # "application/vnd.google-apps.presentation",
}

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    """Create Drive API service from service-account JSON in env or file."""
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # Fallback for local testing
        key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_files_in_folder(service, folder_id: str) -> list[dict[str, Any]]:
    """Return all non-trashed files in the folder, newest first."""
    if not folder_id:
        raise ValueError("DRIVE_FOLDER_ID is not set")

    query = f"'{folder_id}' in parents and trashed = false"
    files: list[dict[str, Any]] = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, size, description)",
                orderBy="modifiedTime desc",
                pageSize=100,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    # Optional mime-type filter
    if ALLOWED_MIME_TYPES:
        files = [f for f in files if f.get("mimeType") in ALLOWED_MIME_TYPES]

    return files


def format_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        # Drive returns RFC 3339
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso[:10]


def clean_title(name: str) -> str:
    """Remove common extensions for nicer display."""
    for ext in (".pdf", ".PDF", ".docx", ".doc"):
        if name.endswith(ext):
            return name[: -len(ext)]
    return name


def build_notes_html(files: list[dict[str, Any]]) -> str:
    """Generate a complete notes.html that matches the existing site design."""

    cards = []
    for f in files:
        title = clean_title(f.get("name", "Untitled"))
        date = format_date(f.get("modifiedTime"))
        file_id = f["id"]
        # Prefer the official webViewLink when available, otherwise construct
        link = f.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
        desc = f.get("description") or ""

        # Simple category heuristic from filename (optional, can be improved)
        category = "筆記"
        lower = title.lower()
        if any(k in lower for k in ("現象", "husserl", "heidegger", "phenomen")):
            category = "現象學"
        elif any(k in lower for k in ("數學", "math", "分析", "analysis")):
            category = "數學 / 哲學"

        cards.append(
            f"""      <article class="note-card">
        <div class="note-meta">{date} · {category}</div>
        <h3>{title}</h3>
        <p>{desc if desc else "點擊下方按鈕開啟 PDF。"}</p>
        <a class="btn" href="{link}" target="_blank" rel="noopener">開啟 PDF</a>
      </article>"""
        )

    cards_html = "\n".join(cards) if cards else "      <p style=\"color:var(--text-muted)\">目前資料夾中沒有符合條件的檔案。</p>"

    # Full page – keep structure identical to the static version
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>筆記 · 集合社 Collective Society</title>
  <meta name="description" content="集合社筆記與 PDF 分享（自動從 Google Drive 更新）" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a href="index.html" class="logo">集合社 <span>Collective Society</span></a>
      <nav class="nav">
        <a href="index.html">主頁</a>
        <a href="events.html">過往活動</a>
        <a href="notes.html" class="active">筆記</a>
      </nav>
    </div>
  </header>

  <main>
    <h1 class="section-title" style="margin-bottom:0.5rem;">筆記</h1>
    <p style="color:var(--text-muted); margin-bottom:2rem;">
      這裡的 PDF 存放於 Google Drive，並由 GitHub Actions 自動同步。點擊「開啟 PDF」會在新分頁打開。
    </p>

    <div class="cards" style="margin-bottom:2.5rem;">
{cards_html}
    </div>

    <div class="hint">
      <strong>自動更新說明：</strong><br>
      本頁由 <code>generate_notes.py</code> + GitHub Actions 從指定的 Google Drive 資料夾產生。<br>
      只要把新的 PDF 放進該資料夾（並設為「知道連結的任何人可檢視」），大約每小時會自動更新一次。
    </div>
  </main>

  <footer class="site-footer">
    <p>© 集合社 Collective Society · <a href="https://github.com/KelvinHoKaHim/collective-society" target="_blank" rel="noopener">GitHub</a></p>
  </footer>
</body>
</html>
"""
    return html


def main() -> None:
    print("Authenticating with Google Drive…")
    service = get_drive_service()

    print(f"Listing files in folder: {FOLDER_ID}")
    files = list_files_in_folder(service, FOLDER_ID)
    print(f"Found {len(files)} file(s)")

    html = build_notes_html(files)

    # Write to disk
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(html)} bytes)")

    # Optional: print a short hash so the Action can detect changes easily
    digest = hashlib.sha256(html.encode()).hexdigest()[:12]
    print(f"Content hash: {digest}")


if __name__ == "__main__":
    try:
        main()
    except HttpError as e:
        print(f"Google API error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise
