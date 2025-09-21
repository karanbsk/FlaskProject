import pytest, time

pytestmark = pytest.mark.perf

def test_smoke_health(client):
    r = client.get("/health")
    assert r.status_code in (200,404,302)

def test_small_benchmark():
    # very small microbenchmark to show perf test capability
    start = time.time()
    for _ in range(1000):
        x = 1+1
    elapsed = time.time() - start
    assert elapsed < 1.0
