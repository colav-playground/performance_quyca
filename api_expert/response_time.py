import time, requests, csv, os

from build_url import expand_endpoints

def measure_response_time(url: str, repetitions: int = 3):
    """Mide el tiempo de respuesta promedio de un endpoint"""
    times = []
    for i in range(repetitions):
        try:
            start = time.perf_counter()
            response = requests.get(url, timeout=30)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            print(f"[{i+1}/{repetitions}] {url} -> {elapsed:.3f}s (status {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"Error con {url}: {e}")
    if times:
        return sum(times) / len(times)
    return None

if __name__ == "__main__":
    urls = expand_endpoints()
    results = []

    for endpoint in urls:
        average_time = measure_response_time(endpoint)
        if average_time is not None:
            results.append({"url": endpoint, "average_time": average_time})

    # Guardamos en CSV
    file_exists = os.path.isfile("api_response_times.csv")
    with open("api_response_times.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "average_time"])
        if not file_exists:
            writer.writeheader()
        writer.writerows([{"url": r["url"], "average_time": f"{r['average_time']:.3f}"} for r in results])

    print("\n======== Resumen =======\n")
    for r in results:
        print(f"{r['url']} -> {r['average_time']:.3f}s promedio")