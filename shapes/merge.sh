
#!/bin/bash

echo "" > merged.txt  # Clear existing merged.txt

for file in *.obj *.urdf; do
    if [ -f "$file" ]; then
        echo "[$file]" >> merged.txt
        cat "$file" >> merged.txt
        echo "" >> merged.txt 
    fi
done

echo "Merged content written to merged.txt"
