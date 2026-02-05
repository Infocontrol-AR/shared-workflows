#!/usr/bin/env python3
"""
Validate GPG signatures and enforce commit message format based on branch naming
"""
import os
import re
import sys
import subprocess


def run_command(cmd, capture_output=True, check=False):
    """Run a shell command and return the result"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture_output,
        text=True,
        check=check
    )
    return result


def check_gpg_signature():
    """Check if the latest commit is GPG signed"""
    print("Checking GPG signatures...")
    
    result = run_command("git log --show-signature -1 2>&1")
    
    if "No signature" in result.stdout or "No signature" in result.stderr:
        print("::warning::Latest commit is not GPG signed. Consider signing your commits for better security.")
    else:
        print("✅ Latest commit is GPG signed")


def validate_branch_and_commit():
    """Validate branch naming and enforce commit message format"""
    ref = os.getenv('GITHUB_REF_NAME', '')
    print(f"Branch: {ref}")
    
    # Pattern for ticket-based branches: feature/XXX, issue/XXX, etc.
    # XXX must be exactly 3 digits
    pattern = r'^(feature|issue|fix|hotfix|bugfix)/(\d{3})$'
    match = re.match(pattern, ref)
    
    if match:
        ticket_number = match.group(2)
        print(f"Detected ticket number: {ticket_number}")
        
        # Get the last commit message
        result = run_command("git log -1 --pretty=%B")
        commit_msg = result.stdout.strip()
        print(f"Current commit message: {commit_msg}")
        
        # Check if commit message starts with "XXX:"
        if not commit_msg.startswith(f"{ticket_number}:"):
            print(f"Commit message does not start with '{ticket_number}:'. Amending commit...")
            
            # Amend the commit message
            new_commit_msg = f"{ticket_number}: {commit_msg}"
            
            # Configure git
            run_command('git config user.email "devops@achilles.com"')
            run_command('git config user.name "Achilles DevOps Bot"')
            
            # Amend commit
            escaped_msg = new_commit_msg.replace('"', '\\"')
            run_command(f'git commit --amend -m "{escaped_msg}"')
            
            # Force push
            run_command(f'git push --force-with-lease origin "{ref}"')
            
            print(f"✅ Commit message amended to: {new_commit_msg}")
        else:
            print(f"✅ Commit message already starts with '{ticket_number}:'")
    
    elif re.match(r'^(develop|main|qa|staging)$', ref):
        print(f"✅ Branch '{ref}' is a standard branch, skipping ticket number validation")
    
    else:
        print(f"::warning::Branch name '{ref}' does not follow the expected pattern "
              f"(feature/XXX, issue/XXX, fix/XXX, hotfix/XXX, bugfix/XXX where XXX is a 3-digit number). "
              f"Consider following the naming convention.")


def main():
    """Main validation function"""
    print("=== Running commit and branch validation ===")
    
    try:
        check_gpg_signature()
        validate_branch_and_commit()
        print("=== Validation complete ===")
    except Exception as e:
        print(f"::error::Validation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()