import requests

API_KEY = "342efb42b24391a856705c2c3de698a4"

headers = {
    "x-apisports-key": API_KEY
}

print("🎾 MODULE TENNIS LANCÉ")

try:
    url = "https://v1.tennis.api-sports.io/players?search=Sinner"

    data = requests.get(url, headers=headers).json()

    print(data)

except Exception as e:
    print("ERREUR TENNIS :", e)