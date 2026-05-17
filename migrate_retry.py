import sqlite3

def run_migration():
    conn = sqlite3.connect('gestra.db')
    c = conn.cursor()
    
    # Check if columns exist
    cols = [col[1] for col in c.execute("PRAGMA table_info(latihan)").fetchall()]
    
    new_cols = {
        'izinkan_retry': 'BOOLEAN DEFAULT 0',
        'max_attempt': 'INTEGER DEFAULT 1',
        'mode_timer': "VARCHAR DEFAULT 'total'",
        'durasi_per_soal': 'INTEGER DEFAULT 30',
        'izinkan_lihat_hasil': 'BOOLEAN DEFAULT 1'
    }
    
    for col, definition in new_cols.items():
        if col not in cols:
            print(f"Adding column {col}...")
            c.execute(f"ALTER TABLE latihan ADD COLUMN {col} {definition}")
            
    conn.commit()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
