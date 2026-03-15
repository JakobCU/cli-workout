"""Webhook integration for workout completion notifications."""

import json
import urllib.request


def send_webhook(url, payload):
    """POST JSON to a webhook URL. Failures are silently caught."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # webhook failure should never crash the app
