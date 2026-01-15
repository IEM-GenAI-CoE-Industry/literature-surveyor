import os
from pathlib import Path
import requests
import pandas as pd
import time
from dotenv import load_dotenv

# --- Configuration & Setup ---

# 1. Locate and Load .env file
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print("Warning: .env file not found.")

# 2. Get Environment Variables
EMAIL = os.getenv("EMAIL")
OPENALEX_API_URL = "https://api.openalex.org/works"

# --- Core Functions ---

def search_openalex(topic, num_results=20):
    print(f"\n Searching OpenAlex for topic: '{topic}'...")
    
    params = {
        'search': topic,
        'per-page': num_results, 
        'mailto': EMAIL 
    }

    try:
        start_time = time.time()
        response = requests.get(OPENALEX_API_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            elapsed = time.time() - start_time
            print(f" Found {len(results)} works in {elapsed:.2f} seconds.")
            return process_results(results)
        else:
            print(f"Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def process_results(results):
    papers = []
    
    for work in results:
        # Authors
        authorships = work.get('authorships', [])
        authors = [a['author']['display_name'] for a in authorships]
        author_str = ", ".join(authors[:2]) # Keep strictly short
        if len(authors) > 2:
            author_str += " et al."
        
        # Venue extraction (Critical for your requirement)
        primary_loc = work.get('primary_location') or {}
        source = primary_loc.get('source') or {}
        venue = source.get('display_name', 'Unknown Venue')
        
        # Type (Journal, Conference, etc.)
        venue_type = source.get('type', 'Unknown').title()
        
        papers.append({
            'Title': work.get('display_name', 'No Title'),
            'Venue': venue,             # <--- The Focus
            'Type': venue_type,         # <--- Helpful metadata
            'Year': work.get('publication_year', 'N/A'),
            'Cited By': work.get('cited_by_count', 0),
            'Authors': author_str
        })
        
    return pd.DataFrame(papers)

# --- Main Execution ---
if __name__ == "__main__":
    # Settings to de-clutter the output
    pd.set_option('display.max_colwidth', 30) # Cut off long titles
    pd.set_option('display.expand_frame_repr', False) # Don't wrap rows
    pd.set_option('display.max_columns', 5)

    print("\n--- OpenAlex Venue Discovery ---")
    TOPIC = input("Enter research topic: ").strip()
    
    if TOPIC:
        df = search_openalex(TOPIC, num_results=15)
        
        if df is not None and not df.empty:
            
            # 1. Output the Summary of Venues (Requirement: Venue Discovery)
            print("\n" + "="*50)
            print("   DISCOVERED VENUES (Conferences & Journals)")
            print("="*50)
            
            # Count how many papers came from each venue
            venue_counts = df.groupby(['Venue', 'Type']).size().reset_index(name='Paper Count')
            # Remove 'Unknown Venue' for cleaner list
            venue_counts = venue_counts[venue_counts['Venue'] != 'Unknown Venue']
            
            # Display clearly
            print(venue_counts.to_string(index=False))
            
            # 2. Output the detailed list (Less cluttered now)
            print("\n" + "-"*50)
            print("  RELEVANT PAPERS")
            print("-"*50)
            # Rearranged columns to put Venue first
            cols = ['Venue', 'Year', 'Title', 'Cited By']
            print(df[cols].head(10).to_string(index=False))
            
            # Save
            safe_topic = "".join([c for c in TOPIC if c.isalnum()]).strip()
            output_file = script_dir / f"venues_{safe_topic}.csv"
            df.to_csv(output_file, index=False)
            print(f"\n Saved detailed data to: {output_file}")
            
        else:
            print("No results found.")
    else:
        print("Please enter a topic.")