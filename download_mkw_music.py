#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import tarfile
import zipfile
import requests
from pathlib import Path
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_vgmstream_cli():
    """Download the latest vgmstream-cli for macOS"""
    print("Fetching latest vgmstream release info...")
    
    # Try the automated builds first
    download_url = "https://vgmstream.org/downloads/vgmstream-mac-cli.tar.gz"
    filename = "vgmstream-mac-cli.tar.gz"
    
    try:
        # Test if the URL is valid
        response = requests.head(download_url)
        if response.status_code != 200:
            # Fallback to GitHub releases
            print("Automated builds not available, checking GitHub releases...")
            api_url = "https://api.github.com/repos/vgmstream/vgmstream/releases/latest"
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            macos_asset = None
            for asset in data['assets']:
                if 'mac' in asset['name'].lower() and 'cli' in asset['name'].lower():
                    macos_asset = asset
                    break
            
            if not macos_asset:
                print("ERROR: Could not find macOS CLI build")
                return None
                
            download_url = macos_asset['browser_download_url']
            filename = macos_asset['name']
        
        print(f"Downloading {filename}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print("\nExtracting vgmstream-cli...")
        if filename.endswith('.tar.gz'):
            with tarfile.open(filename, 'r:gz') as tar_ref:
                tar_ref.extractall('vgmstream')
        elif filename.endswith('.zip'):
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall('vgmstream')
        else:
            print(f"ERROR: Unknown archive format: {filename}")
            return None
        
        os.remove(filename)
        
        vgmstream_path = Path('vgmstream/vgmstream-cli')
        if vgmstream_path.exists():
            os.chmod(vgmstream_path, 0o755)
            print(f"vgmstream-cli extracted to: {vgmstream_path.absolute()}")
            return str(vgmstream_path.absolute())
        else:
            print("ERROR: vgmstream-cli not found in extracted files")
            return None
            
    except Exception as e:
        print(f"Error downloading vgmstream: {e}")
        return None

def fetch_song_data():
    """Fetch and parse the Mario Kart World page to extract song information"""
    print("\nFetching Mario Kart World song list...")
    
    url = "https://smashcustommusic.net/game/5609"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        
        # Split the page to exclude the "Remixes / Fanmade" section
        main_songs_section = html.split("Remixes / Fanmade")[0] if "Remixes / Fanmade" in html else html
        
        song_pattern = r'<tr id="s(\d+)">\s*<td[^>]*><a href="/song/\d+">([^<]+)</a>'
        matches = re.findall(song_pattern, main_songs_section)
        
        songs = []
        for song_id, song_name in matches:
            song_name = unquote(song_name.replace('&#039;', "'").replace('&amp;', '&'))
            songs.append({
                'id': song_id,
                'name': song_name,
                'url': f"https://smashcustommusic.net/brstm/{song_id}"
            })
        
        print(f"Found {len(songs)} songs (excluding fan remixes)")
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

def download_song(song, output_dir, session):
    """Download a single BRSTM file"""
    try:
        filename = f"{sanitize_filename(song['name'])}.brstm"
        filepath = output_dir / filename
        
        if filepath.exists():
            return f"Skipped (already exists): {song['name']}"
        
        # Step 1: Visit the song page first (required for bot protection)
        song_page_url = f"https://smashcustommusic.net/song/{song['id']}"
        
        # Add referrer from the main game page
        session.headers['Referer'] = 'https://smashcustommusic.net/game/5609'
        
        response = session.get(song_page_url, timeout=30)
        response.raise_for_status()
        
        # Random delay between 1-3 seconds to appear more human-like
        import random
        time.sleep(random.uniform(1.0, 3.0))
        
        # Step 2: Now download the BRSTM file with the song page as referrer
        session.headers['Referer'] = song_page_url
        
        response = session.get(song['url'], stream=True, timeout=30)
        response.raise_for_status()
        
        # Check if we got an HTML error page instead of the file
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            # Read a bit of the response to check for error
            error_check = response.content[:500].decode('utf-8', errors='ignore')
            if 'unusual activity' in error_check or 'robot' in error_check:
                return f"Failed: {song['name']} - Bot protection triggered"
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify the file isn't an error page
        if filepath.stat().st_size < 1000:  # BRSTM files are typically larger
            with open(filepath, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                if 'html' in content.lower():
                    filepath.unlink()  # Delete the error file
                    return f"Failed: {song['name']} - Got error page instead of file"
        
        return f"Downloaded: {song['name']}"
        
    except Exception as e:
        return f"Failed: {song['name']} - {str(e)}"

def download_all_songs(songs, max_workers=1):
    """Download all BRSTM files with progress tracking"""
    output_dir = Path('mkw_music_brstm')
    output_dir.mkdir(exist_ok=True)
    
    print(f"\nDownloading {len(songs)} BRSTM files to {output_dir.absolute()}")
    print(f"Using {max_workers} concurrent download(s)")
    print("Note: Downloads are rate-limited to avoid triggering bot protection")
    print("This will take a while with 1-3 second delays between each download\n")
    
    session = requests.Session()
    # Add browser-like headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_song = {executor.submit(download_song, song, output_dir, session): song 
                          for song in songs}
        
        for future in as_completed(future_to_song):
            result = future.result()
            completed += 1
            
            if "Failed" in result:
                failed += 1
                print(f"[{completed}/{len(songs)}] ❌ {result}")
            elif "Skipped" in result:
                print(f"[{completed}/{len(songs)}] ⏭️  {result}")
            else:
                print(f"[{completed}/{len(songs)}] ✅ {result}")
    
    print(f"\n{'='*50}")
    print(f"Download complete!")
    print(f"Total songs: {len(songs)}")
    print(f"Downloaded: {completed - failed}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir.absolute()}")

def create_conversion_script(vgmstream_path):
    """Create a helper script to convert BRSTM files to FLAC/WAV"""
    script_content = f"""#!/bin/bash

VGMSTREAM="{vgmstream_path}"
INPUT_DIR="mkw_music_brstm"
OUTPUT_DIR="mkw_music_flac"

if [ ! -f "$VGMSTREAM" ]; then
    echo "Error: vgmstream-cli not found at $VGMSTREAM"
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory $INPUT_DIR not found"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Converting BRSTM files to FLAC..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

count=0
total=$(find "$INPUT_DIR" -name "*.brstm" | wc -l | tr -d ' ')

for brstm in "$INPUT_DIR"/*.brstm; do
    if [ -f "$brstm" ]; then
        basename=$(basename "$brstm" .brstm)
        output="$OUTPUT_DIR/$basename.flac"
        
        if [ ! -f "$output" ]; then
            count=$((count + 1))
            echo "[$count/$total] Converting: $basename"
            "$VGMSTREAM" -o "$output" "$brstm" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo "[$count/$total] ✅ Converted: $basename"
            else
                echo "[$count/$total] ❌ Failed: $basename"
            fi
        else
            count=$((count + 1))
            echo "[$count/$total] ⏭️  Skipped (exists): $basename"
        fi
    fi
done

echo ""
echo "Conversion complete!"
echo "FLAC files saved to: $OUTPUT_DIR"
"""

    script_path = Path('convert_to_flac.sh')
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"\nCreated conversion script: {script_path.absolute()}")
    print("Run './convert_to_flac.sh' to convert BRSTM files to FLAC")

