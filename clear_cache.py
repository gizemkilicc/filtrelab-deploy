import sqlite3
import os

db_paths = [
    'backend/filtrelab.db',
    'backend/app.db',
    'backend/database.db',
    'filtrelab.db',
    'app.db',
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    for root, dirs, files in os.walk('backend'):
        for f in files:
            if f.endswith('.db'):
                db_path = os.path.join(root, f)
                break
        if db_path:
            break

if not db_path:
    print("DB dosyası bulunamadı!")
else:
    print(f"DB bulundu: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # analysis_history tablosundaki raw_result sütununu null'la
    # (cross_platform_data ayrı bir sütun değil, raw_result JSON'ın içinde)
    cursor.execute("""
        UPDATE analysis_history
        SET raw_result = NULL
        WHERE raw_result IS NOT NULL;
    """)
    rows = cursor.rowcount
    conn.commit()

    print(f"analysis_history: {rows} kayıt raw_result temizlendi")
    print("Not: In-memory cross-platform cache backend restart ile temizlenir.")
    conn.close()
