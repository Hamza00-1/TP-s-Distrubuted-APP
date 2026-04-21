import time
import random
from live_coding_2_client import api_request

def request_with_retry(
    func,                       # fonction appelant l'API
    max_retries=4,              # nombre max de tentatives
    base_delay=1.0,             # délai initial (secondes)
    max_delay=30.0,             # délai maximum (plafond)
    retryable_statuses=(500, 502, 503, 504)
):
    """
    Appelle func() avec retry + backoff exponentiel + jitter.

    func() doit retourner (status_code, response_body).
    On ne retente QUE sur les codes de statut « retryables ».
    Les erreurs 4xx ne sont JAMAIS retentées (sauf 429).
    """

    for attempt in range(max_retries + 1):

        status, body = func()

        # ── Succès → retourner immédiatement ──
        if status is not None and status < 500 \
                and status != 429:
            return status, body

        # ── Rate limited (429) → respecter Retry-After ──
        if status == 429:
            # En production, lire le header Retry-After
            wait = 30.0
            print(f"  ⏳ Rate limited. Attente {wait}s…")
            time.sleep(wait)
            continue

        # ── Dernière tentative atteinte → abandonner ──
        if attempt == max_retries:
            print(f"  💀 Abandon après {max_retries+1} tentatives")
            return status, body

        # ── Calculer le délai de backoff exponentiel ──
        delay = min(base_delay * (2 ** attempt), max_delay)

        # ── Ajouter du jitter (variation aléatoire) ──
        # "Full jitter" : valeur entre 0 et delay
        jittered_delay = random.uniform(0, delay)

        print(
            f"  🔄 Tentative {attempt+1}/{max_retries} "
            f"échouée (status={status}). "
            f"Retry dans {jittered_delay:.1f}s…"
        )
        time.sleep(jittered_delay)

    return status, body

# ── Exemple d'utilisation ──
if __name__ == "__main__":

    # On crée une closure pour passer les paramètres
    def call_health():
        return api_request("GET",
                           "http://127.0.0.1:8080/health",
                           timeout=5)

    status, body = request_with_retry(call_health)
    print(f"Résultat final : {status} → {body}")
