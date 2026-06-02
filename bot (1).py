import requests
import json
import re
import os
import time
from datetime import datetime

# ============================================================
#  CONFIGURATION
# ============================================================

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1511461083561594941/RQpYRQvqscrebnF5Ew6N4QNGUnviyOXR28X9hRvvuRFRvHkBqQxkBxEFzo255ATtd9W0"

COMPTES_THREADS = [
    "seb_nonda",
    "footmercato",
    "actufoot_",
    "massiliazone",
    "laminuteom_",
    "fabriziorom",
    "laprovence",
    "lequipe",
    "diariosport",
    "espoirsdufootball",
]

MOTS_CLES = ["OM", "Marseille", "om", "Om", "l'OM", "les marseillais", "marseillais", "olympique de marseille"]

FICHIER_MEMOIRE = "posts_deja_envoyes.json"

# ============================================================
#  MEMOIRE
# ============================================================

def charger_memoire():
    if os.path.exists(FICHIER_MEMOIRE):
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return []

def sauvegarder_memoire(ids):
    ids_recents = ids[-500:]
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(ids_recents, f)

# ============================================================
#  SCRAPING THREADS
# ============================================================

def get_posts_threads(username):
    url = f"https://www.threads.net/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[ERREUR] {username} — HTTP {response.status_code}")
            return []

        html = response.text
        posts = []

        pattern_alt = r'"caption":\{"text":"([^"]{10,})"'
        textes = re.findall(pattern_alt, html)

        for texte in textes[:5]:
            texte_decode = texte.encode().decode('unicode_escape') if '\\u' in texte else texte
            post_id = f"{username}_{hash(texte_decode) % 10**10}"
            posts.append({
                "id": post_id,
                "username": username,
                "texte": texte_decode,
                "url": f"https://www.threads.net/@{username}"
            })

        return posts

    except Exception as e:
        print(f"[ERREUR] Impossible de lire @{username} : {e}")
        return []

# ============================================================
#  FILTRE MOTS CLÉS
# ============================================================

def contient_mot_cle(texte):
    texte_lower = texte.lower()
    for mot in MOTS_CLES:
        if mot.lower() in texte_lower:
            return True
    return False

# ============================================================
#  ENVOI DISCORD
# ============================================================

def envoyer_discord(post):
    heure = datetime.now().strftime("%H:%M")
    message = {
        "embeds": [{
            "color": 0x009CDE,
            "author": {
                "name": f"@{post['username']} sur Threads",
                "url": post['url'],
            },
            "description": post['texte'][:500] + ("..." if len(post['texte']) > 500 else ""),
            "footer": {
                "text": f"🔵⚪ Alerte OM • {heure}"
            },
            "url": post['url']
        }]
    }

    try:
        r = requests.post(DISCORD_WEBHOOK, json=message, timeout=10)
        if r.status_code == 204:
            print(f"[✅] Envoyé dans Discord : @{post['username']}")
        else:
            print(f"[ERREUR Discord] Status {r.status_code}")
    except Exception as e:
        print(f"[ERREUR Discord] {e}")

# ============================================================
#  EXECUTION UNIQUE (GitHub Actions relance toutes les 15 min)
# ============================================================

print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] 🔵⚪ Vérification OM en cours...")

posts_envoyes = charger_memoire()

for username in COMPTES_THREADS:
    print(f"  → Lecture de @{username}...")
    posts = get_posts_threads(username)

    for post in posts:
        if post["id"] in posts_envoyes:
            continue
        if contient_mot_cle(post["texte"]):
            print(f"  🔵 TROUVÉ : {post['texte'][:80]}...")
            envoyer_discord(post)
            posts_envoyes.append(post["id"])
            time.sleep(1)

    time.sleep(3)

sauvegarder_memoire(posts_envoyes)
print("[✅] Vérification terminée.")
