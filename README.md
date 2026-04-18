# youtube-transcript-saver

A desktop app to paste a YouTube URL/video ID and save transcript output locally.

## MVP scope
- URL/video ID input.
- Format choice: `TXT`, `MD`, or `Both`.
- Save mode:
  - Ask for folder every time.
  - Use a default folder.
- Save action button.
- Status/error line for feedback.

## Out of scope for MVP
- Clipboard auto-detect.
- Drag/drop support.
- Batch mode.
- In-app summarization.
- Browser extension integration.

## Local run flow
1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Run the app locally:
   ```bash
   python3 app.py
   ```

## macOS app package build flow (py2app)
1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Build the `.app` bundle:
   ```bash
   python3 setup.py py2app
   ```
3. Find the built app artifact under:
   - `dist/*.app`
