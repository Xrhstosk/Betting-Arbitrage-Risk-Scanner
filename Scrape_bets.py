import asyncio
from playwright.async_api import async_playwright
# Εισάγουμε τη συνάρτηση ελέγχου από το προηγούμενο αρχείο σου
from Bet_mona import calculate_arbitrage 

async def scrape_odds_and_compare(url):
    print("=" * 60)
    print("      SCRAPE_BETS: LIVE ODDS BROWSER & COMPARATOR      ")
    print("=" * 60)
    print(f"🔗 Σύνδεση με τη σελίδα σύγκρισης... ")

    async with async_playwright() as p:
        # ΑΛΛΑΓΗ: headless=False για να βλέπεις τον browser να ανοίγει στην οθόνη σου
        browser = await p.chromium.launch(headless=False)
        
        # Δημιουργία context με human-like User Agent για αποφυγή ban
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Μπλοκάρουμε τις εικόνες για να φορτώνει πιο γρήγορα
            await page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())
            
            # Μειώνουμε το timeout και αλλάζουμε το wait_until σε "commit" για SPA sites
            await page.goto(url, timeout=30000, wait_until="commit")
            
            print("⏳ Αναμονή για τη φόρτωση των αγώνων από το Flashscore...")
            # ΑΛΛΑΓΗ: Περιμένει μέχρι να εμφανιστεί έστω ένας αγώνας στο DOM πριν προχωρήσει
            await page.wait_for_selector(".event__match", timeout=15000)
            
            print("✅ Η σελίδα φορτώθηκε. Ανάλυση πινάκων Flashscore...")
            
            # Αρχικοποίηση μεταβλητών πριν τη λούπα
            max_odds_1 = 0.0
            max_odds_2 = 0.0
            bookie_1 = "Flashscore Best"
            bookie_2 = "Flashscore Best"
            
            # Εστιάζουμε στα match rows του Flashscore
            rows = await page.query_selector_all(".event__match")
            
            if not rows:
                print("❌ Δεν βρέθηκαν rows αγώνων.")
                await browser.close()
                return

            for row in rows:
                # Στο odds tab, οι αποδόσεις των 2 παικτών βρίσκονται στο class '.odds__value'
                odds_cells = await row.query_selector_all(".odds__value")
                if len(odds_cells) < 2:
                    continue
                
                odds_1_text = (await odds_cells[0].inner_text()).replace(',', '.')
                odds_2_text = (await odds_cells[1].inner_text()).replace(',', '.')
                
                try:
                    odds_1 = float(odds_1_text)
                    odds_2 = float(odds_2_text)
                    
                    # Κρατάμε την καλύτερη απόδοση που εντοπίστηκε σε όλο το ταμπλό για το Σημείο 1
                    if odds_1 > max_odds_1:
                        max_odds_1 = odds_1
                        
                    # Κρατάμε την καλύτερη απόδοση που εντοπίστηκε σε όλο το ταμπλό για το Σημείο 2
                    if odds_2 > max_odds_2:
                        max_odds_2 = odds_2
                except ValueError:
                    continue 
            
            # Κλείνουμε τον browser αφού πήραμε τα δεδομένα
            await browser.close()
            
            # --- ΑΠΟΤΕΛΕΣΜΑΤΑ SCRAPING ---
            if max_odds_1 == 0.0 or max_odds_2 == 0.0:
                print("❌ Δεν βρέθηκαν επαρκή νούμερα αποδόσεων στον πίνακα.")
                return
                
            print("\n🏆 ΚΑΛΥΤΕΡΕΣ ΑΠΟΔΟΣΕΙΣ ΠΟΥ ΒΡΕΘΗΚΑΝ ΣΤΟ ΤΑΜΠΛΟ:")
            print(f"  👉 Σημείο 1: {max_odds_1}")
            print(f"  👉 Σημείο 2: {max_odds_2}")
            
            # --- ΑΥΤΟΜΑΤΗ ΔΙΟΧΕΤΕΥΣΗ ΣΤΟ ΜΑΘΗΜΑΤΙΚΟ ΜΟΝΤΕΛΟ ---
            print("\n🔄 Μεταφορά δεδομένων στο Bet_mona για έλεγχο Arbitrage...")
            
            arbitrage_margin = (1 / max_odds_1) + (1 / max_odds_2)
            TOTAL_BUDGET = 100.0
            
            print("-" * 50)
            print(f"Συνολικό Άθροισμα Πιθανοτήτων: {arbitrage_margin * 100:.2f}%")
            
            if arbitrage_margin >= 1.0:
                print("❌ ΔΕΝ ΥΠΑΡΧΕΙ ARBITRAGE. Η αγορά είναι ισορροπημένη.")
            else:
                print(f"✅ ΥΠΑΡΧΕΙ ARBITRAGE! Κέρδος: {(1 - arbitrage_margin) * 100:.2f}%")
                
                raw_1 = TOTAL_BUDGET / (arbitrage_margin * max_odds_1)
                raw_2 = TOTAL_BUDGET / (arbitrage_margin * max_odds_2)
                
                stake_1 = max(5, round(raw_1 / 5) * 5)
                stake_2 = max(5, round(raw_2 / 5) * 5)
                
                print(f"\n💰 ΠΟΝΤΑΡΙΣΜΑΤΑ (Budget 100€):")
                print(f"  • Παίξτε {stake_1} € στο Σημείο 1 ({bookie_1})")
                print(f"  • Παίξτε {stake_2} € στο Σημείο 2 ({bookie_2})")
                
                actual_cost = stake_1 + stake_2
                ret_1 = stake_1 * max_odds_1
                ret_2 = stake_2 * max_odds_2
                min_ret = min(ret_1, ret_2)
                
                print(f"\n📊 Πραγματικό Κόστος: {actual_cost} €")
                print(f"📉 Εγγυημένη Επιστροφή: {min_ret:.2f} € (Καθαρό: {min_ret - actual_cost:.2f} €)")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Σφάλμα κατά το scraping: {e}")
            await browser.close()

# Εκτέλεση με το URL που επιλέξαμε
if __name__ == "__main__":
    target_url = "https://www.flashscore.com/match/football/bayern-munich-nVp0wiqd/vfb-stuttgart-nJQmYp1B/?mid=xrtCcyAe"
    asyncio.run(scrape_odds_and_compare(target_url))