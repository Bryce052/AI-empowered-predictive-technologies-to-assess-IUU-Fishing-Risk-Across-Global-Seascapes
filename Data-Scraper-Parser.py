# install required libraries - requests pandas sqlalchemy psycopg2 

import requests
import pandas as pd
from sqlalchemy import create_engine
import os

# Step 1: Define GFW Data Fetcher
def fetch_gfw_data(url, local_file="vessel_data.csv"):
    """
    Fetch data from Global Fishing Watch and save locally.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for failed requests
    with open(local_file, "wb") as f:
        f.write(response.content)
    print(f"Data downloaded and saved to {local_file}")
    return local_file

# Step 2: Parse and Validate Data
def parse_vessel_data(file_path):
    """
    Parse the downloaded vessel data CSV into a structured format.
    """
    try:
        # Load CSV into Pandas DataFrame
        df = pd.read_csv(file_path)
        # Select and rename columns for clarity
        df = df.rename(columns={
            "id": "vessel_id",
            "name": "vessel_name",
            "lat": "latitude",
            "lon": "longitude",
            "time": "timestamp"
        })
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # Drop rows with invalid/missing data
        df = df.dropna(subset=['vessel_id', 'latitude', 'longitude', 'timestamp'])
        print(f"Parsed {len(df)} valid records.")
        return df
    except Exception as e:
        print(f"Error parsing data: {e}")
        return pd.DataFrame()

# Step 3: Load Data into PostgreSQL
def load_data_to_db(df, db_url, table_name="vessel_positions"):
    """
    Load the structured vessel data into a PostgreSQL database.
    """
    try:
        # Connect to the database
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Write DataFrame to SQL table
            df.to_sql(table_name, con=conn, if_exists='append', index=False)
            print(f"Loaded {len(df)} records into {table_name} table.")
    except Exception as e:
        print(f"Error loading data into database: {e}")

# Main Script
if __name__ == "__main__":
    # Configuration
    GFW_DATA_URL = "https://globalfishingwatch.org/sample-data.csv"  # Replace with actual URL
    LOCAL_FILE = "vessel_data.csv"
    DATABASE_URL = "postgresql://user:password@localhost/maritime_db"
    
    # Step 1: Fetch Data
    local_file_path = fetch_gfw_data(GFW_DATA_URL, LOCAL_FILE)
    
    # Step 2: Parse Data
    vessel_df = parse_vessel_data(local_file_path)
    
    # Step 3: Load into Database
    if not vessel_df.empty:
        load_data_to_db(vessel_df, DATABASE_URL)
    else:
        print("No valid data to load.")
