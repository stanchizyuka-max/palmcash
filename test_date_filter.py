#!/usr/bin/env python
"""
Test date filtering on vault transactions
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from datetime import date, datetime, timedelta

print("\n" + "="*60)
print("DATE FILTER TEST")
print("="*60)

# Get all transactions
all_tx = VaultTransaction.objects.all()
print(f"\n📊 Total Transactions: {all_tx.count()}")

# Show date range
if all_tx.exists():
    earliest = all_tx.order_by('transaction_date').first()
    latest = all_tx.order_by('-transaction_date').first()
    print(f"\n📅 Date Range:")
    print(f"   Earliest: {earliest.transaction_date.date()}")
    print(f"   Latest: {latest.transaction_date.date()}")

# Test 1: Filter by specific date
print(f"\n\n🧪 TEST 1: Filter by specific date (2026-05-07)")
test_date = '2026-05-07'
filtered = VaultTransaction.objects.filter(transaction_date__date=test_date)
print(f"   Results: {filtered.count()} transactions")
if filtered.exists():
    for tx in filtered[:5]:
        print(f"   - {tx.transaction_date} | {tx.branch} | {tx.transaction_type}")

# Test 2: Filter by date range (gte)
print(f"\n\n🧪 TEST 2: Filter from date (>= 2026-05-06)")
date_from = '2026-05-06'
filtered_from = VaultTransaction.objects.filter(transaction_date__date__gte=date_from)
print(f"   Results: {filtered_from.count()} transactions")

# Test 3: Filter by date range (lte)
print(f"\n\n🧪 TEST 3: Filter to date (<= 2026-05-07)")
date_to = '2026-05-07'
filtered_to = VaultTransaction.objects.filter(transaction_date__date__lte=date_to)
print(f"   Results: {filtered_to.count()} transactions")

# Test 4: Filter by date range (both)
print(f"\n\n🧪 TEST 4: Filter date range (2026-05-06 to 2026-05-07)")
filtered_range = VaultTransaction.objects.filter(
    transaction_date__date__gte='2026-05-06',
    transaction_date__date__lte='2026-05-07'
)
print(f"   Results: {filtered_range.count()} transactions")

# Test 5: Check transaction_date field type
print(f"\n\n🔍 FIELD INSPECTION:")
if all_tx.exists():
    sample = all_tx.first()
    print(f"   transaction_date type: {type(sample.transaction_date)}")
    print(f"   transaction_date value: {sample.transaction_date}")
    print(f"   transaction_date.date(): {sample.transaction_date.date()}")

# Test 6: Simulate web request with empty strings
print(f"\n\n🧪 TEST 6: Simulate empty date inputs (like web form)")
date_from_empty = ''
date_to_empty = ''

qs = VaultTransaction.objects.all()
print(f"   Initial queryset: {qs.count()} transactions")

if date_from_empty.strip():
    qs = qs.filter(transaction_date__date__gte=date_from_empty)
    print(f"   After date_from filter: {qs.count()}")
else:
    print(f"   date_from is empty, skipping filter")

if date_to_empty.strip():
    qs = qs.filter(transaction_date__date__lte=date_to_empty)
    print(f"   After date_to filter: {qs.count()}")
else:
    print(f"   date_to is empty, skipping filter")

print(f"   Final queryset: {qs.count()} transactions")

# Test 7: Test with actual date strings (like from form) - TIMEZONE AWARE
print(f"\n\n🧪 TEST 7: Simulate form submission with dates (TIMEZONE AWARE)")
date_from_form = '2026-05-01'
date_to_form = '2026-05-07'

from datetime import datetime
from django.utils import timezone as tz

qs2 = VaultTransaction.objects.all()
print(f"   Initial queryset: {qs2.count()} transactions")

if date_from_form.strip():
    dt_from = datetime.strptime(date_from_form, '%Y-%m-%d')
    dt_from = tz.make_aware(dt_from.replace(hour=0, minute=0, second=0, microsecond=0))
    qs2 = qs2.filter(transaction_date__gte=dt_from)
    print(f"   After date_from filter ({date_from_form}): {qs2.count()}")
    print(f"   Using datetime: {dt_from}")

if date_to_form.strip():
    dt_to = datetime.strptime(date_to_form, '%Y-%m-%d')
    dt_to = tz.make_aware(dt_to.replace(hour=23, minute=59, second=59, microsecond=999999))
    qs2 = qs2.filter(transaction_date__lte=dt_to)
    print(f"   After date_to filter ({date_to_form}): {qs2.count()}")
    print(f"   Using datetime: {dt_to}")

print(f"   Final queryset: {qs2.count()} transactions")

# Test 8: Check for timezone issues
print(f"\n\n🕐 TIMEZONE CHECK:")
from django.conf import settings
print(f"   USE_TZ: {settings.USE_TZ}")
print(f"   TIME_ZONE: {settings.TIME_ZONE}")

if all_tx.exists():
    sample = all_tx.first()
    print(f"   Sample transaction_date: {sample.transaction_date}")
    print(f"   Is aware: {sample.transaction_date.tzinfo is not None}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60 + "\n")
