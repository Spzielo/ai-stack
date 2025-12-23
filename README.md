# 🧠 AI Cloud Stack

Bienvenue dans ton "Deuxième Cerveau". Voici ton manuel de pilotage.

## 🎮 Commandes Magiques (Cheat Sheet)

Utilise ces commandes pour piloter ton stack sans effort.

| Commande | Action | Description |
| :--- | :--- | :--- |
| **`make dev`** | 👨‍💻 **Travailler** | Lance le mode **Développement** (Hot Reload). Modifie le code, il change direct. |
| **`make prod`** | 🚀 **Déployer** | Lance le mode **Production**. Stable, redémarrage auto, optimisé. |
| **`make logs`** | 👀 **Surveiller** | Affiche les logs de tous les services en temps réel. (`Ctrl+C` pour quitter) |
| **`make backup`** | 💾 **Sauver** | Sauvegarde la base `brain` en local (`./backups`) ET sur GitHub. |
| **`make down`** | 🛑 **Arrêter** | Arrête proprement tous les services. |

**(Pour restaurer une sauvegarde : `make restore file=backups/mon_fichier.sql`)**

---

## 🏗️ Architecture

Tes services tournent sur ces ports :

| Service | Port Local | URL |
| :--- | :--- | :--- |
| **n8n** | `5678` | [http://localhost:5678](http://localhost:5678) |
| **Open WebUI** | `3000` | [http://localhost:3000](http://localhost:3000) |
| **Python Brain** | `8000` | [http://localhost:8000](http://localhost:8000) (API) |
| **Postgres** | `5432` | `localhost:5432` (Accès DB) |
| **Qdrant** | `6333` | `localhost:6333` (Vecteurs) |

---

## 📁 Organisation des Fichiers

- `python-runner/` : Ton code Python (FastAPI).
- `n8n-custom/` : Configuration personnalisée de n8n (Icône, etc).
- `scripts/` : Les scripts shell (backup, restore, switch env).
- `backups/` : Tes fichiers `.sql` de sauvegarde.
- `Makefile` : Le fichier qui contient les raccourcis magiques.

## 🛡️ Sécurité & accès

- **Tailscale** : Accès à distance via `100.x.x.x` (pas de ports ouverts sur Internet public).
- **Secrets** : Tout est dans `.env` (jamais sur Git).

## 📦 Gestion des Dépendances (Poetry)

Le projet utilise **Poetry** pour gérer les librairies Python de manière robuste.
*   `pyproject.toml` : Liste des dépendances.
*   `poetry.lock` : Versions exactes verrouillées.

**Ajouter une librairie :**
```bash
docker exec python-runner poetry add <nom_librairie>
# Exemple
docker exec python-runner poetry add pandas
```
(Le fichier `pyproject.toml` et `poetry.lock` seront mis à jour automatiquement sur ton mac).

## 📢 Notifications (Slack)

Ton "Cerveau" te parle via Slack.

- **`#cerveau-log`** : Journal de bord (ℹ️ infos, 🪵 logs).
- **`#cerveau-alert`** : Urgences (⚠️ attention requise, 🚨 erreurs critiques).

Configuration requise dans `.env` :
```env
SLACK_WEBHOOK_LOG="https://hooks.slack.com/..."
SLACK_WEBHOOK_ALERT="https://hooks.slack.com/..."
```
