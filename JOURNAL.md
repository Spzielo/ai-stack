# Journal de Bord

Ce document trace les réflexions, les impasses et les leçons apprises tout au long du projet.

## 2025-12-23 : Durcissement de l'Infrastructure

### 💡 Leçon : La gestion des dépendances
Nous avons initialement utilisé `pip install` dans le Dockerfile. Bien que fonctionnel, cela manquait de reproductibilité.
**Décision** : Passage immédiat à **Poetry**. C'est un coût initial (temps de build un peu plus long, complexité Dockerfile) mais cela garantit que la Prod est *identique* au Dev.

### ↩️ Pivot : Notifications
Nous avons exploré **Pushover** pour les notifications mobiles.
**Problème** : Trop limité pour une gestion de logs structurée (bruit vs signal).
**Pivot** : Revenir en arrière (suppression complète du code Pushover) et implémenter **Slack**.
**Gain** : Slack permet de créer des canaux séparés (`#log` vs `#alert`), ce qui est crucial pour ne pas "noyer" l'utilisateur sous les infos techniques.

---

## 2025-12-22 : Problèmes de Frontend (Icônes)

### 🐛 Bug : L'icône fantôme sur iOS
Sur iOS, ajouter n8n à l'écran d'accueil affichait un carré blanc ou un "N" par défaut, malgré nos hacks HTML.
**Solution trouvée** : iOS/Safari est très capricieux sur le cache et la découverte d'icônes.
**Fix** :
1.  Utiliser un nom de fichier standard (`apple-touch-icon.png`).
2.  Ne PAS ajouter de balises HTML manuelles (laisser Safari découvrir implicitement).
3.  Utiliser une icône *solide* (pas de transparence).

---

## 2025-12-22 : Architecture API

### 🚀 Migration Flask -> FastAPI
On a démarré en Flask par habitude. Mais Flask est synchrone (bloquant).
Pour un "Cerveau" qui devra traiter des requêtes IA potentiellement longues, bloquer le thread principal est dangereux.
**Action** : Réécriture complète en **FastAPI** (ASGI/Async).
**Résultat** : Plus moderne, validation automatique via Pydantic, et prêt pour l'avenir.
