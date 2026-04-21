# TP 6.2 — Fiabilité côté client (scénarios)

**Objectif :** Définir les politiques de fiabilité pour le client du système documentaire et analyser trois scénarios de panne.

## Étape 1 : Pour chaque service appelé, proposer les caractéristiques de fiabilité  
*(Timeout, Nombre max de retries, Backoff delay associé et les clés d'idempotence)*

| Service | Timeout | Max retries | Base delay | Codes retryables | Idempotency key ? |
| --- | --- | --- | --- | --- | --- |
| Auth (login) | 5s | 1 | 1s | 502, 503, 504 | Non (pas de side effect critique) |
| Auth (verify/logout) | 3s | 2 | 0.5s | 502, 503, 504 | Non (GET idempotent pour verify, POST logout idempotent) |
| Documents (GET) | 10s | 2 | 1s | 500, 502, 503, 504 | Non (lecture) |
| Documents (POST) | 15s | 0 (pas auto) | — | — | **Oui** (UUID côté client) |
| Search (query) | 8s | 2 | 1s | 502, 503 | Non (lecture) |

## Étape 2 & 3 : Analyser les scénarios de panne
Tableau d'évaluation listant les risques, les correctifs et les explications en milieu distribué.

| Scénario | Risque principal | Politique appliquée | Justification |
| --- | --- | --- | --- |
| **S1 — Latence élevée** (Le Document Service répond en 8 à 15 secondes au lieu des 200ms habituelles. La BD est surchargée.) | Bloquer les threads (famine de ressources) côté Gateway et client final, entraînant un effet cascade (crash global). Très mauvaise UX. | Timeout strict (ex: 8s ou 10s max) couplé à un **Circuit Breaker** qui s'ouvre pour protéger la BDD. Utilisation d'un **Fallback** (ex: récupérer des lectures d'un cache local dégradé). | Mettre un Timeout libère les ressources côté client et Gateway. Ouvrir le Circuit Breaker permet à la base de données de "respirer" et récupérer au lieu d'empirer sa lenteur sous un avalanche de requêtes en attente. |
| **S2 — Serveur intermittent** (Le Search Service retourne des erreurs 503 une requête sur trois à cause d'un rolling update.) | Perte inutile de requêtes de recherche depuis l'expérience utilisateur et instabilité perçue, alors qu'une bonne structure existe la majorité du temps. | **Retry avec backoff exponentiel et jitter** : Max 2 retries, délai initial court (ex: 500ms). | L'erreur `503` (Service Unavailable) dans un cas de rolling update est purement transitoire. Ajouter un Retry avec jitter sur cette requête idempotente (GET) permet à l'appel suivant de tomber sur une instance "healthy" de façon fluide, sans risquer de Retry Storm. |
| **S3 — Duplication de requêtes** (Réseau lent, clic double, deux requêtes POST non répondues en parallèle.) | Création de deux documents identiques et facturation/traitement dupliqué en base de données. L'état devient corrompu/incohérent. | **Ne pas réessayer automatiquement** les opérations POST. Utiliser et imposer une **Idempotency-Key** générée par le Web Client au clic via UUID. | Un POST n'est pas idempotent. En associant une `Idempotency-Key` dans les headers de la requête, le premier traitement sera enregistré. Si le client envoie une duplication stricte avec la même clé, le backend renvoie le résultat du premier traitement (200/201) au lieu de créer à nouveau le record, garantissant qu'un et un seul document est généré. |

## Étape 4 : Identifier les situations où un fallback est possible
Outre les mécanismes mis en évidence :
- **Scénario d'indisponibilité Data (S1) :** Si la lecture du Document `123` via `/documents/123/` ne répond plus car Service Down, la configuration peut fournir un File de cache locale si consultable (Cache TTL expiré par exemple avec mention dégradée).
- **Scénario d'indisponibilité du Search Service (S2 exceptionnel) :** Un "fallback" peut consister à rediriger l'utilisateur à naviguer par tags de liste `/documents` de manière standard s'il tente une recherche indisponible.
