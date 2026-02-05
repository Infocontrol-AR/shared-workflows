#!/usr/bin/env python3
"""
Perform health checks on deployed service
"""
import os
import sys
import time
import requests


def write_output(key, value):
    """Write to GITHUB_OUTPUT"""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{key}={value}\n")


def health_check():
    """Run health checks with retry logic"""
    health_status = "unhealthy"
    timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', '300'))
    interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '10'))
    ssh_ip = os.getenv('SSH_IP')
    container_port = os.getenv('CONTAINER_PORT')
    health_endpoint = os.getenv('HEALTH_CHECK_ENDPOINT', '/health')
    
    elapsed = 0
    
    url = f"http://{ssh_ip}:{container_port}{health_endpoint}"
    
    print("Starting health checks...")
    print(f"Endpoint: {url}")
    print(f"Timeout: {timeout}s, Interval: {interval}s")
    
    attempt = 0
    while elapsed < timeout:
        attempt += 1
        
        try:
            response = requests.get(url, timeout=5)
            http_code = response.status_code
        except Exception as e:
            http_code = 0
            print(f"Attempt {attempt}: Connection error - {e}")
        
        print(f"Attempt {attempt}: HTTP {http_code}")
        
        if http_code == 200:
            print("✅ Health check passed!")
            health_status = "healthy"
            break
        
        time.sleep(interval)
        elapsed += interval
    
    if health_status == "unhealthy":
        print(f"::error::Health checks failed after {timeout}s")
    
    write_output('status', health_status)
    return health_status


if __name__ == '__main__':
    try:
        status = health_check()
        if status == "unhealthy":
            sys.exit(1)
    except Exception as e:
        print(f"::error::Health check failed: {e}", file=sys.stderr)
        sys.exit(1)