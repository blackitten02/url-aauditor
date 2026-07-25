# URL Auditor

A small Flask web tool that fetches a public URL and returns a concise page-health report. It is designed to make basic technical and content checks quick without pretending that every website is equally accessible from a cloud server.

**Live demo:** https://url-auditor-rngo.onrender.com/

**Loom demo:** _Add your Loom share link here after recording._

Built for [Digital Heroes Training Task](https://digitalheroesco.com/).

---

## What it reports

For an HTML page, the tool returns:

- HTTP status code
- Response time in milliseconds
- Page title
- Meta description (including an `og:description` fallback)
- H1 count
- Number of images with a missing or blank `alt` attribute
- Approximate visible word count

It also returns controlled, readable errors for malformed URLs, timeouts, connection failures, excessive redirects, and non-HTML responses.

## Tech stack

- **Backend:** Python, Flask, Requests, Beautiful Soup
- **Frontend:** HTML, CSS, and vanilla JavaScript
- **Tests:** Pytest with mocked HTTP requests
- **Deployment:** Render

---

## Local setup

### Prerequisites

- Python 3.12 or later
- Git (only needed if you clone the repository)

### 1. Clone and enter the app folder

```bash
git clone https://github.com/blackitten02/url-aauditor.git
cd url-aauditor/url-auditor
```

> The application currently lives in the repository's `url-auditor` subfolder. Render is configured with that folder as its Root Directory.

### 2. Create and activate a virtual environment

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows PowerShell**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install application dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

```bash
python app.py
```

Open http://127.0.0.1:5000 in a browser.

---

## Running the tests

Install the development dependencies, then run Pytest:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The test suite does **not** make live requests to third-party websites. It mocks `requests.get`, so the tests are deterministic, fast, and safe to run repeatedly. A GitHub Actions workflow also runs `pytest -q` on every push and pull request using Python 3.12.

### Test coverage

| Test | Why it matters |
| --- | --- |
| HTML happy path | Confirms title, description, headings, image-alt count, and word count are extracted correctly. |
| Invalid URL | Confirms malformed input is rejected before a network request is made. |
| Timeout | Confirms a slow target produces a useful error rather than an unhandled exception. |
| Non-HTML response | Confirms documents such as PDFs are not incorrectly parsed as webpages. |
| Missing API input | Confirms the public endpoint returns a clear `400` response for an invalid request. |

---

## API contract

### `POST /api/audit`

Audits a URL sent as JSON.

#### Request

```http
POST /api/audit
Content-Type: application/json
```

```json
{
  "url": "https://example.com"
}
```

### `GET /api/audit?url=https://example.com`

The endpoint also accepts a URL as a query parameter, which is useful for quick manual checks.

### Successful response — `200 OK`

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

### Error response — `400 Bad Request`

For an invalid URL, the API returns a structured report rather than an HTML error page:

```json
{
  "url": "not-a-url",
  "success": false,
  "error": "Invalid URL. Please include http:// or https://",
  "http_status": null,
  "response_time_ms": null,
  "title": null,
  "meta_description": null,
  "h1_count": 0,
  "images_missing_alt": 0,
  "word_count": 0
}
```

If the `url` field is missing entirely, the response is:

```json
{
  "success": false,
  "error": "Missing or empty 'url' parameter"
}
```

---

## Design decisions

### 1. Validate in both the browser and the API

The browser adds `https://` when a user enters a bare domain, which reduces a common point of friction. The backend still validates the scheme and hostname independently because API consumers can bypass the browser. This gives a convenient UI without relying on client-side validation for correctness.

### 2. Use a bounded request with redirect support

External websites can be slow, unavailable, or redirect to their canonical address. The fetch uses a 10-second timeout and follows redirects. The timeout keeps one target from leaving the user waiting indefinitely; following redirects better reflects what a browser user experiences. Timeouts, connection failures, and redirect loops are returned as readable JSON errors instead of crashing the service.

### 3. Parse only `text/html`

A PDF, image, or download might return a valid HTTP status but has no HTML title, headings, or DOM images to inspect. The tool checks the response content type before parsing, then returns a clear non-HTML error. This avoids misleading data and prevents the HTML parser from being used on the wrong kind of resource.

### 4. Count visible content rather than raw source text

Before counting words, the parser removes `script`, `style`, and `noscript` elements. This makes the word count closer to what a visitor can read, instead of inflating it with JavaScript or CSS. It is intentionally an approximation, not an SEO-grade content analysis.

---

## Limitations and next improvement

The results reflect the HTML returned to Render's server. JavaScript-rendered pages may have incomplete content, and some sites block requests from cloud-server IP addresses. In those cases, a connection error can describe the target site's access policy rather than a deployment failure.

With another day, the first improvement I would make is **SSRF protection**. The app currently accepts a user-controlled URL after basic HTTP/HTTPS validation. Before a production release, I would resolve hostnames, reject loopback, private, link-local, and reserved IP ranges, and repeat that validation for redirect targets. This would reduce the risk of an arbitrary-URL tool being used to probe internal services.

One accessibility nuance is also worth noting: the MVP treats a blank `alt=""` value the same as a missing `alt` attribute. A more advanced version would distinguish intentionally decorative images from images whose alternative text is genuinely missing.

---

## Deploying on Render

This repository has the app inside the `url-auditor` subfolder. Configure the Render web service as follows:

| Setting | Value |
| --- | --- |
| Root Directory | `url-auditor` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 30` |
| Python version environment variable | `PYTHON_VERSION=3.12.4` |

---

## AI assistance

AI tools (Grok and Arena.ai) were used as learning and development assistants: to understand the Flask/Render workflow, create and review an initial implementation, troubleshoot the first deployment issue, and plan test cases. The live app and its failure cases were then tested manually. I have documented the implementation choices and limitations above, and can explain the code paths and trade-offs in an interview.
