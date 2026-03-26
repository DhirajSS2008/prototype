"""Direct API tests for insurance, email drafting, and vendor features."""
import requests
import json

BASE = "http://localhost:8000/api"

# Try signin, if fails try signup
r = requests.post(f"{BASE}/auth/signin", json={"email": "test_api@test.com", "password": "test123"})
if r.status_code != 200:
    r = requests.post(f"{BASE}/auth/signup", json={"name": "API Test", "email": "test_api@test.com", "password": "test123"})
    print(f"Signup: {r.status_code}")
    r = requests.post(f"{BASE}/auth/signin", json={"email": "test_api@test.com", "password": "test123"})

data = r.json()
token = data.get("access_token") or data.get("token")
headers = {"Authorization": f"Bearer {token}"}
print(f"Auth: OK (token={token[:20]}...)")

print("\n=== 1. Create Insurance Policy ===")
r = requests.post(f"{BASE}/insurance", headers=headers, json={
    "policy_name": "Business Health Cover",
    "provider": "Star Health",
    "coverage_type": "health",
    "coverage_amount": 500000,
    "claim_limit": 500000,
    "used_claims": 0,
    "expiry_date": "2026-12-31T00:00:00",
})
print(f"Create Policy: {r.status_code}")
policy = r.json()
print(f"  Created: {policy.get('policy_name')} (ID={policy.get('id')})")

print("\n=== 2. List Insurance Policies ===")
r = requests.get(f"{BASE}/insurance", headers=headers)
policies = r.json().get("policies", [])
print(f"Policies: {len(policies)}")
for p in policies:
    print(f"  - {p['policy_name']} ({p['coverage_type']}) cover={p['coverage_amount']} remain={p.get('remaining_claim_limit')}")

print("\n=== 3. Create Vendor Contact ===")
r = requests.post(f"{BASE}/vendors", headers=headers, json={
    "vendor_name": "City Hospital",
    "email": "billing@cityhospital.com",
    "relationship_type": "local_vendor",
    "outstanding_amount": 50000,
})
print(f"Create Vendor: {r.status_code}")
print(f"  Created: {r.json().get('vendor_name')}")

print("\n=== 4. Affordability Check (Health & Medical) ===")
r = requests.post(f"{BASE}/affordability", headers=headers, json={
    "name": "Surgery Bill",
    "amount": 200000,
    "date": "2026-04-15T00:00:00",
    "category": "Health & Medical",
})
result = r.json()
print(f"Decision: {result.get('decision')}")
print(f"Reason: {result.get('reason_code')}")
ins = result.get("insurance_coverage")
if ins:
    print(f"Insurance Status: {ins['coverage_status']}")
    print(f"Total Claimable: {ins['total_claimable']}")
    print(f"Net After Insurance: {ins['net_expense_after_insurance']}")
    for p in ins.get("policies_found", []):
        print(f"  Policy: {p.get('policy_name')} can_claim={p.get('can_claim')}")
    if ins.get("warnings"):
        print(f"Warnings: {ins['warnings']}")
else:
    print("WARNING: No insurance_coverage in response!")

ai = result.get("ai_explanation", "")
print(f"\nAI Explanation: {ai[:300]}")

print("\n=== 5. Generate Negotiation Email (Gemini) ===")
r2 = requests.post(f"{BASE}/affordability/generate-action-email", headers=headers, json={
    "result": result,
    "path": {
        "path_type": "defer_obligation",
        "description": "Defer rent payment to free up cash for medical bill",
        "obligation_name": "Shop Rent Landlord",
        "deferral_days": 15,
    },
    "recipient_type": "landlord",
})
print(f"Email Gen Status: {r2.status_code}")
if r2.status_code == 200:
    email = r2.json().get("email", {})
    print(f"Subject: {email.get('subject', 'N/A')}")
    body = email.get("body", "")
    print(f"Body ({len(body)} chars): {body[:300]}")
else:
    print(f"Error: {r2.text[:200]}")

print("\n=== 6. Generate Borrowing Email (Gemini) ===")
r3 = requests.post(f"{BASE}/affordability/generate-action-email", headers=headers, json={
    "result": result,
    "path": {
        "path_type": "short_term_borrowing",
        "description": "Short-term borrowing to cover medical expense",
        "borrowing_amount": 175000,
        "borrowing_cost": 2625,
    },
    "recipient_type": "bank",
})
print(f"Borrowing Email Status: {r3.status_code}")
if r3.status_code == 200:
    email = r3.json().get("email", {})
    print(f"Subject: {email.get('subject', 'N/A')}")
    print(f"Body (preview): {email.get('body', '')[:300]}")
else:
    print(f"Error: {r3.text[:200]}")

print("\n=== 7. Expiring Policies ===")
r = requests.get(f"{BASE}/insurance/expiring?days=365", headers=headers)
print(f"Expiring within 365d: {r.json().get('count', 0)}")

print("\n=== ALL TESTS COMPLETE ===")
