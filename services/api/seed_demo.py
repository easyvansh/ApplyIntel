from __future__ import annotations

import json
import os
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


DEMO_APPLICATIONS = [
    ("OpenAI", "Software Engineer, Applied AI", "San Francisco, CA", "interview", -21, 0),
    ("Stripe", "Backend Engineer", "Remote", "applied", -12, 2),
    ("Figma", "Product Engineer", "Remote", "interview", -28, 1),
    ("Canva", "Frontend Engineer", "Bengaluru, India", "offer", -45, 3),
    ("Atlassian", "Platform Engineer", "Bengaluru, India", "applied", -8, 0),
    ("Notion", "Full Stack Engineer", "Remote", "saved", -2, 5),
    ("GitHub", "Site Reliability Engineer", "Remote", "rejected", -62, None),
    ("Microsoft", "Cloud Software Engineer", "Hyderabad, India", "interview", -18, 4),
    ("Amazon", "Software Development Engineer", "Bengaluru, India", "applied", -6, 1),
    ("Adobe", "Machine Learning Engineer", "Noida, India", "saved", -1, 7),
    ("Spotify", "Data Engineer", "London, UK", "rejected", -52, None),
    ("Airbnb", "Senior Backend Engineer", "Remote", "offer", -39, 2),
]


def request_json(method: str, path: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        f"{API_BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json", "X-Request-ID": "demo-seed"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def seed_demo_data() -> None:
    today = date.today()
    created = 0
    skipped = 0

    for company, role, location, status, applied_offset, follow_up_offset in DEMO_APPLICATIONS:
        query = urlencode({"q": company, "limit": 100})
        existing = request_json("GET", f"/applications?{query}")["items"]
        if any(item["company"] == company and item["role"] == role for item in existing):
            skipped += 1
            continue

        next_action_date = (
            (today + timedelta(days=follow_up_offset)).isoformat()
            if follow_up_offset is not None
            else None
        )
        request_json(
            "POST",
            "/applications",
            {
                "company": company,
                "role": role,
                "location": location,
                "url": f"https://example.com/jobs/{company.lower()}",
                "status": status,
                "date_applied": (today + timedelta(days=applied_offset)).isoformat(),
                "next_action_date": next_action_date,
                "notes": "Demo record for local development and screenshots.",
            },
        )
        created += 1

    print(f"Demo seed complete: {created} created, {skipped} already present.")


if __name__ == "__main__":
    seed_demo_data()
