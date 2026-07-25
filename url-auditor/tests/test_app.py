"""Tests for the URL audit parsing and error-handling logic."""

from unittest.mock import ANY, Mock, patch

import pytest
import requests

from app import FETCH_TIMEOUT, app, audit_url


HTML_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <title>Sample page</title>
    <meta name="description" content="A concise test description.">
    <style>.hidden { display: none; }</style>
  </head>
  <body>
    <h1>First heading</h1>
    <h1>Second heading</h1>
    <p>Useful copy for visitors.</p>
    <img src="logo.png" alt="Company logo">
    <img src="missing-alt.png">
    <img src="blank-alt.png" alt="">
    <script>this text must not be counted</script>
  </body>
</html>
"""


def fake_response(*, status_code=200, content_type="text/html; charset=utf-8", text=""):
    """Build the small subset of a requests response used by audit_url."""
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": content_type}
    response.text = text
    return response


@patch("app.requests.get")
def test_audit_url_extracts_metrics_from_html(mock_get):
    """Happy path: HTML metadata and visible-content metrics are extracted."""
    mock_get.return_value = fake_response(text=HTML_PAGE)

    report = audit_url("https://example.test/page")

    assert report["success"] is True
    assert report["error"] is None
    assert report["http_status"] == 200
    assert report["response_time_ms"] is not None
    assert report["title"] == "Sample page"
    assert report["meta_description"] == "A concise test description."
    assert report["h1_count"] == 2
    # The current product rule flags both a missing alt attribute and a blank one.
    assert report["images_missing_alt"] == 2
    # title (2 words) + two H1s (4 words) + paragraph (4 words)
    assert report["word_count"] == 10
    mock_get.assert_called_once_with(
        "https://example.test/page",
        headers=ANY,
        timeout=FETCH_TIMEOUT,
        allow_redirects=True,
    )


@patch("app.requests.get")
def test_audit_url_rejects_an_invalid_url_without_fetching(mock_get):
    """Failure path: malformed input is rejected before any network call."""
    report = audit_url("not a url")

    assert report["success"] is False
    assert report["http_status"] is None
    assert report["error"] == "Invalid URL. Please include http:// or https://"
    mock_get.assert_not_called()


@patch("app.requests.get", side_effect=requests.exceptions.Timeout)
def test_audit_url_returns_a_clear_timeout_error(mock_get):
    """Failure path: a slow target produces a controlled error report."""
    report = audit_url("https://slow.example.test")

    assert report["success"] is False
    assert report["http_status"] is None
    assert report["response_time_ms"] is not None
    assert report["error"] == f"Request timed out after {FETCH_TIMEOUT} seconds"
    mock_get.assert_called_once()


@patch("app.requests.get")
def test_audit_url_does_not_try_to_parse_a_non_html_response(mock_get):
    """Failure path: binary/non-HTML content returns an explanatory error."""
    mock_get.return_value = fake_response(
        status_code=200,
        content_type="application/pdf",
        text="not html",
    )

    report = audit_url("https://example.test/document.pdf")

    assert report["success"] is False
    assert report["http_status"] == 200
    assert report["title"] is None
    assert report["word_count"] == 0
    assert report["error"] == "Non-HTML response (Content-Type: application/pdf)"


@pytest.fixture
def client():
    """Flask's test client exercises the public API without starting a server."""
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_api_returns_400_when_url_is_missing(client):
    """API contract: missing input is a client error, not an unhandled exception."""
    response = client.post("/api/audit", json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "success": False,
        "error": "Missing or empty 'url' parameter",
    }
