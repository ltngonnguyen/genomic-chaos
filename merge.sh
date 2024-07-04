#!/bin/bash

# Create/clear the merged.txt file
echo "" > merged.txt

# Find all .py files and iterate
for file in *.py; do
    if [ -f "$file" ]; then  # Make sure it's a regular file
        echo "[$file]" >> merged.txt
        cat "$file" >> merged.txt 
        echo "" >> merged.txt # Add a blank line for separation
    fi
done

echo "Merged content written to merged.txt"
