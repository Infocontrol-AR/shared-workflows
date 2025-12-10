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
    
    # Escape special characters for sed
    local escaped_value=$(echo "$value" | sed 's/[&/\]/\\&/g')
    
    if grep -q "^${key}=" "$ENV_FILE"; then
        # Key exists, update it
        sed -i "s|^${key}=.*|${key}=${escaped_value}|g" "$ENV_FILE"
        echo "✓ Updated: $key"
    else
        # Key doesn't exist, append it
        echo "${key}=${escaped_value}" >> "$ENV_FILE"
        echo "✓ Added: $key"
    fi
}

# Process key-value pairs
while [ $# -gt 0 ]; do
    if [ $# -lt 2 ]; then
        echo "Error: Missing value for key '$1'"
        exit 1
    fi
    
    key="$1"
    value="$2"
    
    update_env_var "$key" "$value"
    
    shift 2
done

echo "Environment file updated successfully!"