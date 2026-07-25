# URL Auditor

A simple web tool that audits any URL and returns a structured report.

**Live demo:** https://url-auditor-rngo.onrender.com

Built for [Digital Heroes Training Task](https://digitalheroesco.com).

## Features

- HTTP status code
- Response time (ms)
- Page title
- Meta description
- H1 count
- Images missing `alt` text
- Approximate word count
- Clean error handling for invalid URLs, timeouts, non-HTML responses

## Tech stack

- Backend: Python + Flask + BeautifulSoup + requests
- Frontend: Vanilla HTML / CSS / JS
- Deploy: Render (free tier) or any WSGI host

## API

### `POST /api/audit`

**Request body (JSON):**
```json
{ "url": "https://example.com" }
```

**Success response (200):**
```json
{
  "url": "https://example.com",
  "success": true,
  "error": null,
  "http_status": 200,
  "response_time_ms": 312,
  "title": "Example Domain",
  "meta_description": null,
  "h1_count": 1,
  "images_missing_alt": 0,
  "word_count": 28
}
```

**Error response (400):**
```json
{
  "url": "not-a-url",
  "success": false,
  "error": "Invalid URL. Please include http:// or https://",
  ...
}
```

Also accepts `GET /api/audit?url=https://example.com`

## Local development

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploy on Render (free)

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect the repo
4. Settings:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 30`
5. Create Web Service → wait for deploy

Your live URL will look like `https://url-auditor-xxxx.onrender.com`
