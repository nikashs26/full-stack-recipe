#!/usr/bin/env python3
"""
Simple health check script for Railway deployment
Run this to test if your backend is working
"""

import requests
import sys
import os

def check_health(railway_url):
    """Check if Railway backend is healthy"""
    try:
        # Test health endpoint
        health_url = f"{railway_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Backend is healthy!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to backend: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    # Get Railway URL from environment or command line
    railway_url = os.environ.get('RAILWAY_URL')
    
    if not railway_url:
        if len(sys.argv) > 1:
            railway_url = sys.argv[1]
        else:
            print("Usage: python health_check.py <railway_url>")
            print("Or set RAILWAY_URL environment variable")
            sys.exit(1)
    
    # Remove trailing slash if present
    railway_url = railway_url.rstrip('/')
    
    print(f"🔍 Checking Railway backend at: {railway_url}")
    
    if check_health(railway_url):
        print("🎉 Your Railway backend is working correctly!")
        sys.exit(0)
    else:
        print("💥 Your Railway backend has issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()
