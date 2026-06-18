#!/usr/bin/env python3
"""Email the day's Market Prompt issue to the Resend audience.

Reads the generated newsletters/<date>.html, builds a short teaser email that
links back to the full issue on the website, and sends it to the whole audience
via Resend Broadcasts.

Environment:
  RESEND_API_KEY      Resend API key                         (required)
  RESEND_AUDIENCE_ID  Resend audience / list to send to      (required)
  MP_FROM             From header, e.g.
                      "Market Prompt <brief@yourdomain.com>"  (required)
  SITE_URL            Public site base used in the email links
                      (optional; defaults to the GitHub Pages URL)

Usage:  python3 send_email.py [YYYY-MM-DD]   (defaults to today, Europe/London)

If the required env vars are missing it prints a notice and exits 0, so it can
sit in the daily workflow harmlessly until Resend is configured.
"""

import os
import sys
import json
import html
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import build  # reuse the site's own parser + helpers

API = "https://api.resend.com"
DEFAULT_SITE = "https://gracious223.github.io/market-prompt"


def _post(path, payload, key):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode() or "{}")


def render_email(name, date_label, bullets, headlines, issue_url, site_url):
    items = "".join(
        f'<li style="margin:0 0 10px;color:#3c3c50;font-size:15px;line-height:1.6">{html.escape(b)}</li>'
        for b in bullets
    )
    heads = "".join(
        f'<li style="margin:0 0 8px;color:#14142b;font-size:15px;line-height:1.5;font-weight:600">{html.escape(h)}</li>'
        for h in headlines
    )
    heads_block = (
        f'<p style="margin:22px 0 6px;font-family:Georgia,serif;font-size:13px;'
        f'letter-spacing:1px;text-transform:uppercase;color:#8a8fa8">In today\'s brief</p>'
        f'<ul style="margin:0;padding-left:18px">{heads}</ul>'
        if headlines else ""
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;background:#f6f3ec;font-family:Helvetica,Arial,sans-serif">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f3ec;padding:28px 12px">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8e3d8">
        <tr><td style="background:#14142b;padding:26px 32px;text-align:center">
          <div style="font-family:Georgia,serif;font-weight:800;font-size:22px;color:#f6f3ec">Market <span style="color:#c9a96e">Prompt</span></div>
          <div style="margin-top:6px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#c9a96e">{html.escape(date_label)} · Daily Brief</div>
        </td></tr>
        <tr><td style="padding:30px 32px 8px">
          <h1 style="margin:0 0 14px;font-family:Georgia,serif;font-size:24px;line-height:1.25;color:#14142b">{html.escape(name)}</h1>
          <ul style="margin:0;padding-left:18px">{items}</ul>
          {heads_block}
        </td></tr>
        <tr><td style="padding:24px 32px 32px" align="center">
          <a href="{html.escape(issue_url)}" style="display:inline-block;background:#c9a96e;color:#14142b;font-weight:700;font-size:15px;text-decoration:none;padding:14px 30px;border-radius:999px">Read today's full brief →</a>
          <p style="margin:16px 0 0;font-size:12px;color:#8a8fa8">No jargon. One quick read. Every term explained.</p>
        </td></tr>
        <tr><td style="background:#faf7f0;padding:22px 32px;text-align:center;border-top:1px solid #e8e3d8">
          <p style="margin:0 0 8px;font-size:13px;color:#5b5f78">More editions at <a href="{html.escape(site_url)}" style="color:#14142b;font-weight:600">Market Prompt</a></p>
          <p style="margin:0;font-size:11px;color:#a0a0b0">You're getting this because you signed up at Market Prompt.
            <a href="{{{{{{RESEND_UNSUBSCRIBE_URL}}}}}}" style="color:#8a8fa8">Unsubscribe</a></p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def main():
    key = os.environ.get("RESEND_API_KEY")
    audience = os.environ.get("RESEND_AUDIENCE_ID")
    sender = os.environ.get("MP_FROM")
    site = (os.environ.get("SITE_URL") or DEFAULT_SITE).rstrip("/")

    if not (key and audience and sender):
        print("Email not configured (need RESEND_API_KEY, RESEND_AUDIENCE_ID, MP_FROM) — skipping send.")
        return 0

    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d")
    path = Path("newsletters") / f"{date}.html"
    if not path.exists():
        print(f"No issue at {path} — nothing to send.")
        return 0

    d = build.parse_issue(path)
    bullets = build.summary_points(d["summary"], n=3, maxwords=22) or [d["summary"]]
    headlines = [s["stories"][0]["title"] for s in d["sectionlist"][:3] if s["stories"]]
    issue_url = f"{site}/newsletters/{date}.html"

    subject = f"Market Prompt — {d['name']}"
    body = render_email(d["name"], d["date_label"], bullets, headlines, issue_url, site)

    try:
        bc = _post("/broadcasts", {
            "audience_id": audience,
            "from": sender,
            "subject": subject,
            "html": body,
            "name": f"Market Prompt {date}",
        }, key)
        bid = bc.get("id")
        if not bid:
            print("Failed to create broadcast:", bc)
            return 1
        _post(f"/broadcasts/{bid}/send", {}, key)
        print(f"Sent broadcast {bid} ({subject}) to audience {audience}.")
        return 0
    except urllib.error.HTTPError as e:
        print(f"Resend API error {e.code}: {e.read().decode(errors='ignore')}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
