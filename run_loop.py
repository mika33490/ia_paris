import time
import subprocess

while True:
    print("🚀 Lancement analyse IA...")

    try:
        subprocess.run(["python", "main.py"], check=False)
    except Exception as e:
        print("ERREUR LOOP:", e)

    print("⏳ Prochaine analyse dans 3 heures...")
    time.sleep(3 * 60 * 60)