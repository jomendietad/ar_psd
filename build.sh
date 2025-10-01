#!/bin/bash

# --- build.sh (Automatic Version) ---
# Smart script that looks for .wav files in the current directory.
# - If it finds one, it analyzes it automatically.
# - If it finds several, it asks the user to choose.
# - If it finds none, it displays an error.
#
# Usage: ./build.sh

# Stops execution if any command fails.
set -e

# Enable 'nullglob' so the array is empty if there are no matches.
shopt -s nullglob

# 1. Find all .wav files in the current directory.
WAV_FILES=(*.wav)
NUM_WAVS=${#WAV_FILES[@]} # Count the number of files found.

# Variable to store the selected file.
WAV_FILE=""

# 2. Logic to decide which file to process.
if [ $NUM_WAVS -eq 0 ]; then
    # Case 1: No .wav files were found.
    echo "Error: No .wav file found in this directory."
    echo "Please place a .wav audio file here before running."
    exit 1
elif [ $NUM_WAVS -eq 1 ]; then
    # Case 2: Exactly one .wav file was found.
    WAV_FILE="${WAV_FILES[0]}"
    echo "Found a single .wav file: '$WAV_FILE'. Starting analysis..."
else
    # Case 3: Multiple .wav files were found.
    echo "Multiple .wav files found. Please choose one to analyze:"
    
    # Use the 'select' command to create a selection menu.
    # An option to "Exit" the script is added.
    select FILENAME in "${WAV_FILES[@]}" "Exit"; do
        if [[ "$FILENAME" == "Exit" ]]; then
            echo "Analysis canceled."
            exit 0
        elif [ -n "$FILENAME" ]; then
            WAV_FILE="$FILENAME"
            echo "You have selected: '$WAV_FILE'. Starting analysis..."
            break # Exit the selection loop.
        else
            echo "Invalid option. Please enter the corresponding number."
        fi
    done
fi

# 3. Execute the 'analyze' target of the Makefile with the selected file.
#    This block only runs if the WAV_FILE variable has been set.
if [ -n "$WAV_FILE" ]; then
    echo "--------------------------------------------------"
    make analyze WAVFILE="$WAV_FILE"
    echo "--------------------------------------------------"
    echo ""
    echo "--- Process completed successfully ---"
    echo "The analysis result is shown above."
    echo "The plot has been saved in the 'plots/' folder."
else
    # This would only happen if the 'select' menu fails, it is a safety measure.
    echo "Error: No file was selected."
    exit 1
fi