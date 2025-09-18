import httpx

def test_connection():
    url = f"{SUPABASE_URL}/rest/v1/"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        print("Status:", r.status_code)
        print("Response:", r.text[:200])
    except Exception as e:
        print("❌ Connect error:", e)
