# Αυτοματοποιημένη Κατηγοριοποίηση Παικτών Στοιχήματος (Sharps vs. Casuals)

Ένα ολοκληρωμένο σύστημα Data Engineering και Machine Learning με χρήση **PostgreSQL (PL/pgSQL)** και **Python (Scikit-Learn)** για τον real-time εντοπισμό επαγγελματιών παικτών (*Sharps*) και τον διαχωρισμό τους από τους ψυχαγωγικούς χρήστες (*Casuals*).

## Περιγραφή & Στόχος
Στην ανάλυση δεδομένων στοιχηματισμού, το καθαρό κέρδος δεν αρκεί βραχυπρόθεσμα για να αξιολογήσει την ικανότητα ενός παίκτη λόγω του παράγοντα τύχης. Ο πιο αξιόπιστος δείκτης είναι το **CLV (Closing Line Value)** — η διαφορά ανάμεσα στην απόδοση που πρόλαβε ο παίκτης και στην τελική απόδοση κλεισίματος της αγοράς.

Το σύστημα υλοποιείται σε δύο στάδια:
1. **Real-Time Υπολογισμός στη Βάση (PostgreSQL):** Ένας `AFTER INSERT` trigger υπολογίζει αυτόματα το καθαρό κέρδος και το CLV τη στιγμή που καταχωρείται κάθε στοίχημα, ενημερώνοντας ακαριαία τα συγκεντρωτικά στατιστικά του παίκτη (`ON CONFLICT ... DO UPDATE`).
2. **Μηχανική Μάθηση (Python):** Ένα script αντλεί τα δεδομένα από τη βάση, εφαρμόζει κανονικοποίηση (`StandardScaler`) και χρησιμοποιεί τον αλγόριθμο **K-Means Clustering** (`k=2`) για τον αυτόματο διαχωρισμό των παικτών και την οπτικοποίηση των αποτελεσμάτων.

## Τεχνολογίες
* **Βάση Δεδομένων:** PostgreSQL, PL/pgSQL (Triggers, Atomic Upserts)
* **Ανάλυση & AI:** Python, SQLAlchemy, Pandas, Scikit-Learn (`StandardScaler`, `KMeans`)
* **Οπτικοποίηση:** Matplotlib, Seaborn

## Δομή Αρχείων
* `database_schema.sql` — Η δομή των πινάκων (`matches`, `bets`, `player_stats`) και η συνάρτηση του trigger `update_player_stats()`.
* `clustering_analysis.py` — Ο κώδικας σύνδεσης με τη βάση, εφαρμογής του K-Means και σχεδίασης του Scatter Plot.
* `requirements.txt` — Οι απαραίτητες βιβλιοθήκες Python.

## Οδηγίες Εκτέλεσης

1. **Ρύθμιση Βάσης Δεδομένων:**
   * Δημιουργήστε μια βάση PostgreSQL με όνομα `Diplwmatikh` (στην πόρτα `5433`).
   * Εκτελέστε το αρχείο `database_schema.sql` μέσω pgAdmin ή `psql`.

2. **Εκτέλεση Ανάλυσης:**
   * Συμπληρώστε τα στοιχεία σύνδεσης (κωδικό πρόσβασης) στο `clustering_analysis.py`.
   * Εγκαταστήστε τις βιβλιοθήκες και τρέξτε το script:
   ```bash
   pip install -r requirements.txt
   python clustering_analysis.py
