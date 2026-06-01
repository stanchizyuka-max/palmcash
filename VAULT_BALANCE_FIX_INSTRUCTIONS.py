"""
VAULT BALANCE FIX INSTRUCTIONS
===============================

PROBLEM IDENTIFIED:
-------------------
The "balance_after" column in vault transactions is showing incorrect values.
This happens because transactions are being created in multiple places:
1. vault_services.py (CORRECT - updates vault balance first, then records transaction)
2. dashboard/vault_views.py (INCORRECT - may not update vault balance correctly)
3. expenses/views.py (INCORRECT - may not update vault balance correctly)
4. payments/views.py (INCORRECT - may not update vault balance correctly)
5. clients/views.py (INCORRECT - may not update vault balance correctly)

ROOT CAUSE:
-----------
When transactions are created directly (not through vault_services), the balance_after
value is calculated at the time of creation, but if multiple transactions happen
simultaneously or the vault balance isn't updated first, the balance_after becomes incorrect.

SOLUTION:
---------
1. Fix MANDEVU's negative balance (immediate)
2. Recalculate all balance_after values (data fix)
3. Ensure all future transactions go through vault_services (code fix - optional)

STEPS TO FIX:
-------------

Step 1: Fix MANDEVU Negative Balance
-------------------------------------
Run on server:
    python fix_mandevu_negative_balance.py

This will inject K25 to bring MANDEVU's vault balance to K0.00

Step 2: Recalculate All Balance After Values
---------------------------------------------
Run on server:
    python recalculate_all_balance_after_values.py

This will:
- Go through ALL vault transactions in chronological order
- Recalculate the balance_after for each transaction
- Update the vault model balances to match
- Fix any discrepancies

Step 3: Restart Application
----------------------------
    sudo systemctl restart palmcash

Step 4: Hard Refresh Browsers
------------------------------
All users must hard refresh: Ctrl + Shift + R (Windows/Linux) or Cmd + Shift + R (Mac)

EXPECTED RESULTS:
-----------------
After running these scripts:
1. MANDEVU vault balance will be K0.00 (not negative)
2. All "balance_after" values will be correct and sequential
3. Vault model balances will match the last transaction's balance_after
4. Transaction history will show correct running balances

VERIFICATION:
-------------
Check each branch's vault page:
- Balance After column should show sequential values
- Each transaction should correctly add (IN) or subtract (OUT) from previous balance
- Final balance should match the vault balance shown at top of page

NOTES:
------
- The recalculation script is safe to run multiple times
- It only updates balance_after values, doesn't create or delete transactions
- All actual transaction amounts remain unchanged
- Only the calculated "balance_after" field is updated
"""
