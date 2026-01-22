import requests
import json

WEBHOOK_SECRET = "dev-secret"

# Simulate SendGrid webhook payload
payload = {
    "from": {
        "email": "tendongbrain@gmail.com"
    },
    "to": [
        {
            "email": "tendongnkengafac@gmail.com"
        }
    ],
    "subject": "Re: Daily Check-in",
    "text": "Today I worked on:\n- Fixed bug in authentication\n- Added new feature\n- Reviewed PRs",
    "html": "<p>Today I worked on:</p><ul><li>Fixed bug in authentication</li><li>Added new feature</li><li>Reviewed PRs</li></ul>"
}

response = requests.post(
    "http://localhost:8000/api/replies/email",
    json=payload,
    headers={"X-Webhook-Secret": WEBHOOK_SECRET}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")