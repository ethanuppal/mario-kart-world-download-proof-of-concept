#!/usr/bin/env python3

import os
import re
import requests
from urllib.parse import unquote
from pathlib import Path

def fetch_expected_songs():
    """Fetch the expected song list from the website"""
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
            songs.append(song_name)
        
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

def verify_downloads():
    """Verify all songs were downloaded correctly"""
    print("🔍 Verifying Mario Kart World Music Downloads")
    print("=" * 50)
    
    # Get expected songs
    print("\nFetching expected song list from website...")
    expected_songs = fetch_expected_songs()
    
    if not expected_songs:
        print("❌ Failed to fetch expected song list")
        return
    
    print(f"✅ Found {len(expected_songs)} expected songs on website")
    
    # Get downloaded files
    download_dir = Path('mkw_music_brstm')
    if not download_dir.exists():
        print(f"❌ Download directory '{download_dir}' not found")
        return
    
    downloaded_files = list(download_dir.glob('*.brstm'))
    print(f"\n✅ Found {len(downloaded_files)} BRSTM files in {download_dir}")
    
    # Create sets for comparison
    expected_set = {f"{sanitize_filename(song)}.brstm" for song in expected_songs}
    downloaded_set = {f.name for f in downloaded_files}
    
    # Find missing and extra files
    missing = expected_set - downloaded_set
    extra = downloaded_set - expected_set
    
    print("\n📊 Verification Results:")
    print(f"Expected songs: {len(expected_songs)}")
    print(f"Downloaded files: {len(downloaded_files)}")
    
    if len(expected_songs) == len(downloaded_files) == 267:
        print("\n✅ COUNT VERIFICATION: PASSED - Exactly 267 songs downloaded (excluding fan remixes)!")
    else:
        print(f"\n❌ COUNT VERIFICATION: FAILED - Expected 267, got {len(downloaded_files)}")
    
    if missing:
        print(f"\n⚠️  Missing files ({len(missing)}):")
        for f in sorted(missing)[:10]:  # Show first 10
            print(f"  - {f}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    
    if extra:
        print(f"\n⚠️  Extra files ({len(extra)}):")
        for f in sorted(extra)[:10]:  # Show first 10
            print(f"  - {f}")
        if len(extra) > 10:
            print(f"  ... and {len(extra) - 10} more")
    
    if not missing and not extra:
        print("\n✅ FILE MATCHING: PASSED - All expected files present, no extras!")
    
    # File size check
    print("\n📏 File Size Analysis:")
    sizes = [f.stat().st_size for f in downloaded_files]
    total_size = sum(sizes)
    avg_size = total_size / len(sizes) if sizes else 0
    min_size = min(sizes) if sizes else 0
    max_size = max(sizes) if sizes else 0
    
    print(f"Total size: {total_size / (1024*1024*1024):.2f} GB")
    print(f"Average file size: {avg_size / (1024*1024):.2f} MB")
    print(f"Smallest file: {min_size / (1024*1024):.2f} MB")
    print(f"Largest file: {max_size / (1024*1024):.2f} MB")
    
    # Check for suspiciously small files (might be error pages)
    small_files = [f for f in downloaded_files if f.stat().st_size < 100000]  # < 100KB
    if small_files:
        print(f"\n⚠️  Suspiciously small files ({len(small_files)}):")
        for f in small_files[:5]:
            print(f"  - {f.name}: {f.stat().st_size / 1024:.1f} KB")
    
    # Final verdict
    print("\n" + "=" * 50)
    if len(downloaded_files) == 267 and not missing and not extra and not small_files:
        print("✅ FINAL VERDICT: ALL CHECKS PASSED! 🎉")
        print("All 267 Mario Kart World songs downloaded successfully (excluding fan remixes)!")
    else:
        print("⚠️  FINAL VERDICT: Some issues detected")
        if len(downloaded_files) != 267:
            print(f"  - Wrong count: {len(downloaded_files)} instead of 267")
        if missing:
            print(f"  - Missing files: {len(missing)}")
        if extra:
            print(f"  - Extra files: {len(extra)}")
        if small_files:
            print(f"  - Suspiciously small files: {len(small_files)}")

if __name__ == "__main__":
    verify_downloads()
