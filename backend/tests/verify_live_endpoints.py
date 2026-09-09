import sys
import time
import json
import urllib.request
import urllib.error
from uuid import uuid4

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USER = "00000000-0000-0000-0000-000000000001"

def request(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Test-User-Id", TEST_USER)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=15) as res:
            res_data = res.read().decode("utf-8")
            elapsed = time.perf_counter() - t0
            return res.status, json.loads(res_data) if res_data else {}, elapsed
    except urllib.error.HTTPError as err:
        elapsed = time.perf_counter() - t0
        err_data = err.read().decode("utf-8")
        try:
            parsed = json.loads(err_data)
        except Exception:
            parsed = {"raw": err_data}
        return err.code, parsed, elapsed

def main():
    print(f"=== Testing Live Backend Distributed Endpoints on {BASE_URL} ===\n")

    # 1. Test Document Listing
    status, data, elapsed = request("GET", "/documents")
    print(f"[1] GET /documents -> HTTP {status} ({elapsed:.3f}s)")
    assert status == 200, f"Expected 200, got {status}"

    # 2. Test BKT Mastery Update & Lock Acquisition
    kc_id = str(uuid4())
    bkt_payload = {
        "user_id": TEST_USER,
        "kc_id": kc_id,
        "is_correct": True
    }
    status, bkt_data, elapsed = request("POST", "/bkt/update", bkt_payload)
    print(f"[2] POST /bkt/update -> HTTP {status} (p_l: {bkt_data.get('updated_p_l')}, lock acquired & released in {elapsed:.3f}s)")
    assert status == 200, f"Expected 200, got {status}"

    # 3. Test Distributed Artifact Caching Roundtrip
    folder_id = str(uuid4())
    artifact_payload = {
        "topic": "Distributed Consensus & Raft",
        "folder_id": folder_id,
        "learning_style": "visual",
        "workload_mode": "free",
        "custom_instructions": "Focus on Raft quorum replication"
    }
    print("[3] Testing Distributed Artifact Cache (Generating study artifact)...")
    status1, art1, elapsed1 = request("POST", "/artifacts/generate", artifact_payload)
    print(f"    Call 1 (Cache Miss): HTTP {status1} in {elapsed1:.3f}s -> Content length: {len(art1.get('content', ''))}")
    assert status1 == 200, f"Expected 200, got {status1}"

    status2, art2, elapsed2 = request("POST", "/artifacts/generate", artifact_payload)
    print(f"    Call 2 (Cache Hit):  HTTP {status2} in {elapsed2:.3f}s -> Speedup: {elapsed1 / max(elapsed2, 0.0001):.1f}x faster!")
    assert status2 == 200, f"Expected 200, got {status2}"
    assert elapsed2 < elapsed1, f"Cache hit ({elapsed2:.3f}s) must be faster than cache miss ({elapsed1:.3f}s)"

    # 4. Test Feynman Rate Limiting Backpressure
    print("\n[4] Testing Distributed Rate Limiting on /feynman/evaluate...")
    rate_limit_hit = False
    for i in range(1, 15):
        payload = {
            "concept": "Distributed Consensus",
            "student_explanation": f"Evaluation test iteration {i} on leader heartbeats."
        }
        status, res, elapsed = request("POST", "/feynman/evaluate", payload)
        if status == 429:
            print(f"    Request {i}: HTTP 429 Too Many Requests -> '{res.get('detail')}' ({elapsed:.3f}s)")
            rate_limit_hit = True
            break
        elif status == 200:
            print(f"    Request {i}: HTTP 200 OK (Allowed by distributed rate limiter in {elapsed:.3f}s)")
        else:
            print(f"    Request {i}: HTTP {status} ({res})")

    assert rate_limit_hit, "Rate limiter did not throttle requests as expected!"
    print("\n=== All Live Distributed Concepts Verified Successfully on http://127.0.0.1:8000! ===")

if __name__ == "__main__":
    main()
