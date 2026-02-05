#!/usr/bin/env python3
"""
Read version from app/_version.py file
"""
import os
import re
import sys
from pathlib import Path


def read_version():
    """Extract version from _version.py file"""
    version_file = Path("app/_version.py")
    
    if not version_file.exists():
        print("::error::app/_version.py not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        content = version_file.read_text()
        
        # Match both single and double quotes
        # Pattern: __version__ = "1.2.3" or __version__ = '1.2.3'
        pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content)
        
        if not match:
            print("::error::Could not extract version from app/_version.py", file=sys.stderr)
            sys.exit(1)
        
        version = match.group(1)
        print(f"Extracted version: {version}")
        
        # Write to GITHUB_OUTPUT
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"version={version}\n")
        
        return version
        
    except Exception as e:
        print(f"::error::Error reading version file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    read_version()