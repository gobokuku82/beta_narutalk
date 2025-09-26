"""
Simple test to check database access
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('database/storage/sales_performance/sales_performance_db.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Test simple query with month column
print("Testing simple query with month column:")
try:
    sql = "SELECT * FROM sales_performance WHERE `202403` > 0 LIMIT 5"
    cursor.execute(sql)
    rows = cursor.fetchall()

    print(f"Found {len(rows)} rows")
    if rows:
        # Print first row
        row = rows[0]
        print("\nFirst row data:")
        for key in row.keys():
            print(f"  {repr(key)}: {row[key]}")

except Exception as e:
    print(f"Error: {e}")

conn.close()