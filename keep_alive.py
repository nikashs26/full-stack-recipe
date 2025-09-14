#!/usr/bin/env python3
"""
Keep Alive Script for Render Free Tier
Pings your Render backend every few minutes to prevent it from sleeping
"""

import requests
import time
import schedule
import logging
from datetime import datetime

# Configuration
BACKEND_URL = "https://dietary-delight.onrender.com"
PING_INTERVAL_MINUTES = 5  # Ping every 5 minutes
HEALTH_ENDPOINT = "/api/health"
RECIPE_COUNT_ENDPOINT = "/api/recipe-counts"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keep_alive.log'),
        logging.StreamHandler()
    ]
)

def ping_backend():
    """Ping the backend to keep it alive"""
    try:
        # Try health endpoint first
        health_url = f"{BACKEND_URL}{HEALTH_ENDPOINT}"
        response = requests.get(health_url, timeout=30)
        
        if response.status_code == 200:
            logging.info(f"✅ Health check successful - Status: {response.status_code}")
            
            # Also check recipe count to ensure it's working
            try:
                count_url = f"{BACKEND_URL}{RECIPE_COUNT_ENDPOINT}"
                count_response = requests.get(count_url, timeout=30)
                if count_response.status_code == 200:
                    count_data = count_response.json()
                    total_recipes = count_data.get('data', {}).get('total', 0)
                    logging.info(f"📊 Recipe count: {total_recipes}")
                else:
                    logging.warning(f"⚠️ Recipe count check failed - Status: {count_response.status_code}")
            except Exception as e:
                logging.warning(f"⚠️ Recipe count check error: {e}")
                
        else:
            logging.warning(f"⚠️ Health check failed - Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.error("❌ Request timed out - Backend might be sleeping")
    except requests.exceptions.ConnectionError:
        logging.error("❌ Connection error - Backend might be down")
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")

def main():
    """Main function to run the keep-alive service"""
    logging.info("🚀 Starting Keep-Alive service for Render backend")
    logging.info(f"📍 Backend URL: {BACKEND_URL}")
    logging.info(f"⏰ Ping interval: {PING_INTERVAL_MINUTES} minutes")
    
    # Schedule the ping job
    schedule.every(PING_INTERVAL_MINUTES).minutes.do(ping_backend)
    
    # Do an initial ping
    logging.info("🔄 Performing initial ping...")
    ping_backend()
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled jobs
        except KeyboardInterrupt:
            logging.info("🛑 Keep-alive service stopped by user")
            break
        except Exception as e:
            logging.error(f"❌ Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
