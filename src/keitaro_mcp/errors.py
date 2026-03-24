"""Keitaro API error types."""


class KeitaroError(Exception):
    """API error with HTTP status, response body, and URL."""

    def __init__(self, status_code: int, body: str, url: str):
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(f"HTTP {status_code} for {url}: {body[:200]}")
