import time
import os
print("SCRIPT LANCÉ")
import joblib
import pandas as pd
import requests
from datetime import datetime

# =============================
# LOAD MODEL
# =============================
model = joblib.load("ml/model.pkl")

API_KEY = "342efb42b24391a856705c2c3de698a4"
BANKROLL = 100

# =============================
# TELEGRAM
# =============================
def envoyer_telegram(message):
    token = "8669660996:AAHQ4QSBPsgLCdtcmyqS2kolpfILbnpZS1M"
    chat_id = "1756104923"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    r = requests.post(url, data={
        "chat_id": chat_id,
        "text": message
    })


# =============================
# CONFIG
# =============================
LEAGUES_AUTORISEES = [

    # EUROPE TOP 5
    39,   # Premier League
    140,  # Liga
    135,  # Serie A
    78,   # Bundesliga
    61,   # Ligue 1

    # AUTRES GROSSES LIGUES
    88,   # Eredivisie
    94,   # Portugal
    203,  # Turquie
    119,  # Danemark
    113,  # Suède
    106,  # Norvège
    179,  # Ecosse

    # COMPÉTITIONS UEFA
    2,    # Champions League
    3,    # Europa League
    848,   # Conference League

    # COMPÉTITIONS INTERNATIONALES
    1,    # Coupe du Monde FIFA
    4,    # Euro Championship
    5,    # UEFA Nations League
    29,   # Qualif Coupe du Monde Afrique
]

headers = {"x-apisports-key": API_KEY}

# =============================
# KELLY
# =============================
def kelly(p, cote):
    b = cote - 1
    q = 1 - p
    k = (b * p - q) / b
    return max(0, min(k, 0.05))

def mise(proba, cote):
    return round(BANKROLL * kelly(proba/100, cote), 2)

def calcul_score(proba, ev, diff, xg_home, xg_away):

    score = 0

    score += proba * 0.4
    score += ev * 100 * 0.3
    score += diff * 2
    score += xg_home * 10
    score -= xg_away * 5

    return round(max(0, min(score, 100)), 1)
# =============================
# API
# =============================
today = datetime.today().strftime("%Y-%m-%d")

fixtures = requests.get(
    f"https://v3.football.api-sports.io/fixtures?date={today}",
    headers=headers
).json()


print("NB MATCHS:", len(fixtures.get("response", [])))
print("RESULTATS API :", fixtures.get("results"))
print("ERREURS API :", fixtures.get("errors"))
print(fixtures)

odds = requests.get(
    f"https://v3.football.api-sports.io/odds?date={today}",
    headers=headers
).json()

