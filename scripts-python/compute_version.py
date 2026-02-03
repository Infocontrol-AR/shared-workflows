#!/usr/bin/env python3
"""
Compute version based on IMAGE_TAG, VERSION_FILE_NAME, and branch
"""
import os
import sys
import re
import subprocess


def run_command(cmd, capture_output=True):
    """Run a shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    return result


def write_output(key, value):
    """Write to GITHUB_OUTPUT"""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{key}={value}\n")


def increment_version(version_file, increment_type):
    """Call versionmanager.py to increment version"""
    cmd = f'python3 /devops-tools/versionmanager.py increase "{version_file}" --number "{increment_type}"'
    run_command(cmd, capture_output=False)


def get_version(version_file):
    """Get version from versionmanager.py"""
    result = run_command(f'python3 /devops-tools/versionmanager.py get "{version_file}"')
    version = result.stdout.strip().replace('\r', '')
    return version


def commit_and_push_version(version, ref):
    """Commit version changes and push"""
    run_command('git config user.email "devops@achilles.com"')
    run_command('git config user.name "Achilles DevOps Bot"')
    
    run_command(f'git tag -a "{version}" -m "Tag {version} created automatically"')
    run_command('git add .')
    run_command('git commit -m "NOTICKET: Increasing version number" || echo "No changes to commit"')
    
    run_command('git push --tags')
    run_command(f'git push origin "{ref}"')


def compute_version():
    """Main version computation logic"""
    image_tag = os.getenv('IMAGE_TAG', 'None')
    version_file_name = os.getenv('VERSION_FILE_NAME', 'None')
    github_run_id = os.getenv('GITHUB_RUN_ID', '')
    version_number = os.getenv('VERSION_NUMBER', 'patch')
    ref = os.getenv('GITHUB_REF_NAME', '')
    
    # Check if IMAGE_TAG is set and not 'None'
    if image_tag and image_tag != 'None':
        print(f"Using provided IMAGE_TAG: {image_tag}")
        write_output('version', image_tag)
        return
    
    # Check if VERSION_FILE_NAME is 'None'
    if version_file_name == 'None':
        print("Using hardcoded version.")
        write_output('version', 'bge-m3')
        return
    
    print(f"Branch: {ref}")
    
    # Determine version based on branch
    if re.match(r'^(develop|main|feature/|issue/|fix/)', ref):
        # Development branches
        version = f"latest-{github_run_id}"
        write_output('version', version)
        
    elif re.match(r'^(qa|staging|bugfix/)', ref):
        # QA/Staging branches - increment based on VERSION_NUMBER
        increment_version(version_file_name, version_number)
        version = get_version(version_file_name)
        commit_and_push_version(version, ref)
        write_output('version', version)
        
    elif ref.startswith('hotfix/'):
        # Hotfix branches - always increment patch
        increment_version(version_file_name, 'patch')
        version = get_version(version_file_name)
        commit_and_push_version(version, ref)
        write_output('version', version)
        
    else:
        # Unknown branch
        write_output('version', 'unknown')
        print(f"::warning::Unknown branch '{ref}', version set to 'unknown'")


if __name__ == '__main__':
    try:
        compute_version()
    except Exception as e:
        print(f"::error::Version computation failed: {e}", file=sys.stderr)
        sys.exit(1)