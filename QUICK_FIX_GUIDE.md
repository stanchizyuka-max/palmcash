# 🚨 QUICK FIX GUIDE - Vault Balance Issue

## The Problem in One Sentence:
Payment collections are being recorded as OUT (money leaving) instead of IN (money coming in), making vault balances negative.

---

## The Fix in 3 Commands:

```bash
# 1. Check what's wrong
python check_actual_state.py

# 2. Fix it
python fix_payment_collection_directions.py

# 3. Verify it worked
python check_actual_state.py
```

---

## What You'll See:

### BEFORE Fix:
```
Payment Collection  ▼ OUT  -K210.00  Balance: K-210.00  ❌
Payment Collection  ▼ OUT  -K280.00  Balance: K-490.00  ❌
```

### AFTER Fix:
```
Payment Collection  ▲ IN   +K210.00  Balance: K210.00   ✅
Payment Collection  ▲ IN   +K280.00  Balance: K490.00   ✅
```

---

## Optional Cleanup:

After the fix, you can remove the capital injections that were added by previous fix attempts:

```bash
python remove_capital_injections.py
```

---

## Expected Final Balances:

| Branch | Expected Balance |
|--------|-----------------|
| KAMWALA SOUTH | Positive (payment collections - expenses) |
| Chazanga | K350 (K140 + K210) |
| KUKU | Positive (payment collections - expenses) |
| MANDEVU | Positive (payment collections - expenses) |

---

## Don't Forget:

1. **Restart app:** `sudo systemctl restart palmcash`
2. **Hard refresh browser:** Ctrl + Shift + R

---

## If It Doesn't Work:

1. Run `investigate_reversals.py`
2. Save output from `check_actual_state.py`
3. Take screenshots
4. Contact developer

---

**All scripts are safe to run multiple times!**
