import sqlite3

# Query functions (same as in query_interface.py)
def connect_to_database(db_name="maritime_data.db"):
    return sqlite3.connect(db_name)

def find_vessel_by_name(conn, vessel_name):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE vessel_name = ?
    ''', (vessel_name,))
    return cursor.fetchall()

def get_vessels_by_flag(conn, flag):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE flag = ?
    ''', (flag,))
    return cursor.fetchall()

def get_vessels_by_status(conn, status):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vessels WHERE status = ?
    ''', (status,))
    return cursor.fetchall()

# Chatbot logic
def chatbot():
    conn = connect_to_database()
    print("Welcome to the Maritime Chatbot! Type 'exit' to quit.")
    
    while True:
        # Get user input
        user_input = input("\nAsk a question: ").strip().lower()
        
        if user_input == "exit":
            print("Goodbye!")
            break
        
        # Handle different intents
        if "find vessel" in user_input:
            vessel_name = input("Enter the vessel name: ").strip()
            result = find_vessel_by_name(conn, vessel_name)
            print("Vessel details:", result if result else "No vessel found.")
        
        elif "vessels by flag" in user_input:
            flag = input("Enter the flag: ").strip()
            result = get_vessels_by_flag(conn, flag)
            print("Vessels with flag:", result if result else "No vessels found.")
        
        elif "vessels by status" in user_input:
            status = input("Enter the status (e.g., 'In Transit', 'Docked'): ").strip()
            result = get_vessels_by_status(conn, status)
            print("Vessels with status:", result if result else "No vessels found.")
        
        else:
            print("I didn't understand that. Try asking about vessels by name, flag, or status.")
    
    conn.close()

# Run the chatbot
if __name__ == "__main__":
    chatbot()
