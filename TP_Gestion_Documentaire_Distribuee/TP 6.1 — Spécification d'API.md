# TP 6.1 — Spécification d'API (contrat)

**Objectif :** Définir le contrat d'API complet pour chaque service du système documentaire.

## Étape 1 : Identifier les endpoints minimum nécessaires pour chaque service
- **Auth :** `/api/v1/auth/login`, `/api/v1/auth/verify`, `/api/v1/auth/logout`
- **Documents :** `/api/v1/documents` (création et liste globale), `/api/v1/documents/{id}` (lecture, mise à jour, suppression d'un élément spécifique)
- **Search :** `/api/v1/search` (effectue une query sur le contenu texte indexable)

## Étape 2 : Définir les détails pour chaque endpoint
Cette étape prend en compte la méthode HTTP associée, l'URL, le payload JSON d'entrée et de sortie attendu, les codes d'erreurs, le support de l'idempotence et les critères de sécurité.

| Endpoint | Méthode | Entrée (JSON) | Sortie (JSON) | Erreurs | Idempotent ? | Sécurité |
| --- | --- | --- | --- | --- | --- | --- |
| `/api/v1/auth/login` | `POST` | `{"username": str, "password": str}` | `{"token": str, "expires_at": str}` | 400 (champs manquants), 401 (credentials invalides), 429 (brute force) | ⚠️ Non (génère un token) | Rate limiting strict, TLS, pas de message « user inexistant » vs « mauvais mdp » |
| `/api/v1/auth/verify` | `GET` | Header: `Authorization: Bearer <token>` | `{"valid": bool, "user_id": str, "roles": [str]}` | 401 (token invalide/expiré) | ✅ Oui | Utilisé par les autres services (inter-service) |
| `/api/v1/auth/logout` | `POST` | Header: `Authorization: Bearer <token>` | `204 No Content` | 401 (token invalide/absent) | ✅ Oui | Blacklist du token (mise en cache Redis pour révocation) |
| `/api/v1/documents` | `POST` | `{"title": str, "content": str, "tags": [str]}` | `{"id": str, "title": str, "created_at": str}` | 400 (validation), 401, 403, 413 (trop gros) | ❌ Non → prévoir `Idempotency-Key` | AuthN + AuthZ (rôle éditeur+), validation stricte, taille max |
| `/api/v1/documents` | `GET` | Query params: `page, per_page, sort, order, tag` | `{"data": [...], "total": int, "page": int, "per_page": int}` | 400 (params invalides), 401 | ✅ Oui | AuthN, pagination forcée (max 100), Rate Limiting contre l'aspiration |
| `/api/v1/documents/{id}` | `GET` | Path param: `id` (UUID) | `{"id": str, "title": str, "content": str, …}` | 401, 403, 404 | ✅ Oui | AuthN + AuthZ (propriétaire ou rôle lecteur) |
| `/api/v1/documents/{id}` | `PUT` | `{"title": str, "content": str, "tags": [str]}` | `{"id": str, "title": str, "updated_at": str}` | 400, 401, 403, 404, 409 (conflit version) | ✅ Oui | AuthN + AuthZ (propriétaire ou éditeur) |
| `/api/v1/documents/{id}` | `DELETE`| Path param: `id` (UUID) | `204 No Content` | 401, 403, 404 | ✅ Oui | AuthN + AuthZ (propriétaire ou admin), audit log |
| `/api/v1/search` | `GET` | Query params: `q, page, per_page, tag, date_from, date_to` | `{"results": [...], "total": int, "page": int}` | 400 (query vide), 401, 429 | ✅ Oui | AuthN, rate limiting (requêtes coûteuses), résultats filtrés par AuthZ |

## Étape 3 : Se demander pour chaque endpoint : est-il idempotent ?
L'idempotence a été notée pour chaque point du tableau de l'étape 2.
- **Oui** pour tous les appels `GET`, `PUT` (remplacement d'un ID en l'état) et `DELETE`.
- **Non** par essence pour les `POST` de documents. S'il n'y a pas pas clé d'idempotence passée par le client, l'effet sera la création d'un document en double. 

## Étape 4 : Prévoir la pagination pour les endpoints de type « liste »
Les requêtes permettant le listage telles que `GET /api/v1/documents` ou `GET /api/v1/search` comporteront de manière par défaut et optionnelle des attributs de pagination: `page` et `per_page`.
Côté serveur, une limite imposée obligatoire garantira de ne pas surcharger la mémoire avec un cas comme max 100 `per_page`.

## Étape 5 : Documenter les headers requis
Chaque aspect de l'API s'attend typiquement à trois headers clefs :
- **Authorization:** Requis sur tous les endpoints non publics, sous la notation `Bearer <token>` pour envoyer le JWT.
- **Content-Type:** Obligatoire en `application/json` pour identifier la nature des bodys en POST et PUT.
- **X-Request-Id:** De configuration avancée, un identifiant (UUID) unique qui est propagé en header pour tracer une demande au travers du Gateway et des différents Micro-Services (idéal pour le débuggage).
