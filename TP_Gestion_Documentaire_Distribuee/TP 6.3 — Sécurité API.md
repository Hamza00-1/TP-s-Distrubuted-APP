# TP 6.3 — Sécurité API : modèle minimal

**Objectif :** Définir les premières mesures de sécurité pour l'API du système documentaire.

## Étape 1 : Définir un mécanisme simple de token
- **Génération :** La méthode préconisée est le *JWT (JSON Web Token)*, instancié et signé de manière asymétrique ou symétrique exclusive par le module central `Auth Service`. Il lui est fixé une durée de vie très courte (15 à 60 minutes). Il peut être associé à un Refresh Token plus long sécurisé par cookie `HttpOnly`.
- **Transmission :** En clair via l'entête HTTP (Authorization): `Authorization: Bearer <TOKEN>`. Ne devra en aucun cas être joint en Query params de l'URL pour ne pas laisser de traces en proxy tiers.
- **Vérification :** Directe sans requête réseau. Tous les sous-services (Documents, Search) utilisant le JWT valide son identité avec la clé secrète asymétrique publique partagée entre microservices, lisant le payload sans engorger le flux principal d'Auth.
- **Invalidation :** Bien qu'un JWT ai sa propre date d'expiration, les procédures de "logout" insèrent les identifiants en File active (Redis) qui sera une "Denylist" pour le Gateway avant tout routage.

## Étape 2 : Identifier où placer les contrôles de sécurité
- **Validation d'entrée :** Une vérification superficielle de structure et du type s'en tient à la charge du *Gateway*. La validation forte du typage, des plages et des longueurs (comme les contraintes du projet) demeure la stricte responsabilité du *Service Métier impliqué (Document)*.
- **Rate limiting :** Opéré via des compteurs de seuils à la *API Gateway*. La souplesse viendra par IP: Modéré pour le Search, et critique pour l'Auth (contre le Brute Force).
- **Audit logs :** Sur le service *Auth* particulièrement, afin de tracer l'empreinte de tentatives de compromission et succès des accès, puis en second niveau sur le *Service Document* concernant tous les changements (CRUD ou Suppression d'admin) en incluant UUID, Timestamps et l'IP de requêtes.

## Étape 3 & 4 : Cartographier les surfaces d'exposition et déterminer contrôles et menaces
Liste croisée et analyse pour trois espaces ciblés : L'API publique cliente, le flux inter-services et le pan pour les points de données Administratrices.

| Surface (Exposition) | Menace principale (Type d'Attaque) | Contrôle proposé | Priorité |
| --- | --- | --- | --- |
| API publique — `/auth/login` | Brute force sur credentials / Credential Stuffing | Rate limiting (5 tentatives/min/IP), verrouillage progressif de compte, logs explicites sans renvoyer d'erreurs différenciées. | 🔴 Critique |
| API publique — `/documents` (POST/PUT) | Injection JSON (XSS, NoSQL), upload malveillant. | Validation stricte, taille max fixée, whitelist des propriétés d'entrée (`Content-Type` vérifié). | 🔴 Critique |
| API publique — `/documents` (GET) | Scraping massif / Enumerate IDs des documents d'autres utilisateurs / BOLA, IDOR | Authentification, AuthZ forte (vérifie si la personne a accès au document UUID). Pagination obligatoire pour les listes et Rate limiting global. IDs sous format non devinable (UUIDv4). | 🔴 Critique |
| API publique — `/search` | DDoS applicatif (saturation des workers DB / RegexDoS) par requêtes très coûteuses ou infinies. | Rate limiting en Gateway, pagination obligatoire empêchant `per_page=999999`, timeout de la requête base de données pour stopper les strings trop lourds. | 🟠 Élevée |
| API publique — Tous endpoints | Attaques de type MITM, interception de tokens en clair sur réseau. | Chiffrement TLS / HTTPS obligatoire de bout en bout, HSTS, Secure Headers. | 🔴 Critique |
| Inter-services — `auth <-> documents <-> search` | Mouvement latéral, demande interne malveillante, ou usurpation de service par accès "réseau privé / trusted network". | Imposer le principe de "Zéro Confiance" même en réseau interne : communications en **mTLS**, vérification d'un Token Service ou propagation du JWT Client initial avec sa validité. | 🟠 Élevée |
| Inter-services — Tous | Replay de requêtes internes (reflétant une tentative d'exploitation retardée d'une communication interceptée). | Mise en place de Nonces, timestamps sur l'entête interne et un petit temps limité à sa validité. | 🟡 Moyenne |
| Admin — gestion utilisateurs | Accès non autorisé, élévation illicite de privilèges (E). | Contrôle AuthZ strict (RBAC pour rôle Admin), vérifier un second facteur (MFA), masquer d'Internet si possible (VPN). Audit log très riche de modifications. | 🔴 Critique |
| Admin — endpoints de stats / debug | Fuite d'informations sensibles sur la structure du backend, version des bases. | Suppression et non-transposition de l'accès à ces endpoints dans le paramétrage du routage de l'API publique en PROD. | 🟠 Élevée |
| Tous endpoints — `/auth/logout` | Token non invalidé et récupérable depuis l'ordinateur de la cible. Séjour étendu d'accès. | Invalidation du Token immédiate par insertion de son ID JWT dans un "Blacklist Cache Redis" révoquant instantanément. | 🔴 Critique |
