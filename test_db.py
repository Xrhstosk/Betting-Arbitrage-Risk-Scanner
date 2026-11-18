import psycopg2

# Συνδεόμαστε me oles tis baseis kai rwtame ean blepei to systhma toyow pinakes bets', 'matches', 'player_stats', 'users'
TEST_CONFIG = {
    "dbname": "Diplwmatikh",
    "user": "postgres",
    "password": "kgkdts7819",  # <-- Βάλε τον κωδικό σου εδώ
    "host": "localhost",
    "port": "5433"
}

def inspect_postgres_server():
    print("⏳ Σύνδεση στον PostgreSQL Server (port 5432)...")
    try:
        conn = psycopg2.connect(**TEST_CONFIG)
        cursor = conn.cursor()
        
        # 1. Ανάκτηση όλων των πραγματικών ονομάτων βάσεων
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
        databases = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "=" * 60)
        print("📁 ΠΡΑΓΜΑΤΙΚΕΣ ΒΑΣΕΙΣ ΔΕΔΟΜΕΝΩΝ ΠΟΥ ΥΠΑΡΧΟΥΝ ΣΤΟΝ SERVER:")
        print("=" * 60)
        for db in databases:
            print(f"  👉 '{db}'")
        print("=" * 60)
        
        # 2. Αν κάποια βάση περιέχει τους πίνακες της διπλωματικής σου
        print("\n🔍 Αναζήτηση των πινάκων ('matches', 'bets', 'player_stats', 'users')...")
        for db in databases:
            try:
                temp_conn = psycopg2.connect(
                    dbname=db, 
                    user=TEST_CONFIG['user'], 
                    password=TEST_CONFIG['password'], 
                    host=TEST_CONFIG['host'], 
                    port=TEST_CONFIG['port']
                )
                temp_cur = temp_conn.cursor()
                temp_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('matches', 'bets', 'player_stats', 'users');
                """)
                found_tables = [r[0] for r in temp_cur.fetchall()]
                if found_tables:
                    print(f"  🎯 Στη βάση '{db}' βρέθηκαν οι πίνακες: {found_tables}")
                temp_cur.close()
                temp_conn.close()
            except Exception:
                pass
                
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print("\n❌ ΑΠΟΤΥΧΙΑ ΣΥΝΔΕΣΗΣ ΣΤΟΝ SERVER:")
        print(f"⚠️ {e}")
        print("\n💡 Αν δεν συνδέεται ούτε στο 'postgres':")
        print("   - Έλεγξε αν το port στο pgAdmin είναι 5433 αντί για 5432.")
        print("   - Επιβεβαίωσε τον κωδικό του χρήστη 'postgres'.")

if __name__ == "__main__":
    inspect_postgres_server()