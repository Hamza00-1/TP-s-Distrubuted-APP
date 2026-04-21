#!/usr/bin/env python3
"""
Serveur API complet (Suite Séance 5 / Séance 6)
Implémente :
- AuthN (Login, Verify, Logout) avec des tokens mockés
- CRUD Documents complet (/api/v1/documents)
- Recherche basique (/api/v1/search)
- Gestion des Idempotency-Key pour les POST
"""

import json
import time
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# ── Base de "documents" en mémoire (simule une DB) ──
DOCUMENTS_DB = {
    "1": {"id": "1", "title": "Rapport Q3", "content": "Contenu du rapport", "created_at": datetime.utcnow().isoformat()},
    "2": {"id": "2", "title": "Plan stratégique", "content": "Contenu du plan", "created_at": datetime.utcnow().isoformat()}
}

TOKENS = set()  # Tokens actifs
DENYLIST = set() # Tokens révoqués (Logout)
IDEMPOTENCY_KEYS = {} # Stockage temporaire des réponses POST pour éviter la duplication

class APIHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _check_auth(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._send_json(401, {"error": "unauthorized", "message": "Token manquant"})
            return False
        token = auth.split(" ")[1]
        if token not in TOKENS or token in DENYLIST:
            self._send_json(401, {"error": "unauthorized", "message": "Token invalide ou expiré"})
            return False
        return True
        
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Endpoint Verify Token
        if path == "/api/v1/auth/verify":
            if self._check_auth():
                self._send_json(200, {"valid": True, "user_id": "admin", "roles": ["admin"]})
            return
            
        # Endpoints Documents
        if path.startswith("/api/v1/documents"):
            if not self._check_auth(): return
            
            parts = [p for p in path.split("/") if p]
            if len(parts) == 3: # /api/v1/documents (Lister)
                self._send_json(200, {"data": list(DOCUMENTS_DB.values()), "total": len(DOCUMENTS_DB)})
            elif len(parts) == 4: # /api/v1/documents/{id}
                doc_id = parts[3]
                if doc_id in DOCUMENTS_DB:
                    self._send_json(200, DOCUMENTS_DB[doc_id])
                else:
                    self._send_json(404, {"error": "not_found", "message": "Document non trouvé"})
            return
            
        # Endpoint Search
        if path.startswith("/api/v1/search"):
            if not self._check_auth(): return
            self._send_json(200, {"results": list(DOCUMENTS_DB.values()), "total": len(DOCUMENTS_DB)})
            return

        self._send_json(404, {"error": "not_found", "message": "Route inconnue"})

    def do_POST(self):
        path = self.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        
        try:
            data = json.loads(body)
        except:
            self._send_json(400, {"error": "bad_request", "message": "JSON invalide"})
            return

        # Login
        if path == "/api/v1/auth/login":
            if data.get("username") == "admin" and data.get("password") == "admin":
                token = str(uuid.uuid4())
                TOKENS.add(token)
                self._send_json(200, {"token": token, "expires_at": ""})
            else:
                self._send_json(401, {"error": "unauthorized", "message": "Identifiants invalides"})
            return
            
        # Logout
        if path == "/api/v1/auth/logout":
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth.split(" ")[1]
                DENYLIST.add(token)
            self._send_json(204, {})
            return
            
        # Création de document
        if path == "/api/v1/documents":
            if not self._check_auth(): return
            
            # Gestion de la duplication via Idempotency-Key
            idempotency_key = self.headers.get("Idempotency-Key")
            if idempotency_key and idempotency_key in IDEMPOTENCY_KEYS:
                print(f"♻️  Clé d'idempotence détectée : Retour des données en cache.")
                self._send_json(201, IDEMPOTENCY_KEYS[idempotency_key])
                return

            title = data.get("title", "").strip()
            if not title:
                self._send_json(400, {"error": "bad_request", "message": "Title requis"})
                return
                
            doc_id = str(uuid.uuid4())
            doc = {
                "id": doc_id,
                "title": title,
                "content": data.get("content", ""),
                "created_at": datetime.utcnow().isoformat()
            }
            DOCUMENTS_DB[doc_id] = doc
            
            # Enregistrement pour idempotence future
            if idempotency_key:
                IDEMPOTENCY_KEYS[idempotency_key] = doc
                
            self._send_json(201, doc)
            return

        self._send_json(404, {"error": "not_found", "message": "Route inconnue"})

    def do_PUT(self):
        path = self.path
        if path.startswith("/api/v1/documents/"):
            if not self._check_auth(): return
            parts = [p for p in path.split("/") if p]
            if len(parts) == 4:
                doc_id = parts[3]
                if doc_id not in DOCUMENTS_DB:
                    self._send_json(404, {"error": "not_found", "message": "Document non trouvé"})
                    return
                
                content_length = int(self.headers.get('Content-Length', 0))
                try:
                    data = json.loads(self.rfile.read(content_length))
                except:
                    self._send_json(400, {"error": "bad_request", "message": "JSON invalide"})
                    return
                    
                DOCUMENTS_DB[doc_id].update({
                    "title": data.get("title", DOCUMENTS_DB[doc_id]["title"]),
                    "content": data.get("content", DOCUMENTS_DB[doc_id]["content"]),
                    "updated_at": datetime.utcnow().isoformat()
                })
                self._send_json(200, DOCUMENTS_DB[doc_id])
                return
        self._send_json(404, {"error": "not_found", "message": "Route inconnue"})

    def do_DELETE(self):
        path = self.path
        if path.startswith("/api/v1/documents/"):
            if not self._check_auth(): return
            parts = [p for p in path.split("/") if p]
            if len(parts) == 4:
                doc_id = parts[3]
                if doc_id in DOCUMENTS_DB:
                    del DOCUMENTS_DB[doc_id]
                    self._send_json(204, {})
                else:
                    self._send_json(404, {"error": "not_found", "message": "Document non trouvé"})
                return
        self._send_json(404, {"error": "not_found", "message": "Route inconnue"})


if __name__ == "__main__":
    serveur = HTTPServer(("127.0.0.1", 8000), APIHandler)
    print("Serveur API (Séance 5/6) démarré sur http://127.0.0.1:8000")
    serveur.serve_forever()
