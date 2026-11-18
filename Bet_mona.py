import math

def get_valid_odds(prompt):
    """Συνάρτηση που ζητάει απόδοση και ξαναρωτάει αν ο χρήστης κάνει λάθος"""
    while True:
        try:
            user_input = input(prompt).strip()
            # Αν ο χρήστης έβαλε κατά λάθος κόμμα, το αλλάζουμε σε τελεία
            if ',' in user_input:
                user_input = user_input.replace(',', '.')
                
            odds_value = float(user_input)
            
            if odds_value <= 1.0:
                print("❌ Λάθος: Η απόδοση πρέπει να είναι μεγαλύτερη από 1.00. Ξαναπροσπαθήστε.")
                continue
                
            return odds_value
        except ValueError:
            print("❌ Λάθος: Δεν δώσατε έγκυρο αριθμό (π.χ. γράψτε 2.15 και όχι γράμματα). Ξαναπροσπαθήστε.")

def calculate_arbitrage():
    print("=" * 60)
    print("      BET_MONA: SMART ARBITRAGE CALCULATOR (Fixed Budget 100€)   ")
    print("=" * 60)
    
    # 1. Επιλογή τύπου αγοράς με έλεγχο λάθους
    while True:
        market_type = input("Επιλέξτε τύπο αγώνα:\n[2] για 2 αποτελέσματα (Τένις, Μπάσκετ κλπ)\n[3] για 3 αποτελέσματα (Ποδόσφαιρο 1-X-2)\nΕπιλογή: ").strip()
        if market_type in ['2', '3']:
            break
        print("❌ Λάθος επιλογή. Παρακαλώ πληκτρολογήστε μόνο 2 ή 3.\n")
    
    # Σταθερό Budget στα 100 ευρώ
    TOTAL_BUDGET = 100.0
    odds = []

    # 2. Εισαγωγή αποδόσεων με αυτόματη επανάληψη σε λάθος
    print("\n--- ΕΙΣΑΓΩΓΗ ΑΠΟΔΟΣΕΩΝ ---")
    odds.append(get_valid_odds("Καλύτερη απόδοση για Νίκη 1 (Γηπεδούχος): "))
    
    if market_type == '3':
        odds.append(get_valid_odds("Καλύτερη απόδοση για Χ (Ισοπαλία): "))
        
    odds.append(get_valid_odds("Καλύτερη απόδοση για Νίκη 2 (Φιλοξενούμενος): "))

    # 3. Υπολογισμός Arbitrage Margin (L)
    arbitrage_margin = sum(1 / o for o in odds)
    
    print("\n" + "-" * 50)
    print(f"Συνολικό Άθροισμα Πιθανοτήτων: {arbitrage_margin * 100:.2f}%")
    
    # Έλεγχος αν υπάρχει Sure Bet
    if arbitrage_margin >= 1.0:
        print("❌ ΔΕΝ ΥΠΑΡΧΕΙ ARBITRAGE σε αυτές τις αποδόσεις.")
        print(f"Η γκανιότα είναι υπέρ της στοιχηματικής: {((arbitrage_margin - 1) * 100):.2f}%")
        print("-" * 50)
        return
    
    profit_margin_raw = (1 - arbitrage_margin) * 100
    print(f"✅ ΥΠΑΡΧΕΙ ARBITRAGE! Θεωρητικό Περιθώριο Κέρδους: {profit_margin_raw:.2f}%")
    print("-" * 50)

    # 4. Μαθηματικό Ιδανικό Ποντάρισμα
    raw_stakes = [TOTAL_BUDGET / (arbitrage_margin * o) for o in odds]
    
    # 5. SMART ROUNDING: Στρογγυλοποίηση στα κοντινότερα 5 ευρώ
    smart_stakes = []
    for stake in raw_stakes:
        rounded = max(5, round(stake / 5) * 5)
        smart_stakes.append(rounded)
    
    actual_investment = sum(smart_stakes)
    
    print("\n💰 ΠΡΟΤΕΙΝΟΜΕΝΑ ΠΟΝΤΑΡΙΣΜΑΤΑ (Στρογγυλοποιημένα για προστασία):")
    for i, stake in enumerate(smart_stakes):
        if market_type == '3':
            label = "Σημείο 1" if i == 0 else ("Σημείο Χ" if i == 1 else "Σημείο 2")
        else:
            label = "Σημείο 1" if i == 0 else "Σημείο 2"
            
        print(f"  👉 {label} (Απόδοση {odds[i]}): Ποντάρετε {stake} €")
    
    print("\n📊 ΑΝΑΛΥΣΗ ΠΡΑΓΜΑΤΙΚΩΝ ΑΠΟΤΕΛΕΣΜΑΤΩΝ (Για Budget ~100€):")
    print(f"  Συνολικό Πραγματικό Κόστος: {actual_investment} €")
    
    min_return = float('inf')
    for i, stake in enumerate(smart_stakes):
        possible_return = stake * odds[i]
        if market_type == '3':
            label = "Σημείο 1" if i == 0 else ("Σημείο Χ" if i == 1 else "Σημείο 2")
        else:
            label = "Σημείο 1" if i == 0 else "Σημείο 2"
            
        net_for_this_outcome = possible_return - actual_investment
        print(f"  • Αν βγει το {label}: Είσπραξη {possible_return:.2f} € | Καθαρό Κέρδος: {net_for_this_outcome:.2f} €")
        
        if possible_return < min_return:
            min_return = possible_return
            
    net_profit = min_return - actual_investment
    real_profit_margin = (net_profit / actual_investment) * 100
    
    print("-" * 50)
    if net_profit > 0:
        print(f"📉 Ελάχιστο Εγγυημένο Καθαρό Κέρδος: {net_profit:.2f} € ({real_profit_margin:.2f}%)")
    else:
        print(f"⚠️ Λόγω της στρογγυλοποίησης στα 5€, σε αυτό το σενάριο ρισκάρεις μικρή χασούρα: {net_profit:.2f} €")
        print("Αυτό συμβαίνει γιατί το 100€ δεν «σπάει» πάντα τέλεια σε πεντάευρα για τις συγκεκριμένες αποδόσεις.")
    print("=" * 60)

if __name__ == "__main__":
    calculate_arbitrage()