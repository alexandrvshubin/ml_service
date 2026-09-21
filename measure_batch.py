import httpx
import statistics
import time

URL = "http://localhost:8000"
ROW = {"url": "ya.ru", "title": "Сегодня: +14⁠…⁠+20⁠° · переменная облачность, без осадков"}

def measure_single(n=10):
    latencies = []
    for _ in range(n):
        r = httpx.post(f"{URL}/v1/predict", json=ROW)
        latencies.append(r.json()["latency_ms"])
    return statistics.median(latencies)

def measure_batch(n=10, batch_size=500):
    latencies = []
    payload = {"rows": [ROW] * batch_size}
    for _ in range(n):
        r = httpx.post(f"{URL}/v1/predict/batch", json=payload)
        latencies.append(r.json()["total_latency_ms"])
    return statistics.median(latencies)

if __name__ == "__main__":
    time.sleep(3)
    med_single = measure_single()
    med_batch = measure_batch()
    print(f"1:   {med_single} ms")
    print(f"500:  {med_batch} ms")
    print(f"{med_batch / med_single:.2f}x")