def main():
    print("Mario Kart World Music Downloader")
    print("="*50)
    
    vgmstream_path = download_vgmstream_cli()
    if not vgmstream_path:
        print("\nFailed to download vgmstream-cli. Exiting.")
        sys.exit(1)
    
    songs = fetch_song_data()
    if not songs:
        print("\nFailed to fetch song data. Exiting.")
        sys.exit(1)
    
    print("\nReady to download. This will download approximately 267 BRSTM files (excluding fan remixes).")
    print("Continue? (y/n): ", end='')
    
    if input().lower() != 'y':
        print("Download cancelled.")
        sys.exit(0)
    
    download_all_songs(songs)
    
    create_conversion_script(vgmstream_path)
    
    print("\n✨ All done! ✨")
    print("\nNext steps:")
    print("1. BRSTM files are in: mkw_music_brstm/")
    print("2. To convert to FLAC, run: ./convert_to_flac.sh")
    print("3. To convert to WAV instead, edit convert_to_flac.sh and change .flac to .wav")
    
    print("\n⚠️  Note about bot protection:")
    print("If downloads are failing due to bot protection, you may need to:")
    print("- Use a VPN or different network")
    print("- Manually download files from https://smashcustommusic.net/game/5609")
    print("- Try running the script at different times")

if __name__ == "__main__":
    main()
