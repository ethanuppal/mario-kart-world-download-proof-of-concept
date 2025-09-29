#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import time

VGMSTREAM = "/Users/ethan/sandbox/marioworld/vgmstream/vgmstream-cli"
INPUT_DIR = "mkw_music_brstm"
OUTPUT_DIR = "mkw_music_alac"

def check_dependencies():
    if not Path(VGMSTREAM).exists():
        print(f"Error: vgmstream-cli not found at {VGMSTREAM}")
        sys.exit(1)
    
    if not Path(INPUT_DIR).exists():
        print(f"Error: Input directory {INPUT_DIR} not found")
        sys.exit(1)
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except:
        print("Error: ffmpeg not found. Please install ffmpeg for ALAC conversion.")
        print("Install with: brew install ffmpeg")
        sys.exit(1)

def convert_file(brstm_path, output_path, file_index, total_files):
    basename = brstm_path.stem
    temp_wav = output_path.with_suffix('.wav')
    
    try:
        subprocess.run(
            [VGMSTREAM, "-o", str(temp_wav), str(brstm_path)],
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        subprocess.run(
            ["ffmpeg", "-i", str(temp_wav), "-c:a", "alac", "-y", str(output_path)],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=True
        )
        
        temp_wav.unlink()
        
        return f"[{file_index}/{total_files}] ✅ Converted: {basename}"
    
    except subprocess.CalledProcessError:
        if temp_wav.exists():
            temp_wav.unlink()
        return f"[{file_index}/{total_files}] ❌ Failed: {basename}"

def convert_files_parallel():
    check_dependencies()
    
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    brstm_files = list(Path(INPUT_DIR).glob("*.brstm"))
    if not brstm_files:
        print(f"No BRSTM files found in {INPUT_DIR}")
        return
    
    print("Converting BRSTM files to ALAC...")
    print(f"Input: {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Using {cpu_count()} parallel workers")
    print()
    
    tasks = []
    total_files = len(brstm_files)
    file_index = 0
    
    for brstm_path in brstm_files:
        output_path = Path(OUTPUT_DIR) / f"{brstm_path.stem}.m4a"
        
        if output_path.exists():
            file_index += 1
            print(f"[{file_index}/{total_files}] ⏭️  Skipped (exists): {brstm_path.stem}")
        else:
            tasks.append((brstm_path, output_path))
    
    if not tasks:
        print("\nAll files already converted!")
        return
    
    start_time = time.time()
    completed = file_index
    
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = {}
        
        for idx, (brstm_path, output_path) in enumerate(tasks, start=file_index + 1):
            future = executor.submit(convert_file, brstm_path, output_path, idx, total_files)
            futures[future] = brstm_path.stem
        
        for future in as_completed(futures):
            result = future.result()
            print(result)
            completed += 1
    
    elapsed_time = time.time() - start_time
    print(f"\nConversion complete!")
    print(f"Converted {len(tasks)} files in {elapsed_time:.1f} seconds")
    print(f"ALAC files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    convert_files_parallel()
