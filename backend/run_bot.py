import sys
from pathlib import Path

# Add app directory to path
backend_path = Path(__file__).resolve().parent
sys.path.append(str(backend_path))

from app.agents.telegram_bot import run_polling_bot

if __name__ == "__main__":
    try:
        run_polling_bot()
    except KeyboardInterrupt:
        print("\nStopping bot. Goodbye!")
