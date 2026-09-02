"""List model ids from an OpenAI-compatible endpoint configured in .env."""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv

API_KEY_ENV = "OPENAI_API_KEY"
BASE_URL_ENV = "OPENAI_BASE_URL"


def normalize_openai_base_url(raw_base_url: str) -> str:
    base_url = raw_base_url.strip().rstrip("/")
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"{BASE_URL_ENV} is not a valid URL: {raw_base_url!r}")
    if parsed.path in ("", "/"):
        return f"{base_url}/v1"
    return base_url


def request_models(base_url: str, api_key: str) -> dict[str, Any]:
    url = f"{base_url}/models"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body[:1000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot connect to {url}: {exc.reason}") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        preview = body[:500].replace("\n", " ")
        raise RuntimeError(
            "The endpoint did not return JSON. "
            f"Tried {url}. Response preview: {preview!r}"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Expected a JSON object from {url}, got {type(payload).__name__}"
        )
    return payload


def print_model_ids(payload: dict[str, Any]) -> int:
    data = payload.get("data")
    if not isinstance(data, list):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    count = 0
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            print(item["id"])
            count += 1
    return count


def main() -> int:
    load_dotenv()

    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        print(f"Set {API_KEY_ENV} in .env first.", file=sys.stderr)
        return 2

    raw_base_url = os.getenv(BASE_URL_ENV)
    if not raw_base_url:
        print(
            f"Set {BASE_URL_ENV}, for example https://api.centos.hk/v1", file=sys.stderr
        )
        return 2

    try:
        base_url = normalize_openai_base_url(raw_base_url)
        payload = request_models(base_url, api_key)
        count = print_model_ids(payload)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"\n{count} model(s) returned from {base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
