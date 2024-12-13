# install packages - pip install requests beautifulsoup4 pandas

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 1: Define the crawler
def search_vessel_by_mmsi(mmsi):
    """
    Search vessel information by MMSI on a target website.
    """
    base_url = f"https://www.vesselfinder.com/vessels?name={mmsi}"  # Example site
    response = requests.get(base_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for MMSI {mmsi}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract vessel information (update selectors based on target website)
    try:
        name = soup.find('h1', class_='vessel-name').text.strip()
        flag = soup.find('span', class_='flag').text.strip()
        type_ = soup.find('div', text='Type:').find_next('div').text.strip()
        position = soup.find('div', text='Current Position:').find_next('div').text.strip()
        
        return {
            "MMSI": mmsi,
            "Name": name,
            "Flag": flag,
            "Type": type_,
            "Position": position
        }
    except Exception as e:
        print(f"Error parsing data for MMSI {mmsi}: {e}")
        return None

# Step 2: Crawl for multiple MMSI
def crawl_vessels(mmsi_list):
    """
    Crawl multiple vessels and save the data.
    """
    data = []
    for mmsi in mmsi_list:
        print(f"Searching for MMSI: {mmsi}")
        result = search_vessel_by_mmsi(mmsi)
        if result:
            data.append(result)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv("vessel_data.csv", index=False)
    print("Crawling complete. Data saved to vessel_data.csv.")

# Step 3: Example usage
if __name__ == "__main__":
    mmsi_list = ["211331640", "636091308"]  # Replace with your MMSI numbers
    crawl_vessels(mmsi_list)
