import sys
import os
import logging

# --- Setup Logging to see the output ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Logic to import from venue_discovery ---
# This script simulates the "Main Service" calling the helper module
try:
    from venue_discovery.service import discover_venues
except ImportError as e:
    print(f" Import Error: {e}")
    print("Make sure this script is in the 'backend' folder and 'venue_discovery' is a subfolder with an __init__.py file.")
    sys.exit(1)

# --- Test Execution ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  PHASE 3 TEST: ACADEMIC VENUE DISCOVERY")
    print("="*50)
    
    # 1. Get User Input (Simulating Step 1 & 2)
    domain = input("Enter research domain (e.g., 'Generative AI'): ").strip() or "Generative AI"
    
    # 2. Call the Service (Simulating Step 3)
    print(f"\n[Service] Discovering venues for: '{domain}'...")
    results = discover_venues(domain)
    
    # 3. Display Results (Simulating Step 7 output)
    print("\n" + "-"*50)
    print("  DISCOVERY RESULTS")
    print("-" * 50)
    
    conferences = results.get("conferences", [])
    journals = results.get("journals", [])
    
    if conferences:
        print(f"\n Conferences ({len(conferences)}):")
        for conf in conferences:
            print(f"  • {conf}")
    else:
        print("\n  Conferences: None found.")

    if journals:
        print(f"\n Journals ({len(journals)}):")
        for jour in journals:
            print(f"  • {jour}")
    else:
        print("\n Journals: None found.")
        
    print("\n" + "="*50)