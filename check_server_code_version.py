#!/usr/bin/env python
"""
Check if the server has the latest vault_views.py code with the fix.
This will help determine if the code was deployed.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

print(f"DEBUG: BASE_DIR = {BASE_DIR}")

# Try to load .env if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / 'palmcash' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

django.setup()

print("=" * 70)
print("SERVER CODE VERSION CHECK")
print("=" * 70)

# Check if the vault_views.py file has the new code
vault_views_path = BASE_DIR / 'dashboard' / 'vault_views.py'

print(f"\n1. Checking file: {vault_views_path}")
print(f"   File exists: {vault_views_path.exists()}")

if vault_views_path.exists():
    with open(vault_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key indicators of the new code
    indicators = {
        'Security deposit reset': 'SecurityDeposit.objects.filter' in content and 'update(paid_amount=0)' in content,
        'Transaction grouping': 'closing_groups = defaultdict' in content,
        'Security closing transaction': 'CLOSE-SECURITY-' in content,
        'Daily vault identification': "'Daily vault' in closing.description" in content,
        'Weekly vault identification': "'Weekly vault' in closing.description" in content,
        'Security identification': "'Security deposits' in closing.description" in content,
    }
    
    print("\n2. CODE FEATURES DETECTED:")
    print("-" * 70)
    
    all_present = True
    for feature, present in indicators.items():
        status = "✅" if present else "❌"
        print(f"   {status} {feature}")
        if not present:
            all_present = False
    
    print("\n3. DEPLOYMENT STATUS:")
    print("-" * 70)
    if all_present:
        print("   ✅ ALL NEW FEATURES DETECTED")
        print("   The server appears to have the latest code.")
        print("\n   If history still shows 0 closings, the issue is likely:")
        print("   - No month closings were created before")
        print("   - Old closings have different description format")
        print("   - Need to restart the application server")
    else:
        print("   ❌ MISSING FEATURES DETECTED")
        print("   The server does NOT have the latest code.")
        print("\n   Action required:")
        print("   1. Pull latest code: git pull origin main")
        print("   2. Restart application: sudo systemctl restart palmcash")
    
    # Check for old code patterns that should be removed
    print("\n4. CHECKING FOR OLD CODE PATTERNS:")
    print("-" * 70)
    
    old_patterns = {
        'Old linear processing': 'for closing in closings:' in content and 'closing_list.append({' in content,
        'Direct closing.amount usage': "closing.amount" in content,
    }
    
    # Note: Some of these patterns might legitimately exist in other parts
    # This is just a rough check
    
    print("   Note: Some patterns may exist in other contexts")
    
    # Show file modification time
    import datetime
    mod_time = datetime.datetime.fromtimestamp(vault_views_path.stat().st_mtime)
    print(f"\n5. FILE LAST MODIFIED:")
    print(f"   {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
else:
    print("   ❌ vault_views.py file not found!")

# Check git status
print("\n6. GIT STATUS:")
print("-" * 70)
import subprocess
try:
    result = subprocess.run(
        ['git', 'log', '-1', '--oneline'],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"   Latest commit: {result.stdout.strip()}")
    else:
        print(f"   Could not get git status")
except Exception as e:
    print(f"   Error checking git: {e}")

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)
