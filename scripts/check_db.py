import sqlite3

conn = sqlite3.connect('mycelial_patterns.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check pattern count
try:
    cursor.execute('SELECT COUNT(*) FROM patterns')
    count = cursor.fetchone()[0]
    print(f'\nTotal patterns in DB: {count}')

    # Get recent patterns
    cursor.execute('SELECT * FROM patterns ORDER BY timestamp DESC LIMIT 5')
    rows = cursor.fetchall()
    print(f'\nRecent 5 patterns:')
    for row in rows:
        print(row)
except Exception as e:
    print(f'Error querying patterns: {e}')

conn.close()
