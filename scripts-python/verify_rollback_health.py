#!/usr/bin/env python3
"""
Verify that the rolled back service is healthy
"""
import os
import sys
import time
import requests


def verify_rollback_health():
    """Verify rollback was successful by checking health"""
    ssh_ip = os.getenv('SSH_IP')
    container_port = os.getenv('CONTAINER_PORT')
    health_endpoint = os.getenv('HEALTH_CHECK_ENDPOINT', '/health')
    
    url = f"http://{ssh_ip}:{container_port}{health_endpoint}"
    
    print("Waiting 30 seconds for rolled back container...")
    time.sleep(30)
    
    for attempt in range(1, 11):
        try:
            response = requests.get(url, timeout=5)
            http_code = response.status_code
        except Exception:
            http_code = 0
        
        if http_code == 200:
            print("✅ Rollback successful - service is healthy")
            return 0
        
        print(f"Attempt {attempt}: HTTP {http_code}")
        time.sleep(5)
    
    print("::error::Rollback verification failed")
    return 1


if __name__ == '__main__':
    try:
        exit_code = verify_rollback_health()
        sys.exit(exit_code)
    except Exception as e:
        print(f"::error::Rollback verification failed: {e}", file=sys.stderr)
        sys.exit(1)