# =============================
# UTILS
# =============================
def get_stats(team_id, league_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&league={league_id}&season=2024"
    return requests.get(url, headers=headers).json().get("response", {})

def get_odds(match_id, bet_name, label):
    try:
        for m in odds["response"]:
            if m["fixture"]["id"] == match_id:
                for b in m["bookmakers"]:
                    for bet in b["bets"]:
                        if bet["name"] == bet_name:
                            for val in bet["values"]:
                                if val["value"] == label:
                                    return float(val["odd"])
    except:
        return None

def analyser_over_btts(match_id, home, away, total_xg, xg_home, xg_away):

    # OVER 2.5
    cote_over = get_odds(match_id, "Goals Over/Under", "Over 2.5")

    if cote_over:

        proba_over = min(95, total_xg * 30)

        ev_over = ((proba_over / 100) * cote_over) - 1

        print("OVER 2.5")
        print("PROBA =", round(proba_over, 1))
        print("COTE =", cote_over)
        print("EV =", round(ev_over, 3))

        if ev_over > 0.25 and proba_over >= 75:

            niveau = "🔥 ULTRA SAFE"

        elif ev_over > 0.15:

            niveau = "🟢 SAFE"

        else:

            niveau = "🟡 VALUE"
        
        score_ia = calcul_score(
            proba_over,
            ev_over,
            total_xg,
            xg_home,
            xg_away
        )
        
        if ev_over > 0.08:

            safe_results.append({
                "niveau": niveau,
                "note": note_ia,
                "score": score_ia,
                "match": f"{home} vs {away}",
                "pari": "Over 2.5",
                "proba": round(proba_over, 1),
                "cote": round(cote_over, 2),
                "ev": round(ev_over, 3)
            })

    # BTTS
    cote_btts = get_odds(match_id, "Both Teams Score", "Yes")

    if cote_btts:

        proba_btts = min(95, (xg_home + xg_away) * 25)

        ev_btts = ((proba_btts / 100) * cote_btts) - 1

        print("BTTS")
        print("PROBA =", round(proba_btts, 1))
        print("COTE =", cote_btts)
        print("EV =", round(ev_btts, 3))
        
        if ev_btts > 0.25 and proba_btts >= 75:

            niveau = "🔥 ULTRA SAFE"

        elif ev_btts > 0.15:

            niveau = "🟢 SAFE"

        else:

            niveau = "🟡 VALUE"

        score_ia = calcul_score(
            proba_btts,
            ev_btts,
            total_xg,
            xg_home,
            xg_away
        )

        if ev_btts > 0.08:

            safe_results.append({
                "niveau": niveau,
                "note": note_ia,
                "score": score_ia,
                "match": f"{home} vs {away}",
                "pari": "BTTS OUI",
                "proba": round(proba_btts, 1),
                "cote": round(cote_btts, 2),
                "ev": round(ev_btts, 3)
            })

# =============================
# ANALYSE
# =============================
safe_results = []
sniper_results = []
historique = []

for match in fixtures.get("response", []):

    print("ANALYSE MATCH")

    league_id = match["league"]["id"]

    if LEAGUES_AUTORISEES and league_id not in LEAGUES_AUTORISEES:
        continue

    print("LIGUE OK")

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    match_id = match["fixture"]["id"]

    print(home, "vs", away)

    home_stats = get_stats(match["teams"]["home"]["id"], league_id)
    away_stats = get_stats(match["teams"]["away"]["id"], league_id)

    if not home_stats or not away_stats:
        print("PAS DE STATS")
        continue

    print("STATS OK")

    try:

        hp = home_stats["fixtures"]["played"]["home"]
        ap = away_stats["fixtures"]["played"]["away"]

        att_home = home_stats["goals"]["for"]["total"]["home"] / max(hp, 1)
        def_home = home_stats["goals"]["against"]["total"]["home"] / max(hp, 1)

        att_away = away_stats["goals"]["for"]["total"]["away"] / max(ap, 1)
        def_away = away_stats["goals"]["against"]["total"]["away"] / max(ap, 1)

        xg_home = (att_home + def_away) / 2
        xg_away = (att_away + def_home) / 2

        total_xg = xg_home + xg_away

        print("TOTAL XG =", round(total_xg, 2))

        if total_xg >= 2.8:
            print("OVER 2.5 POSSIBLE")

        if xg_home >= 1 and xg_away >= 1:
            print("BTTS POSSIBLE")

        diff = (xg_home - xg_away) * 10

        features = pd.DataFrame([[

            round(xg_home),
            round(xg_away)

        ]], columns=[

            "home_goals",
            "away_goals"

        ])

        force_home = xg_home * 1.2
        force_away = xg_away

        proba_win = 50 + ((force_home - force_away) * 15)

        proba_win = max(5, min(95, proba_win))

        print(home, "vs", away)
        print("DIFF =", round(diff, 2))
        print("ML =", round(proba_win, 1))
        
        print("XG HOME:", round(xg_home, 2))
        print("XG AWAY:", round(xg_away, 2))

        score_estime = f"{round(xg_home)}-{round(xg_away)}"
        print("SCORE ESTIMÉ:", score_estime)

        cote_win = get_odds(match_id, "Match Winner", "Home")

        if cote_win is None:
            print("PAS DE COTE")
            continue

        ev = ((proba_win / 100) * cote_win) - 1

        print(home, "vs", away)
        print("DIFF =", round(diff, 2))
        print("ML =", round(proba_win, 1))
        print("XG HOME =", round(xg_home, 2))
        print("XG AWAY =", round(xg_away, 2))
        print("COTE =", cote_win)
        print("EV =", round(ev, 3))
        
        score_ia = calcul_score(
            proba_win,
            ev,
            diff,
            xg_home,
            xg_away
        )

        print("SCORE IA =", score_ia)

        if score_ia >= 85:
            note_ia = "👑 GOD TIER"

        elif score_ia >= 75:
            note_ia = "🔥 ELITE"

        elif score_ia >= 65:
            note_ia = "🟢 SAFE"

        else:
            note_ia = "🟡 RISKY"

        print("NOTE IA =", note_ia)

        if ev > 0.25 and proba_win >= 60:

            niveau = "🔥 ULTRA SAFE"

        elif ev > 0.15:

            niveau = "🟢 SAFE"

        else:

            niveau = "🟡 VALUE"

        print("NIVEAU =", niveau)

        analyser_over_btts(
            match_id,
            home,
            away,
            total_xg,
            xg_home,
            xg_away
        )
        

        if diff < 1.5:
            continue

        if proba_win < 52:
            continue

        if xg_home < 1.1:
            continue

        if xg_away > 1.8:
            continue

        print("COTE:", cote_win)
        print("EV:", round(ev, 3))

        if ev > 0.08 and proba_win >= 55:

            print("SAFE BET AJOUTÉ")

            safe_results.append({
                "niveau": niveau,
                "note": note_ia,
                "score": score_ia,
                "match": f"{home} vs {away}",
                "pari": "Victoire domicile",
                "proba": round(proba_win, 1),
                "cote": round(cote_win, 2),
                "ev": round(ev, 3)
            })

            historique.append({
                "date": today,
                "match": f"{home} vs {away}",
                "pari": "Victoire domicile",
                "proba": round(proba_win, 1),
                "cote": round(cote_win, 2),
                "ev": round(ev, 3)
            })

    except Exception as e:

        print("ERREUR:", e)
        continue
                                                                                                                                                                                            # =============================
# TRI
# =============================
safe_results = sorted(
    safe_results,
    key=lambda x: x["score"],
    reverse=True
)
sniper_results = sorted(sniper_results, key=lambda x: x["ev"], reverse=True)

# =============================
# OUTPUT
# =============================
print("\n🟢 SAFE BETS\n")

for r in safe_results[:5]:
    montant = mise(r["proba"], r["cote"])

    msg = f"""{r['niveau']} {r['match']}
{r['pari']} | {r['cote']}
Score IA: {r['score']}/100
Note IA: {r['note']}
Confiance: {r['proba']}%
Mise: {montant}€
"""

    print(msg)
    envoyer_telegram(msg)

print("\n💣 SNIPER BETS\n")

for r in sniper_results[:3]:
    montant = mise(r["proba"], r["cote"])

    msg = f"""💣 {r['match']}
{r['pari']} | {r['cote']}
Confiance: {r['proba']}%
Mise: {montant}€
"""

    print(msg)
    envoyer_telegram(msg)

if historique:

    df = pd.DataFrame(historique)

    fichier = "historique_paris.csv"

    if os.path.exists(fichier):

        ancien = pd.read_csv(fichier)
        df = pd.concat([ancien, df], ignore_index=True)

    df.to_csv(fichier, index=False)
# =============================
# UPDATE RESULTATS
# =============================

fichier = "historique_paris.csv"

if os.path.exists(fichier):

    df = pd.read_csv(fichier)

    if "resultat" not in df.columns:
        df["resultat"] = ""

    if "profit" not in df.columns:
        df["profit"] = 0

    for index, row in df.iterrows():

        if row["resultat"] != "":
            continue

        try:

            equipes = row["match"].split(" vs ")

            home = equipes[0]
            away = equipes[1]

            url = f"https://v3.football.api-sports.io/fixtures?date={row['date']}"

            data = requests.get(url, headers=headers).json()

            for match in data.get("response", []):

                h = match["teams"]["home"]["name"]
                a = match["teams"]["away"]["name"]

                if h == home and a == away:

                    hg = match["goals"]["home"]
                    ag = match["goals"]["away"]

                    if hg is None or ag is None:
                        continue

                    if hg > ag:

                        df.at[index, "resultat"] = "WIN"

                        profit = (float(row["cote"]) - 1) * 5
                        df.at[index, "profit"] = round(profit, 2)

                    else:

                        df.at[index, "resultat"] = "LOSE"
                        df.at[index, "profit"] = -5

                    print(home, "vs", away, "=>", df.at[index, "resultat"])

        except Exception as e:

            print("ERREUR UPDATE:", e)

        time.sleep(1)


    df = df.drop_duplicates(
        subset=["date", "match", "pari"],
        keep="last"
    )


    df.to_csv(fichier, index=False)


print("RESULTATS MIS A JOUR")
print("HISTORIQUE SAUVEGARDÉ")
print("\nAnalyse terminée.")

date = today
wins = 0
losses = 0
profit_total = 0
taux_reussite = 0

if os.path.exists("historique_paris.csv"):
    df_bilan = pd.read_csv("historique_paris.csv")

    if "resultat" in df_bilan.columns:
        wins = len(df_bilan[df_bilan["resultat"] == "WIN"])
        losses = len(df_bilan[df_bilan["resultat"] == "LOSE"])

    if "profit" in df_bilan.columns:
        profit_total = df_bilan["profit"].sum()

    total_termines = wins + losses

    if total_termines > 0:
        taux_reussite = round((wins / total_termines) * 100, 1)

resume = f"""🤖 Analyse terminée

📅 {date}

📊 Matchs analysés : {len(fixtures.get("response", []))}
🟢 SAFE BETS : {len(safe_results)}
💣 SNIPER BETS : {len(sniper_results)}

📈 Bilan IA
✅ Gagnés : {wins}
❌ Perdus : {losses}
🎯 Réussite : {taux_reussite}%
💰 Profit : {round(profit_total, 2)}€

⏳ Prochaine analyse dans 3 heures.

"""
top3 = safe_results[:3]

if top3:
    message_top = "🏆 TOP 3 PARIS IA 🏆\n\n"

    for i, r in enumerate(top3, start=1):
        montant = mise(r["proba"], r["cote"])

        message_top += f"""
{i}️⃣ {r['match']}

🎯 {r['pari']}
💰 Cote : {r['cote']}
🤖 Score IA : {r['score']}/100
📊 Confiance : {r['proba']}%
💵 Mise : {montant}€
⭐ {r['note']}

"""

    envoyer_telegram(message_top)
envoyer_telegram(resume)


