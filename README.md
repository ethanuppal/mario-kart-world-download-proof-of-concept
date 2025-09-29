THIS IS A PROOF OF CONCEPT. YOU SHOULD NOT RUN IT. I DO NOT EVER INTEND TO RUN IT. I DO NOT GUARANTEE THAT THIS WORKS BECAUSE I HAVE NOT RUN IT.

PIRACY IS ILLEGAL. DO NOT USE THIS CODE TO TRAIN MODELS.

# Mario Kart World Music Downloader

A Python script to download all lossless BRSTM music files from Mario Kart World and convert them to FLAC/WAV using vgmstream.

## Features

- Downloads the latest vgmstream-cli for macOS automatically
- Fetches all 268 Mario Kart World music tracks in lossless BRSTM format
- Includes browser-like headers to avoid bot detection
- Concurrent downloads with progress tracking
- Automatic retry and error handling
- Conversion script to convert BRSTM to FLAC/WAV

## Prerequisites

- macOS (for vgmstream-cli compatibility)
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone or download this repository:
```bash
cd /path/to/marioworld
```

3. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On macOS/Linux
uv pip install -r requirements.txt
```

## Usage

1. Run the downloader script:
```bash
python download_mkw_music.py
```

The script will:
- Download the latest vgmstream-cli for macOS
- Fetch the song list from Smash Custom Music
- Download all BRSTM files to `mkw_music_brstm/`
- Create a conversion script `convert_to_flac.sh`

2. Convert BRSTM files to FLAC (optional):
```bash
./convert_to_flac.sh
```

This will convert all downloaded BRSTM files to FLAC format in the `mkw_music_flac/` directory.

## Output Structure

```
marioworld/
├── vgmstream/           # vgmstream-cli binary
├── mkw_music_brstm/     # Downloaded BRSTM files
├── mkw_music_flac/      # Converted FLAC files (after running conversion)
└── convert_to_flac.sh   # Auto-generated conversion script
```

## Configuration

- **Concurrent Downloads**: The script uses 3 concurrent downloads by default to be respectful of the server. This can be adjusted in the `download_all_songs()` function.
- **Output Format**: To convert to WAV instead of FLAC, edit `convert_to_flac.sh` and change `.flac` to `.wav`.

## Notes

- The BRSTM files are high-quality capture card recordings, not direct game rips
- Files are downloaded from [Smash Custom Music](https://smashcustommusic.net/game/5609)
- The script includes delays and browser headers to avoid triggering bot protection
- Already downloaded files will be skipped on subsequent runs

## Alternative Download Method

Due to aggressive bot protection on the Smash Custom Music website, the automatic downloader might fail. If this happens, use the URL generator script:

```bash
python generate_download_urls.py
```

This creates:
- `download_with_wget.sh` - A bash script that downloads files one by one with delays
- `mkw_urls.txt` - A simple list of all download URLs
- `mkw_aria2_input.txt` - Input file for aria2c downloader

Then run:
```bash
./download_with_wget.sh
```

## Troubleshooting

If downloads fail with "Bot protection triggered":
- Use the alternative download method above
- Try using a VPN or different network connection
- Download files manually from the website
- Run the script at different times of day
- Increase delays between downloads

## License

This tool is for personal use. Please respect the original uploaders and the Smash Custom Music community.
