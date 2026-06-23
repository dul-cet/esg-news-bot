import time
from typing import Optional
import requests
from config import NETWORK_CONFIG


def safe_get(
    url: str,
    *,
    session: Optional[requests.Session] = None,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: Optional[int] = None,
):
    """HTTP GET with timeout + retries to improve parser resiliency."""
    req_timeout = timeout or NETWORK_CONFIG['request_timeout_sec']
    retries = max(1, NETWORK_CONFIG['max_retries'])
    backoff = max(0.0, NETWORK_CONFIG['retry_backoff_sec'])
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            client = session if session is not None else requests
            response = client.get(url, headers=headers, params=params, timeout=req_timeout)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(backoff * attempt)

    if last_error:
        raise last_error
    raise RuntimeError('safe_get failed without explicit exception')
