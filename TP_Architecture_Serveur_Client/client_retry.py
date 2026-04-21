import json
import time
import random
import urllib.request
import urllib.error

def fetch_with_retry(url, max_retries=4, base_delay=0.5, timeout=1.5):
    for tentative in range(max_retries):
        try:
            print(f"  Tentative {tentative + 1}/{max_retries}...")
            response = urllib.request.urlopen(url, timeout=timeout)
            data = json.loads(response.read().decode("utf-8"))
            print(f"  Succes a la tentative {tentative + 1}")
            return data
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  Echec : {e}")
            if tentative < max_retries - 1:
                delay = base_delay * (2 ** tentative)
                jitter = random.uniform(0, delay * 0.3)
                wait = delay + jitter
                print(f"  Attente {wait:.2f}s avant retry...")
                time.sleep(wait)
            else:
                print(f"  Toutes les tentatives echouees.")
                return None

if __name__ == "__main__":
    print("Appel avec retry + backoff exponentiel :")
    result = fetch_with_retry("http://127.0.0.1:8000/documents/2")
    if result:
        print(f"\nDocument recupere : {result}")
    else:
        print("\nImpossible de joindre le service.")
