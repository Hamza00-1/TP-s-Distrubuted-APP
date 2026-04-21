import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ── Stockage en mémoire (simulation d'une base de données) ──
documents_db = {}

# ── Token attendu (en production : JAMAIS en dur !) ──
VALID_TOKEN = "secret-token-abc123"


class APIHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP pour notre mini API."""

    def _send_json(self, status_code, data):
        """Envoie une réponse JSON avec le code de statut donné."""
        self.send_response(status_code)                # Code HTTP (200, 400…)
        self.send_header("Content-Type",
                         "application/json")        # Type MIME
        self.end_headers()                             # Fin des headers
        self.wfile.write(                              # Écriture du body
            json.dumps(data).encode("utf-8")
        )

    def _check_auth(self):
        """Vérifie le header Authorization. Retourne True si valide."""
        auth = self.headers.get("Authorization", "")
        # Format attendu : "Bearer secret-token-abc123"
        if auth != f"Bearer {VALID_TOKEN}":
            self._send_json(401, {
                "error": "unauthorized",
                "message": "Token manquant ou invalide"
            })
            return False
        return True

    # ── GET ────────────────────────────────────────────────────
    def do_GET(self):
        # Endpoint de santé : pas d'auth nécessaire
        if self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "documents_count": len(documents_db)
            })
            return

        # Tout autre GET → 404
        self._send_json(404, {
            "error": "not_found",
            "message": f"Endpoint {self.path} inconnu"
        })

    # ── POST ───────────────────────────────────────────────────
    def do_POST(self):
        if self.path != "/documents":
            self._send_json(404, {
                "error": "not_found",
                "message": f"Endpoint {self.path} inconnu"
            })
            return

        # ① Vérifier l'authentification
        if not self._check_auth():
            return

        # ② Lire et parser le body JSON
        content_length = int(
            self.headers.get("Content-Length", 0)
        )
        if content_length == 0:
            self._send_json(400, {
                "error": "bad_request",
                "message": "Corps de requête vide"
            })
            return

        try:
            raw_body = self.rfile.read(content_length)
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {
                "error": "bad_request",
                "message": "JSON invalide"
            })
            return

        # ③ Validation des champs
        title = body.get("title", "").strip()
        content = body.get("content", "").strip()

        if not title or not content:
            self._send_json(400, {
                "error": "validation_error",
                "message": "'title' et 'content' sont requis"
            })
            return

        if len(title) > 200:
            self._send_json(400, {
                "error": "validation_error",
                "message": "'title' ne doit pas dépasser 200 caractères"
            })
            return

        # ④ Créer le document
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "created_at": datetime.utcnow().isoformat()
        }

        # ⑤ Répondre 201 Created
        self._send_json(201, documents_db[doc_id])

    # Supprimer les logs de requête par défaut (trop verbeux)
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), APIHandler)
    print("Serveur démarré sur http://127.0.0.1:8080")
    server.serve_forever()
