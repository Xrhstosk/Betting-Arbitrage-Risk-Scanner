import time
import requests
import psycopg2
from datetime import datetime

# 1. ΡΥΘΜΙΣΕΙΣ API & ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ (PostgreSQL)
API_KEY = "6c660f395b0185ef3684334958d2dc6d"
REGION = "eu"
TOTAL_BUDGET = 100.0

# 🐘 ΣΤΟΙΧΕΙΑ ΣΥΝΔΕΣΗΣ PGADMIN / POSTGRESQL
DB_CONFIG = {
    "dbname": "arbitrage_db",
    "user": "postgres",
    "password": "kgkdts7819",  # <-- ελεχγος
    "host": "localhost",
    "port": "5433"
}

# 🚫 ΛΙΣΤΑ ΑΠΟΚΛΕΙΣΜΕΝΩΝ ΕΤΑΙΡΕΙΩΝ (Blacklist)
EXCLUDED_BOOKIES = [
    "LeoVegas",
    "1xBet",
    "BetOnline.ag",
    "Coolbet",
    "Pinnacle",
    "William Hill",
    "Betfair",
    "Tipico",
    "888sport",
    "matchbook",
    "Unibet",
    "Nordic Bet",
    "GTbets",
    "MyBookie.ag",
]

def save_to_postgres(data):
    """Αποθηκεύει ή ενημερώνει τις επιλεγμένες ευκαιρίες στην PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        INSERT INTO arbitrage_opportunities (
            sport_title, match_name, market_type, theoretical_profit_pct, 
            actual_net_profit, total_cost,
            outcome1_name, outcome1_odds, outcome1_bookie, outcome1_stake,
            outcomeX_odds, outcomeX_bookie, outcomeX_stake,
            outcome2_name, outcome2_odds, outcome2_bookie, outcome2_stake,
            notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (match_name, market_type, outcome1_bookie, outcome2_bookie) 
        DO UPDATE SET 
            found_at = CURRENT_TIMESTAMP,
            theoretical_profit_pct = EXCLUDED.theoretical_profit_pct,
            actual_net_profit = EXCLUDED.actual_net_profit,
            notes = EXCLUDED.notes;
        """
        
        cursor.execute(query, (
            data['sport_title'], data['match_name'], data['market_type'],
            data['margin_pct'], data['net_1'], data['total_cost'],
            data.get('o1_name'), data.get('o1_odds'), data.get('o1_bookie'), data.get('o1_stake'),
            data.get('oX_odds'), data.get('oX_bookie'), data.get('oX_stake'),
            data.get('o2_name'), data.get('o2_odds'), data.get('o2_bookie'), data.get('o2_stake'),
            f"NetSum: {data['net_sum']:+.2f}€ | Type: {data['market_type']}"
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"   💾 [DB Success] Αποθηκεύτηκε: {data['match_name']}")
    except Exception as e:
        print(f"\n   ❌ [DB Error] Αποτυχία εγγραφής για '{data['match_name']}': {e}\n")
        
        cursor.execute(query, (
            data['sport_title'], data['match_name'], data['market_type'],
            data['margin_pct'], data['net_1'], data['total_cost'],
            data.get('o1_name'), data.get('o1_odds'), data.get('o1_bookie'), data.get('o1_stake'),
            data.get('oX_odds'), data.get('oX_bookie'), data.get('oX_stake'),
            data.get('o2_name'), data.get('o2_odds'), data.get('o2_bookie'), data.get('o2_stake'),
            f"NetSum: {data['net_sum']:+.2f}€ | Type: {data['market_type']}"
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ⚠️ [DB Error] Αποτυχία εγγραφής στη βάση: {e}")

def get_active_sports():
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return [s for s in response.json() if s.get('active', False)]
        return []
    except Exception as e:
        print(f"❌ Σφάλμα σύνδεσης: {e}")
        return []

def scan_sport(sport_key, sport_title):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions={REGION}&markets=h2h"
    matched_opportunities = []
    remaining_calls = "N/A"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return matched_opportunities, remaining_calls

        remaining_calls = response.headers.get('x-requests-remaining', 'N/A')
        matches = response.json()

        for match in matches:
            home_team = match.get('home_team', 'Home')
            away_team = match.get('away_team', 'Away')
            
            best_odds = {}
            best_bookies = {}
            
            for bookmaker in match.get('bookmakers', []):
                bookie_name = bookmaker['title']
                if any(excluded.lower() in bookie_name.lower() for excluded in EXCLUDED_BOOKIES):
                    continue

                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market.get('outcomes', []):
                            name = outcome['name']
                            price = float(outcome['price'])
                            if name not in best_odds or price > best_odds[name]:
                                best_odds[name] = price
                                best_bookies[name] = bookie_name

            # --- 1. 3-WAY MATCHES (Ποδόσφαιρο) ---
            if len(best_odds) == 3 and 'Draw' in best_odds:
                o1, oX, o2 = best_odds[home_team], best_odds['Draw'], best_odds[away_team]
                b1, bX, b2 = best_bookies[home_team], best_bookies['Draw'], best_bookies[away_team]
                
                margin = (1 / o1) + (1 / oX) + (1 / o2)
                margin_pct = margin * 100
                
                # Break-even για το Χ
                stake_X = max(5, round((TOTAL_BUDGET / oX) / 5) * 5)
                remaining_budget = TOTAL_BUDGET - stake_X
                
                ratio_1 = (1 / o1) / ((1 / o1) + (1 / o2))
                stake_1 = max(5, round((remaining_budget * ratio_1) / 5) * 5)
                stake_2 = max(5, remaining_budget - stake_1)
                actual_cost = stake_1 + stake_X + stake_2
                
                ret_1 = (stake_1 * o1) - actual_cost
                ret_X = (stake_X * oX) - actual_cost
                ret_2 = (stake_2 * o2) - actual_cost
                net_sum = ret_1 + ret_2
                
                if (-2.0 <= ret_X <= 2.0) and (net_sum >= 2.0):
                    matched_opportunities.append({
                        'sport_title': sport_title,
                        'match_name': f"{home_team} vs {away_team}",
                        'market_type': '3-WAY',
                        'margin_pct': margin_pct,
                        'total_cost': actual_cost,
                        'o1_name': home_team, 'o1_odds': o1, 'o1_bookie': b1, 'o1_stake': stake_1, 'net_1': ret_1,
                        'oX_odds': oX, 'oX_bookie': bX, 'oX_stake': stake_X, 'net_X': ret_X,
                        'o2_name': away_team, 'o2_odds': o2, 'o2_bookie': b2, 'o2_stake': stake_2, 'net_2': ret_2,
                        'net_sum': net_sum
                    })

            # --- 2. 2-WAY MATCHES (Τένις, Μπάσκετ κλπ) ---
            elif len(best_odds) == 2 and 'Draw' not in best_odds:
                o1, o2 = best_odds[home_team], best_odds[away_team]
                b1, b2 = best_bookies[home_team], best_bookies[away_team]
                
                margin = (1 / o1) + (1 / o2)
                margin_pct = margin * 100
                
                raw_1 = TOTAL_BUDGET / (margin * o1)
                raw_2 = TOTAL_BUDGET / (margin * o2)
                stake_1 = max(5, round(raw_1 / 5) * 5)
                stake_2 = max(5, round(raw_2 / 5) * 5)
                actual_cost = stake_1 + stake_2
                
                ret_1 = (stake_1 * o1) - actual_cost
                ret_2 = (stake_2 * o2) - actual_cost
                net_sum = ret_1 + ret_2
                
                # Φίλτρο για 2-Way: Άθροισμα Net 1 + Net 2 >= +2.00€
                if net_sum >= 2.0:
                    matched_opportunities.append({
                        'sport_title': sport_title,
                        'match_name': f"{home_team} vs {away_team}",
                        'market_type': '2-WAY',
                        'margin_pct': margin_pct,
                        'total_cost': actual_cost,
                        'o1_name': home_team, 'o1_odds': o1, 'o1_bookie': b1, 'o1_stake': stake_1, 'net_1': ret_1,
                        'oX_odds': None, 'oX_bookie': None, 'oX_stake': 0, 'net_X': 0,
                        'o2_name': away_team, 'o2_odds': o2, 'o2_bookie': b2, 'o2_stake': stake_2, 'net_2': ret_2,
                        'net_sum': net_sum
                    })

    except Exception as e:
        print(f"⚠️ Σφάλμα στο {sport_key}: {e}")
        
    return matched_opportunities, remaining_calls

def main():
    print("=" * 70)
    print("   UNIVERSAL ASYMMETRIC RISK SCANNER (3-WAY & 2-WAY SPORTS)   ")
    print("=" * 70)
    
    active_sports = get_active_sports()
    if not active_sports:
        print("❌ Δεν βρέθηκαν ενεργά αθλήματα.")
        return

    print(f"🌍 Εντοπίστηκαν {len(active_sports)} ενεργές διοργανώσεις (Ποδόσφαιρο, Τένις, Μπάσκετ κλπ).")
    confirm = input("⚠️ Εκτέλεση καθολικού σκαναρίσματος; (y/n): ")
    if confirm.lower() != 'y':
        print("🛑 Η εκτέλεση ακυρώθηκε.")
        return

    all_matched = []
    latest_rem = "N/A"

    print("\n⏳ Έναρξη σκαναρίσματος σε όλα τα αθλήματα...")
    for idx, sport in enumerate(active_sports, 1):
        print(f"[{idx}/{len(active_sports)}] Έλεγχος: {sport['title']}...", end="\r")
        opps, rem = scan_sport(sport['key'], sport['title'])
        if opps:
            all_matched.extend(opps)
        if rem != "N/A":
            latest_rem = rem
        time.sleep(0.1)

    print("\n\n" + "=" * 70)
    print(f"✅ Ολοκληρώθηκε ο έλεγχος! Βρέθηκαν {len(all_matched)} αγώνες που πληρούν τα κριτήρια.")
    print("=" * 70)

    if not all_matched:
        print("ℹ️ Δεν βρέθηκε κανένας αγώνας με τα συγκεκριμένα κριτήρια τη δεδομένη στιγμή.")
        print(f"📊 Απομένουν {latest_rem} API calls για αυτόν τον μήνα.")
        return

    for idx, match in enumerate(all_matched, 1):
        print(f"\n#{idx} 🎯 {match['match_name']} | {match['sport_title']} ({match['market_type']})")
        print(f"    📈 Total Margin: {match['margin_pct']:.2f}% | Κόστος: {match['total_cost']:.2f}€")
        
        if match['market_type'] == '3-WAY':
            print(f"    [1] {match['o1_name']}: {match['o1_odds']} ({match['o1_bookie']}) -> {match['o1_stake']}€ | Καθαρό: {match['net_1']:+.2f}€")
            print(f"    [X] Ισοπαλία: {match['oX_odds']} ({match['oX_bookie']}) -> {match['oX_stake']}€ | Καθαρό: {match['net_X']:+.2f}€ (Break-even)")
            print(f"    [2] {match['o2_name']}: {match['o2_odds']} ({match['o2_bookie']}) -> {match['o2_stake']}€ | Καθαρό: {match['net_2']:+.2f}€")
        else:
            print(f"    [1] {match['o1_name']}: {match['o1_odds']} ({match['o1_bookie']}) -> {match['o1_stake']}€ | Καθαρό: {match['net_1']:+.2f}€")
            print(f"    [2] {match['o2_name']}: {match['o2_odds']} ({match['o2_bookie']}) -> {match['o2_stake']}€ | Καθαρό: {match['net_2']:+.2f}€")
            
        print(f"    ➕ Άθροισμα (Net 1 + Net 2): {match['net_sum']:+.2f}€")
        save_to_postgres(match)

    print("\n" + "=" * 70)
    print(f"💾 Αποθηκεύτηκαν επιτυχώς {len(all_matched)} αγώνες στη βάση PostgreSQL (pgAdmin).")
    print(f"📊 Απομένουν {latest_rem} API calls για αυτόν τον μήνα.")
    print("=" * 70)

if __name__ == "__main__":
    main()