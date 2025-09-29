#!/bin/bash

VGMSTREAM="/Users/ethan/sandbox/marioworld/vgmstream/vgmstream-cli"
INPUT_DIR="mkw_music_brstm"
OUTPUT_DIR="mkw_music_alac"

if [ ! -f "$VGMSTREAM" ]; then
    echo "Error: vgmstream-cli not found at $VGMSTREAM"
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory $INPUT_DIR not found"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Converting BRSTM files to ALAC (Apple Lossless)..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

count=0
total=$(find "$INPUT_DIR" -name "*.brstm" | wc -l | tr -d ' ')

for brstm in "$INPUT_DIR"/*.brstm; do
    if [ -f "$brstm" ]; then
        basename=$(basename "$brstm" .brstm)
        output="$OUTPUT_DIR/$basename.m4a"
        
        if [ ! -f "$output" ]; then
            count=$((count + 1))
            echo "[$count/$total] Converting: $basename"
            # Convert to WAV first, then use ffmpeg to convert to ALAC
            "$VGMSTREAM" -o - "$brstm" 2>/dev/null | ffmpeg -i - -c:a alac "$output" -y -loglevel quiet 2>/dev/null
            
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
echo "ALAC files saved to: $OUTPUT_DIR"

# Show summary
echo ""
echo "Summary:"
echo "Total BRSTM files: $total"
echo "Successfully converted: $(find "$OUTPUT_DIR" -name "*.m4a" | wc -l | tr -d ' ')"
