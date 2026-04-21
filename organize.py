import os
import shutil

# Directories
dir1 = "TP1_Architecture_Serveur_Client"
dir2 = "TP6_Gestion_Documentaire_Distribuee"

os.makedirs(dir1, exist_ok=True)
os.makedirs(dir2, exist_ok=True)

# File mappings
files_to_dir1 = [
    "Server.py",
    "client.py",
    "client_retry.py",
    "client_async.py",
    "cs1.html",
    "ar cs1.html",
    "A.R CS.html",
    "browser_capture.png",
    "Rapport de TP _ Architecture Serveur-Client HTTP.pdf"
]

files_to_dir2 = [
    "main_api.py",
    "live_coding_2_client.py",
    "live_coding_3_retry.py",
    "TP 6.1 — Spécification d'API.md",
    "TP 6.1 — Spécification d'API.pdf",
    "TP 6.2 — Fiabilité côté client.md",
    "TP 6.2 — Fiabilité côté client.pdf",
    "TP 6.3 — Sécurité API.md"
]

for f in files_to_dir1:
    if os.path.exists(f):
        shutil.move(f, os.path.join(dir1, f))

for f in files_to_dir2:
    if os.path.exists(f):
        shutil.move(f, os.path.join(dir2, f))

readme_content = """# Travaux Pratiques - Architectures Distribuées (APP DIS)

Ce dépôt contient l'ensemble des travaux pratiques réalisés pour le module d'Architectures Distribuées.

* **[TP 1 : Architecture Serveur-Client HTTP](./TP1_Architecture_Serveur_Client)** : Mise en place d'une communication client-serveur, gestion des timeouts, backoff exponentiel et appels asynchrones.
* **[TP 6 : Système de Gestion Documentaire Distribué](./TP6_Gestion_Documentaire_Distribuee)** : Création d'une API REST robuste avec spécification OpenAPI, politiques de fiabilité et sécurisation.
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)

print("Files organized successfully!")
