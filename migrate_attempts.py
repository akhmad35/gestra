import sqlite3

def run_migration():
    conn = sqlite3.connect('gestra.db')
    c = conn.cursor()
    
    # Check if columns exist
    cols = [col[1] for col in c.execute("PRAGMA table_info(jawaban)").fetchall()]
    
    if 'attempts_count' not in cols:
        print("Adding column attempts_count...")
        c.execute("ALTER TABLE jawaban ADD COLUMN attempts_count INTEGER DEFAULT 1")
            
    conn.commit()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
