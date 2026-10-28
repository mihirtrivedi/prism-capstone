"""Automated test runner that spins up mock providers and Prism gateway,
runs smoke_test.py and load_test.py, and tears down all services.
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def wait_for_url(url, proc, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print(f"Process for {url} exited prematurely with code {proc.returncode}!")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            # print first error
            if time.time() - start > 10:
                print(f"Error connecting to {url}: {type(e).__name__}: {e}")
        time.sleep(0.5)
    return False


def main():
    print("=" * 60)
    print("Starting Prism Verification Test Suite")
    print("=" * 60)

    # 1. Start Mock Provider Alpha (port 9001)
    print("Launching Mock Provider Alpha on port 9001 ...")
    alpha_proc = subprocess.Popen([
        PYTHON, str(ROOT / "scripts" / "mock_provider.py"),
        "--port", "9001", "--name", "alpha"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 2. Start Mock Provider Beta (port 9002)
    print("Launching Mock Provider Beta on port 9002 ...")
    beta_proc = subprocess.Popen([
        PYTHON, str(ROOT / "scripts" / "mock_provider.py"),
        "--port", "9002", "--name", "beta"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 3. Start Prism Gateway (port 8080)
    print("Launching Prism Gateway on port 8080 ...")
    gateway_proc = subprocess.Popen([
        PYTHON, str(ROOT / "main.py"),
        "--port", "8080"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        # Wait for all 3 to respond
        print("Waiting for servers to become ready ...")
        if not wait_for_url("http://127.0.0.1:9001/health", alpha_proc):
            raise RuntimeError("Provider Alpha failed to start on 9001")
        if not wait_for_url("http://127.0.0.1:9002/health", beta_proc):
            raise RuntimeError("Provider Beta failed to start on 9002")
        if not wait_for_url("http://127.0.0.1:8080/health", gateway_proc):
            raise RuntimeError("Prism Gateway failed to start on 8080")
        print("All 3 servers are healthy!\n")

        # 4. Run Smoke Test
        print("-" * 60)
        print("RUNNING SMOKE TEST (smoke_test.py):")
        print("-" * 60)
        smoke_res = subprocess.run([
            PYTHON, str(ROOT / "scripts" / "smoke_test.py"),
            "--url", "http://127.0.0.1:8080",
            "--key", "prism-sk-search-1a2b3c",
            "--model", "fast"
        ], capture_output=True, text=True)

        print(smoke_res.stdout)
        if smoke_res.stderr:
            print("STDERR:", smoke_res.stderr)

        # 5. Run Load Test
        print("-" * 60)
        print("RUNNING LOAD TEST (load_test.py):")
        print("-" * 60)
        load_res = subprocess.run([
            PYTHON, str(ROOT / "scripts" / "load_test.py"),
            "--url", "http://127.0.0.1:8080",
            "--key", "prism-sk-free-7g8h9i",
            "--model", "fast",
            "--requests", "30",
            "--concurrency", "10",
            "--rpm-limit", "10"
        ], capture_output=True, text=True)

        # Note: if free-tier key name in seed_keys is 'prism-sk-free-7g8h9i', check that:
        if "unknown virtual" in load_res.stdout.lower() or "rejected" in load_res.stdout.lower() and "401" in load_res.stdout:
            # retry with exact key
            load_res = subprocess.run([
                PYTHON, str(ROOT / "scripts" / "load_test.py"),
                "--url", "http://127.0.0.1:8080",
                "--key", "prism-sk-free-7g8h9i",
                "--model", "fast",
                "--requests", "30",
                "--concurrency", "10",
                "--rpm-limit", "10"
            ], capture_output=True, text=True)

        print(load_res.stdout)
        if load_res.stderr:
            print("STDERR:", load_res.stderr)

    finally:
        print("\nShutting down servers ...")
        gateway_proc.terminate()
        alpha_proc.terminate()
        beta_proc.terminate()
        gateway_proc.wait()
        alpha_proc.wait()
        beta_proc.wait()
        print("All servers stopped cleanly.")


if __name__ == "__main__":
    main()
