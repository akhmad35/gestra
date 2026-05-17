import sqlite3

def run_migration():
    conn = sqlite3.connect('gestra.db')
    c = conn.cursor()
    
    # Check if columns exist
    cols = [col[1] for col in c.execute("PRAGMA table_info(latihan)").fetchall()]
    
    if 'metode_pembuatan' not in cols:
        print("Adding columns...")
        c.execute("ALTER TABLE latihan ADD COLUMN metode_pembuatan VARCHAR DEFAULT 'manual'")
        c.execute("ALTER TABLE latihan ADD COLUMN dataset_type VARCHAR")
        c.execute("ALTER TABLE latihan ADD COLUMN jumlah_soal INTEGER DEFAULT 5")
        c.execute("ALTER TABLE latihan ADD COLUMN durasi_menit INTEGER DEFAULT 0")
        c.execute("ALTER TABLE latihan ADD COLUMN waktu_mulai DATETIME")
        c.execute("ALTER TABLE latihan ADD COLUMN waktu_selesai DATETIME")
        c.execute("ALTER TABLE latihan ADD COLUMN status VARCHAR DEFAULT 'draft'")
        c.execute("ALTER TABLE latihan ADD COLUMN soal_tergenerate TEXT")
        conn.commit()
        print("Columns added successfully.")
    else:
        print("Columns already exist.")

if __name__ == "__main__":
    run_migration()
