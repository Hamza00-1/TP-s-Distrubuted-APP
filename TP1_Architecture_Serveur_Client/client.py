#!/usr/bin/env python3
"""
Client API Client (Suite Séance 5 / Séance 6)
Démontre :
- L'authentification (login, bearer token)
- Un mécanisme de Retry avec Backoff Exponentiel et Jitter
- L'utilisation de Idempotency-Key
- Timeout réseau
"""

import json
import time
import uuid
import random
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def request_with_retry(method, path, data=None, token=None, max_retries=3, base_delay=1.0, timeout=5, idempotency_key=None):
    url = f"{BASE_URL}{path}"
    body_bytes = json.dumps(data).encode("utf-8") if data else None

    for attempt in range(max_retries + 1):
        req = urllib.request.Request(url, data=body_bytes, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Request-Id", str(uuid.uuid4()))
        
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        if idempotency_key:
            req.add_header("Idempotency-Key", idempotency_key)

        print(f"\n[Tentative {attempt+1}] {method} {url}")
        
        try:
            response = urllib.request.urlopen(req, timeout=timeout)
            status = response.status
            body = response.read().decode("utf-8")
            print(f"✅ Status {status} Succès")
            return status, json.loads(body) if body else {}
            
        except urllib.error.HTTPError as e:
            error_body = {}
            try:
                error_body = json.loads(e.read().decode("utf-8"))
            except:
                pass
            print(f"❌ Erreur HTTP {e.code}: {error_body}")
            status = e.code
            
            # Ne retenter que pour ces codes (les 400 n'ont pas de retry car non transitoires)
            if status not in [500, 502, 503, 504, 429]:
                return status, error_body
                
            if status == 429: # Rate Limiting (Trop de requêtes)
                print("⏳ Rate limited. Attente forcée de 5s...")
                time.sleep(5)
                continue
                
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"🔌 Erreur réseau ou timeout : {e}")
            status = 0
            
        if attempt == max_retries:
            print(f"💀 Abandon après {max_retries + 1} essais.")
            return status, {}

        # Backoff exponentiel avec Jitter
        delay = min(base_delay * (2 ** attempt), 30.0)
        jittered_delay = random.uniform(0, delay)
        print(f"🔄 Retry programmé dans {jittered_delay:.2f}s...")
        time.sleep(jittered_delay)


if __name__ == "__main__":
    print("=== Démonstration du Client API (Séance 6) ===")

    # 1. Login
    print("\n--- 1. Authentification (Login) ---")
    status, res = request_with_retry("POST", "/api/v1/auth/login", data={"username": "admin", "password": "admin"})
    token = res.get("token")
    if not token:
        print("Échec de la récupération du token.")
        exit(1)

    # 2. Get Documents
    print("\n--- 2. Liste des documents ---")
    request_with_retry("GET", "/api/v1/documents", token=token)

    # 3. Create Document with Idempotency Key (simulate duplication)
    print("\n--- 3. Création document avec Idempotency Key ---")
    ikey = str(uuid.uuid4())
    print("  -> Première requête (Création effective) :")
    request_with_retry("POST", "/api/v1/documents", data={"title": "Nouveau Document"}, token=token, idempotency_key=ikey)
    
    print("\n  -> Seconde requête (Duplication évitée grâce à Idempotency-Key) :")
    request_with_retry("POST", "/api/v1/documents", data={"title": "Nouveau Document"}, token=token, idempotency_key=ikey)

    # 4. Search
    print("\n--- 4. Recherche ---")
    request_with_retry("GET", "/api/v1/search", token=token)
