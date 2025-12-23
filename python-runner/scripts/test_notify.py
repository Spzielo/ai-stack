import sys
import logging
from core.notifier import notifier

# Configure logging to show info
logging.basicConfig(level=logging.INFO)

print("📨 Sending test notification to Slack...")
success = notifier.info(
    "Brain Connected",
    "Le système de notification Slack est opérationnel ! 🚀\nCeci est un test depuis `python-runner`."
)

if success:
    print("✅ Notification successfully sent!")
    sys.exit(0)
else:
    print("❌ Failed to send notification. Check logs/credentials.")
    sys.exit(1)
