#!/usr/bin/env python3
"""
Test script to validate the complete frontend authentication flow.
This simulates what the frontend does step-by-step.
"""

import requests
import json
import pyotp
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/auth"
TEST_USER = {
    "username": "roykoigu",
    "password": "Koigu@1998"
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_login_without_mfa():
    """Test 1: Login without MFA token (should fail if MFA enabled)"""
    print_section("TEST 1: Login WITHOUT MFA Token")
    
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            data = response.json()
            if "MFA token required" in data.get("detail", ""):
                print("✅ Correctly requires MFA token")
                return True
        elif response.status_code == 200:
            print("⚠️  WARNING: Login succeeded without MFA - MFA not enforced!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_current_totp_token(secret):
    """Generate current TOTP token from secret"""
    totp = pyotp.TOTP(secret)
    return totp.now()

def test_login_with_mfa():
    """Test 2: Login with MFA token"""
    print_section("TEST 2: Login WITH MFA Token")
    
    # First, we need the MFA secret for roykoigu
    print("⚠️  NOTE: We need the MFA secret to generate valid TOTP codes")
    print("Please enter the MFA secret for roykoigu user:")
    print("(You can get this from the database or from when the user set up MFA)")
    
    secret = input("MFA Secret: ").strip()
    
    if not secret:
        print("❌ No secret provided, skipping test")
        return False
    
    # Generate current TOTP token
    totp_token = get_current_totp_token(secret)
    print(f"\n🔑 Generated TOTP Token: {totp_token}")
    print(f"📅 Current Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Attempt login
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "mfa_token": totp_token
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Login successful with MFA!")
                print(f"🎫 Access Token: {data['access_token'][:50]}...")
                return True, data["access_token"]
        else:
            print(f"❌ Login failed: {response.json().get('detail')}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_access_protected_route(access_token):
    """Test 3: Access protected route with token"""
    print_section("TEST 3: Access Protected Route (Dashboard)")
    
    try:
        response = requests.get(
            "http://localhost:8000/api/protected/dashboard",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print("✅ Successfully accessed protected route")
            return True
        else:
            print(f"Response: {response.text}")
            print("❌ Failed to access protected route")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_api_format():
    """Test 4: Exactly mimic frontend request format"""
    print_section("TEST 4: Mimic Exact Frontend Request Format")
    
    print("Testing with hardcoded token from your Postman screenshot...")
    
    # Use the exact format that frontend sends
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            data=json.dumps({
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "mfa_token": "703934"  # From Postman screenshot
            }),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login format is correct")
        elif response.status_code == 401:
            print("⚠️  Token expired (TOTP codes are valid for 30 seconds)")
        else:
            print(f"❌ Unexpected response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_backend_health():
    """Check if backend is running"""
    print_section("BACKEND HEALTH CHECK")
    
    try:
        response = requests.get("http://localhost:8000/api/auth/login", timeout=2)
        print(f"✅ Backend is running (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend is NOT running on port 8000")
        return False
    except Exception as e:
        print(f"⚠️  Backend check error: {e}")
        return False

def main():
    print("\n" + "🔐" * 30)
    print("  MFA Token Authenticator - Frontend Flow Test")
    print("🔐" * 30)
    
    # Check backend
    if not check_backend_health():
        print("\n❌ Please start the backend server first:")
        print("   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Test 1: Login without MFA
    test_login_without_mfa()
    
    # Test 4: Test exact frontend format
    test_frontend_api_format()
    
    # Test 2: Login with MFA (interactive)
    print("\n" + "⚠️ " * 20)
    print("The next test requires the MFA secret from the database.")
    print("Do you want to continue with MFA secret test? (y/n): ", end="")
    
    if input().strip().lower() == 'y':
        success, token = test_login_with_mfa()
        
        if success and token:
            # Test 3: Access protected route
            test_access_protected_route(token)
    
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print("✅ = Test passed")
    print("❌ = Test failed")
    print("⚠️  = Warning/Info")
    print("\nIf login works in Postman but not frontend, check:")
    print("1. TOTP tokens expire every 30 seconds - enter code quickly")
    print("2. Frontend console for exact error messages")
    print("3. Network tab to see exact request/response")
    print("4. Make sure frontend is using correct API_BASE URL")

if __name__ == "__main__":
    main()
