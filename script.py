import json
import re
import time
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

#logging configuration
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO,  
)

def scrape_complaints():
    """Main function to scrape NYC 311 complaints from the portal"""
    
    # Configure Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    
    # Initializing the Chrome driver with configured options
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logging.info("Checking for complaints...")
        driver.get("https://portal.311.nyc.gov/check-status/")
        
        # Waiting for complaints to load (max 20 seconds)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "entitypinmap-list-box-item"))
        )
        
        # Getting all complaint elements from the page
        complaints_list = driver.find_elements(By.CLASS_NAME, "entitypinmap-list-box-item")
        
        # Regular expression to parse complaint labels (format: "Category - Address, Zipcode")
        pattern = re.compile(r"^(.*?)\s*-\s*(.*?),\s*(\d{5})$")
        
        # Processing each complaint and extract relevant information
        current_complaints = []
        for complaint in complaints_list:
            label = complaint.get_attribute("aria-label")
            match = pattern.match(label)
            if match:
                category = match.group(1)  # Extracting complaint category
                zipcode = match.group(3)   # Extracting ZIP code
                
                current_complaints.append({
                    "category": category,
                    "zip": zipcode
                })
            else:
                logging.info(f" No match found for: {label}")
        
        # Loading previously stored complaints for comparison
        previous_complaints = read_previous_complaints()
        
        # Identify new complaints by comparing with previous data
        new_complaints = []
        for complaint in current_complaints:
            if complaint not in previous_complaints:
                new_complaints.append(complaint)
        
        # Saving current complaints to file
        if new_complaints:
            with open("data.json", "w") as json_file:
                json.dump(current_complaints, json_file, indent=4)
        
        # Log results    
        if not new_complaints:
            logging.info("No new complaints found")
        else:
            logging.info("New complaints found!")
            
    except Exception as e:
        logging.error(f" Error occurred: {str(e)}")
    finally:

        driver.quit()

def read_previous_complaints(file_path="data.json"):
    """
    Reads the previous complaints from the JSON file.
    Args:
        file_path (str): Path to the JSON file containing previous complaints
    Returns:
        list: List of previous complaints or empty list if file doesn't exist
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error reading previous data file: {str(e)}")
    return []


def main():
    """Main execution loop that runs the scraper every 10 minutes"""
    while True:
        scrape_complaints()
        logging.info("Waiting 10 minutes before next check...")
        time.sleep(600)  # Sleep for 10 minutes


if __name__ == "__main__":
    logging.info("Starting NYC 311 complaint monitor...")
    main()