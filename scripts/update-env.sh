#!/bin/bash

# update-env.sh - Update .env file with secrets and configuration
# Usage: ./update-env.sh <env_file> <key1> <value1> <key2> <value2> ...

set -e

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found"
    exit 1
fi

# Check if perl is available
if ! command -v perl &> /dev/null; then
    echo "Error: perl is not installed. Please install it first:"
    echo "  sudo apt-get install perl"
    exit 1
fi

echo "Updating environment file: $ENV_FILE"

# Shift to get key-value pairs
shift

# Function to update or add a key-value pair in .env file
update_env_var() {
    local key="$1"
    local value="$2"
    
    # Escape special characters for perl regex
    # We use quotemeta in perl to handle all special chars automatically
    local escaped_key=$(printf '%s' "$key" | perl -pe 's/([\\|.*+?{}()[\]^$])/\\$1/g')
    
    if grep -q "^${key}=" "$ENV_FILE"; then
        # Key exists, update it using perl
        # Use \Q...\E to quote metacharacters in the replacement value
        perl -i -pe "s/^${escaped_key}=.*/\Q${key}\E=\Q${value}\E/" "$ENV_FILE"
        echo "✓ Updated: $key"
    else
        # Key doesn't exist, append it
        # No escaping needed when appending
        echo "${key}=${value}" >> "$ENV_FILE"
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