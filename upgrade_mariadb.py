#!/usr/bin/env python3
"""
MariaDB Upgrade Helper Script
This script helps you upgrade MariaDB from 10.4 to 10.6
"""

import subprocess
import sys
import os
from pathlib import Path

def check_mariadb_version():
    """Check current MariaDB version"""
    try:
        result = subprocess.run(
            ['mysql', '-h', 'localhost', '-P', '3307', '-u', 'root', '-e', 'SELECT VERSION();'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            output = result.stdout
            if '10.4' in output:
                print("✓ Current MariaDB version: 10.4.32")
                return '10.4'
            elif '10.5' in output or '10.6' in output or '10.7' in output:
                print("✓ MariaDB is already 10.5 or later!")
                return 'new'
        return None
    except Exception as e:
        print(f"Error checking version: {e}")
        return None

def main():
    print("=" * 60)
    print("MariaDB Upgrade Helper")
    print("=" * 60)
    
    version = check_mariadb_version()
    
    if version == 'new':
        print("\n✓ Your MariaDB is already 10.5 or later!")
        print("Try running: python manage.py migrate")
        return 0
    
    if version == '10.4':
        print("\n⚠ MariaDB 10.4 detected - upgrade needed")
        print("\nTo upgrade MariaDB:")
        print("1. Download MariaDB 10.6 MSI from: https://mariadb.org/download/")
        print("2. Run the installer")
        print("3. Select 'Upgrade existing installation'")
        print("4. Keep port 3307")
        print("5. Complete the installation")
        print("\nAfter upgrade, run this script again to verify.")
        return 1
    
    print("\n✗ Could not determine MariaDB version")
    return 1

if __name__ == '__main__':
    sys.exit(main())
