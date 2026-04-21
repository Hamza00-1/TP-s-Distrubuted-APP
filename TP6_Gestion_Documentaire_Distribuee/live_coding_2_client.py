import json
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def api_request(method, url, data=None, token=None, timeout=10):
    """
    Effectue une requête HTTP vers l'API.
    - method  : "GET" ou "POST"
    - url     : URL complète de l'endpoint
    - data    : dict Python (sera converti en JSON)
    - token   : token d'authentification
    - timeout : durée max en secondes (défaut : 10s)
    Retourne : (status_code, response_dict)
    """

    # ── Préparer le body JSON si nécessaire ──
    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")

    # ── Construire la requête ──
    req = Request(url, data=body_bytes, method=method)
    req.add_header("Content-Type", "application/json")

    # ── Ajouter un identifiant unique de requête ──
    # Permet la traçabilité dans les logs du serveur
    request_id = str(uuid.uuid4())
    req.add_header("X-Request-Id", request_id)
    print(f"[{request_id[:8]}] {method} {url}")

    # ── Ajouter le token si fourni ──
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    # ── Envoyer avec timeout ──
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"  ✅ {resp.status}")
            return resp.status, body

    except HTTPError as e:
        # Erreur HTTP (4xx, 5xx) : lire le body d'erreur
        error_body = {}
        try:
            error_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            pass
        print(f"  ❌ HTTP {e.code}: {error_body}")
        return e.code, error_body

    except URLError as e:
        # Erreur réseau (connexion refusée, DNS, timeout…)
        print(f"  🔌 Erreur réseau: {e.reason}")
        return None, {"error": str(e.reason)}

# ── Exemples d'utilisation ──
if __name__ == "__main__":
    BASE = "http://127.0.0.1:8080"
    TOKEN = "secret-token-abc123"

    # GET /health (pas d'auth)
    status, data = api_request("GET", f"{BASE}/health")

    # POST /documents (avec auth + données)
    status, data = api_request(
        "POST",
        f"{BASE}/documents",
        data={"title": "Mon doc", "content": "Contenu…"},
        token=TOKEN,
        timeout=5
    )

    # POST sans auth → doit retourner 401
    status, data = api_request(
        "POST",
        f"{BASE}/documents",
        data={"title": "Test", "content": "X"}
    )
