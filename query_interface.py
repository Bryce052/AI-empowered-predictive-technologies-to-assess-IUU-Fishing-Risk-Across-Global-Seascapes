import sqlite3

# Connect to the SQLite database
def connect_to_database(db_name="maritime_data.db"):
    return sqlite3.connect(db_name)

# Query: Find vessel by name
def find_vessel_by_name(conn, vessel_name):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE vessel_name = ?
    ''', (vessel_name,))
    return cursor.fetchall()

# Query: Get all vessels with a specific flag
def get_vessels_by_flag(conn, flag):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE flag = ?
    ''', (flag,))
    return cursor.fetchall()

# Query: Get all vessels in a specific status
def get_vessels_by_status(conn, status):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE status = ?
    ''', (status,))
    return cursor.fetchall()

# Main script for testing queries
if __name__ == "__main__":
    conn = connect_to_database()
    
    # Example 1: Find a vessel by name
    vessel_name = "Poseidon Explorer"
    result = find_vessel_by_name(conn, vessel_name)
    print(f"Details for vessel '{vessel_name}':", result)
    
    # Example 2: Get vessels with a specific flag
    flag = "Panama"
    result = get_vessels_by_flag(conn, flag)
    print(f"Vessels with flag '{flag}':", result)
    
    # Example 3: Get vessels in a specific status
    status = "In Transit"
    result = get_vessels_by_status(conn, status)
    print(f"Vessels with status '{status}':", result)
    
    conn.close()
