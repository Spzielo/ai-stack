import sys
import logging
import time
from core.notifier import notifier

logging.basicConfig(level=logging.INFO)

print("🧪 Testing Notification Levels...")

# 1. Info (Standard Log)
print("sending INFO...")
notifier.info(
    "Nouvelle Note",
    "J'ai reçu une note de Vincent : 'Penser à acheter du lait'.\nJe l'ai classée dans *Inbox*."
)
time.sleep(1)

# 2. Warning (Attention needed)
print("sending WARNING...")
notifier.warning(
    "Décision Requise",
    "J'hésite sur le classement de cette note.\nEst-ce un *Projet* ou une *Tâche* ?"
)
time.sleep(1)

# 3. Critical (Urgent)
print("sending CRITICAL...")
notifier.critical(
    "Erreur Critique",
    "❌ Impossible de se connecter à n8n !\nLe workflow de classification échoue."
)

print("✅ Done. Check Slack!")
