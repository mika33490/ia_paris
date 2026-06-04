import time
import subprocess

while True:
    print("🚀 Lancement analyse FOOT...")

    try:
        subprocess.run(["python", "main.py"], check=False)
    except Exception as e:
        print("ERREUR FOOT:", e)

    print("🎾 Lancement analyse TENNIS...")

    try:
        subprocess.run(["python", "tennis.py"], check=False)
    except Exception as e:
        print("ERREUR TENNIS:", e)

    print("⏳ Prochaine analyse dans 3 heures...")
    time.sleep(3 * 60 * 60)