import sqlite3
import pandas as pd

# Function to set up the SQLite database and table
def setup_database(db_name="maritime_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vessels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vessel_name TEXT,
            vessel_type TEXT,
            owner TEXT,
            flag TEXT,
            speed_knots REAL,
            dimensions TEXT,
            visited_ports TEXT,
            last_known_position TEXT,
            status TEXT,
            mmsi INTEGER
        )
    ''')
    conn.commit()
    return conn

# Function to insert data into the database
def insert_data(conn, dataframe):
    cursor = conn.cursor()
    for _, row in dataframe.iterrows():
        cursor.execute('''
            INSERT INTO vessels (
                vessel_name, vessel_type, owner, flag, speed_knots,
                dimensions, visited_ports, last_known_position, status, mmsi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['Vessel_Name'], row['Vessel_Type'], row['Owner'], row['Flag'],
            row['Speed_knots'], row['Dimensions_m'], 
            row['Visited_Ports'], row['Last_Known_Position'], 
            row['Status'], row['MMSI']
        ))
    conn.commit()

# Main script to execute the loading process
if __name__ == "__main__":
    # Specify the CSV file path
    file_path = "Maritime_Example_Dataset.csv"
    
    # Load the CSV dataset
    try:
        dataset = pd.read_csv(file_path)
        print("Dataset loaded successfully.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        exit()
    
    # Set up the database
    conn = setup_database()
    print("Database setup complete.")
    
    # Insert data into the database
    insert_data(conn, dataset)
    print("Data inserted into the database.")
    
    # Close the database connection
    conn.close()
    print("Database connection closed.")
