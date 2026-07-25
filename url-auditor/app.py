from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import re

app = Flask(__name__)
CORS(app)

# Timeout for fetching pages (seconds)
FETCH_TIMEOUT = 10

def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def audit_url(url: str) -> dict:
    """
    Fetch the URL and return a structured audit report.
    Handles invalid URLs, timeouts, non-HTML, and network errors gracefully.
    """
    report = {
        "url": url,
        "success": False,
        "error": None,
        "http_status": None,
        "response_time_ms": None,
        "title": None,
        "meta_description": None,
        "h1_count": 0,
        "images_missing_alt": 0,
        "word_count": 0,
    }

    if not is_valid_url(url):
        report["error"] = "Invalid URL. Please include http:// or https://"
        return report

    start = time.time()
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; URL-Auditor/1.0; +https://digitalheroesco.com)"
        }
        response = requests.get(
            url,
            headers=headers,
            timeout=FETCH_TIMEOUT,
            allow_redirects=True,
        )
        elapsed_ms = round((time.time() - start) * 1000)

        report["http_status"] = response.status_code
        report["response_time_ms"] = elapsed_ms

        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            report["error"] = f"Non-HTML response (Content-Type: {content_type or 'unknown'})"
            return report

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("title")
        report["title"] = title_tag.get_text(strip=True) if title_tag else None

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_desc and meta_desc.get("content"):
            report["meta_description"] = meta_desc["content"].strip()
        else:
            # also check property="og:description"
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                report["meta_description"] = og_desc["content"].strip()

        # H1 count
        report["h1_count"] = len(soup.find_all("h1"))

        # Images missing alt
        images = soup.find_all("img")
        missing_alt = 0
        for img in images:
            alt = img.get("alt")
            if alt is None or (isinstance(alt, str) and not alt.strip()):
                missing_alt += 1
        report["images_missing_alt"] = missing_alt

        # Approximate word count (visible text)
        # Remove script/style
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        words = re.findall(r"\b\w+\b", text)
        report["word_count"] = len(words)

        report["success"] = True
        return report

    except requests.exceptions.Timeout:
        report["error"] = f"Request timed out after {FETCH_TIMEOUT} seconds"
        report["response_time_ms"] = round((time.time() - start) * 1000)
        return report
    except requests.exceptions.TooManyRedirects:
        report["error"] = "Too many redirects"
        return report
    except requests.exceptions.ConnectionError:
        report["error"] = "Connection error – could not reach the host"
        return report
    except requests.exceptions.RequestException as e:
        report["error"] = f"Request failed: {str(e)}"
        return report
    except Exception as e:
        report["error"] = f"Unexpected error while parsing: {str(e)}"
        return report


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/audit", methods=["POST", "GET"])
def api_audit():
    """
    Accepts URL via JSON body {"url": "..."} or query param ?url=...
    Returns JSON report.
    """
    url = None
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        url = data.get("url") or request.form.get("url")
    else:
        url = request.args.get("url")

    if not url or not isinstance(url, str) or not url.strip():
        return jsonify({
            "success": False,
            "error": "Missing or empty 'url' parameter"
        }), 400

    url = url.strip()
    report = audit_url(url)
    status_code = 200 if report["success"] else 400
    return jsonify(report), status_code


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For local development only
    app.run(host="0.0.0.0", port=5000, debug=True)
