"""Minimal endpoint test with JWT authentication — ASCII-safe output."""
import urllib.request, json, sys

BASE = "http://localhost:8000"
TEST_EMAIL = "test@liquisense.com"
TEST_PASSWORD = "TestPass123"


def post(path, data, token=None):
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


errors = []
token = None

# 1. Health check (no auth needed)
try:
    d = get("/api/health")
    print(f"[OK] Health: {d['status']}")
except Exception as e:
    errors.append(f"[FAIL] Health: {e}")
    print(errors[-1])

# 2. Sign up (or sign in if already exists)
try:
    try:
        d = post("/api/auth/signup", {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        })
        token = d["access_token"]
        print(f"[OK] Signup: user={d['user']['email']}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            # Already exists, sign in
            d = post("/api/auth/signin", {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            })
            token = d["access_token"]
            print(f"[OK] Signin (existing): user={d['user']['email']}")
        else:
            raise
except Exception as e:
    errors.append(f"[FAIL] Auth: {e}")
    print(errors[-1])
    print("Cannot proceed without token. Exiting.")
    sys.exit(1)

# 3. Get current user
try:
    d = get("/api/auth/me", token)
    print(f"[OK] Me: email={d['email']}, id={d['id']}")
except Exception as e:
    errors.append(f"[FAIL] Me: {e}")
    print(errors[-1])

# 4. Dashboard
try:
    d = get("/api/dashboard", token)
    print(f"[OK] Dashboard: balance={d['current_balance']}")
except Exception as e:
    errors.append(f"[FAIL] Dashboard: {e}")
    print(errors[-1])

# 5. Forecast
try:
    d = get("/api/dashboard/forecast?days=5", token)
    print(f"[OK] Forecast: {len(d.get('forecast', []))} points")
except Exception as e:
    errors.append(f"[FAIL] Forecast: {e}")
    print(errors[-1])

# 6. Transactions
try:
    d = get("/api/transactions", token)
    print(f"[OK] Transactions: total={d['total']}")
except Exception as e:
    errors.append(f"[FAIL] Transactions: {e}")
    print(errors[-1])

# 7. Affordability check
try:
    result = post(
        "/api/affordability",
        {
            "name": "Office Laptop",
            "amount": 80000,
            "category": "Equipment",
            "date": "2026-03-28T00:00:00",
        },
        token,
    )
    print(f"[OK] Affordability: decision={result['decision']}")
except Exception as e:
    errors.append(f"[FAIL] Affordability: {e}")
    print(errors[-1])

# 8. Affordability history
try:
    d = get("/api/affordability/history", token)
    print(f"[OK] History: total={d['total']}")
except Exception as e:
    errors.append(f"[FAIL] History: {e}")
    print(errors[-1])

# 9. Categories (no auth needed)
try:
    d = get("/api/dashboard/categories")
    print(f"[OK] Categories: {len(d.get('categories', []))} categories")
except Exception as e:
    errors.append(f"[FAIL] Categories: {e}")
    print(errors[-1])


print()
if errors:
    print(f"=== {len(errors)} FAILURE(S) ===")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("=== ALL CHECKS PASSED ===")
