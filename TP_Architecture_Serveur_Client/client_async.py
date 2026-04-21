import asyncio
import time

async def appeler_service(nom, latence):
    print(f"  Appel a {nom} (latence prevue : {latence}s)...")
    await asyncio.sleep(latence)
    print(f"  {nom} a repondu !")
    return {"service": nom, "status": "ok"}

async def appels_sequentiels():
    print("\n-- Appels SEQUENTIELS --")
    debut = time.time()
    r1 = await appeler_service("Auth", 0.5)
    r2 = await appeler_service("Stockage", 0.8)
    r3 = await appeler_service("Recherche", 0.3)
    total = time.time() - debut
    print(f"  Temps total sequentiel : {total:.2f}s")

async def appels_paralleles():
    print("\n-- Appels PARALLELES (asyncio.gather) --")
    debut = time.time()
    r1, r2, r3 = await asyncio.gather(
        appeler_service("Auth", 0.5),
        appeler_service("Stockage", 0.8),
        appeler_service("Recherche", 0.3),
    )
    total = time.time() - debut
    print(f"  Temps total parallele : {total:.2f}s")

if __name__ == "__main__":
    asyncio.run(appels_sequentiels())
    asyncio.run(appels_paralleles())
