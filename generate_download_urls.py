#!/usr/bin/env python3

import re
import requests
from urllib.parse import unquote

def fetch_song_data():
    """Fetch and parse the Mario Kart World page to extract song information"""
    print("Fetching Mario Kart World song list...")
    
    url = "https://smashcustommusic.net/game/5609"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        
        song_pattern = r'<tr id="s(\d+)">\s*<td[^>]*><a href="/song/\d+">([^<]+)</a>'
        matches = re.findall(song_pattern, html)
        
        songs = []
        for song_id, song_name in matches:
            song_name = unquote(song_name.replace('&#039;', "'").replace('&amp;', '&'))
            songs.append({
                'id': song_id,
                'name': song_name,
                'page_url': f"https://smashcustommusic.net/song/{song_id}",
                'download_url': f"https://smashcustommusic.net/brstm/{song_id}"
            })
        
        print(f"Found {len(songs)} songs")
        return songs
        
    except Exception as e:
        print(f"Error fetching song data: {e}")
        return []

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def main():
    print("Mario Kart World Music URL Generator")
    print("="*50)
    print()
    
    songs = fetch_song_data()
    if not songs:
        print("Failed to fetch song data.")
        return
    
    # Generate URL list file
    with open('mkw_urls.txt', 'w') as f:
        for song in songs:
            f.write(f"{song['download_url']}\n")
    
    # Generate wget script
    with open('download_with_wget.sh', 'w') as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Mario Kart World Music Download Script using wget\n")
        f.write("# This script downloads files one by one with delays\n\n")
        f.write("mkdir -p mkw_music_brstm\n")
        f.write("cd mkw_music_brstm\n\n")
        
        for song in songs:
            filename = f"{sanitize_filename(song['name'])}.brstm"
            f.write(f"# {song['name']}\n")
            f.write(f"echo \"Downloading: {song['name']}\"\n")
            f.write(f"wget -O \"{filename}\" --referer=\"{song['page_url']}\" ")
            f.write(f"--user-agent=\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36\" ")
            f.write(f"\"{song['download_url']}\"\n")
            f.write("sleep 2\n\n")
    
    # Generate aria2c input file
    with open('mkw_aria2_input.txt', 'w') as f:
        for song in songs:
            filename = f"{sanitize_filename(song['name'])}.brstm"
            f.write(f"{song['download_url']}\n")
            f.write(f"  out={filename}\n")
            f.write(f"  referer={song['page_url']}\n")
    
    # Make wget script executable
    import os
    os.chmod('download_with_wget.sh', 0o755)
    
    print("\n✅ Generated download files:")
    print("- mkw_urls.txt: Simple URL list")
    print("- download_with_wget.sh: Bash script using wget with delays")
    print("- mkw_aria2_input.txt: Input file for aria2c")
    
    print("\n📥 How to use:")
    print("\n1. With wget (recommended for bot protection):")
    print("   ./download_with_wget.sh")
    
    print("\n2. With aria2c (faster but might trigger bot protection):")
    print("   aria2c -i mkw_aria2_input.txt -d mkw_music_brstm --max-concurrent-downloads=1")
    
    print("\n3. With curl (manual, one file at a time):")
    print("   Example: curl -o output.brstm --referer 'https://smashcustommusic.net/song/115501' 'https://smashcustommusic.net/brstm/115501'")
    
    print("\n⚠️  Important:")
    print("- The wget script includes 2-second delays between downloads")
    print("- If you get bot protection errors, try:")
    print("  - Using a VPN")
    print("  - Increasing delays in the script")
    print("  - Downloading in smaller batches")

if __name__ == "__main__":
    main()
