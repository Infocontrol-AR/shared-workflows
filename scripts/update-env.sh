#!/bin/bash

# update-env.sh - Update .env file with secrets and configuration
# Usage: ./update-env.sh <env_file> <key1> <value1> <key2> <value2> ...

set -e

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found"
    exit 1
fi

echo "Updating environment file: $ENV_FILE"

# Shift to get key-value pairs
shift

# Function to update or add a key-value pair in .env file
update_env_var() {
    local key="$1"
    local value="$2"
    
    # Check if key exists in the file
    if grep -q "^${key}=" "$ENV_FILE"; then
        # Key exists, update it
        # Use a temporary file for safety
        local temp_file="${ENV_FILE}.tmp"
        
        # Read the file line by line and update the matching key
        while IFS= read -r line; do
            if [[ "$line" =~ ^${key}= ]]; then
                # echo "${key}=\"${value}\""
                echo "${key}=${value}"
            else
                echo "$line"
            fi
        done < "$ENV_FILE" > "$temp_file"
        
        # Replace original file with updated content
        mv "$temp_file" "$ENV_FILE"
        echo "✓ Updated: $key"
    else
        # Key doesn't exist, append it
        echo "" >> "$ENV_FILE"  # Ensure there's a newline before appending
        # echo "${key}=\"${value}\"" >> "$ENV_FILE"
        echo "${key}=${value}" >> "$ENV_FILE"
        echo "✓ Added: $key"
    fi
}

# Process key-value pairs
while [ $# -gt 0 ]; do
    echo "Processing: $#"
    echo "Parsing: $1 = $2"
    if [ $# -lt 2 ]; then
        echo "Error: Missing value for key '$1'"
        exit 1
    fi
    
    key="$1"
    value="$2"
    
    # Skip empty values
    if [ -n "$value" ]; then
        update_env_var "$key" "$value"
    else
        echo "⚠ Skipped (empty value): $key"
    fi
    
    shift 2
done

echo "Environment file updated successfully!"