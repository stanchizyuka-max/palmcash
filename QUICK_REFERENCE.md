# Quick Reference - Vault Type Filters

## 🎯 All Pages with Vault Type Filters

| Page | URL | Filter Name | Column Name | Status |
|------|-----|-------------|-------------|--------|
| **Processing Fees Summary** | `/dashboard/processing-fees-summary/` | Loan Type | Loan Type | ✅ Fixed |
| **Manager Processing Fees** | `/dashboard/processing-fees/` | Loan Type | Vault | ✅ Working |
| **Expense List** | `/dashboard/expenses/` | Vault Type | Vault | ✅ Working |
| **Vault Transactions** | `/dashboard/vault/` | Vault Type | Vault | ✅ Working |

---

## 🔍 Quick Troubleshooting

### Problem: "I don't see the new filter"
**Solution**: Hard refresh browser (Ctrl+Shift+R)

### Problem: "Filter shows 0 results"
**Solution**: Click "Clear" or select "All Types/All Vaults"

### Problem: "Vault shows 'No transactions yet'"
**Solution**: Run `python check_vault_transactions.py` to check database

### Problem: "Changes not appearing"
**Solution**: 
1. Restart development server
2. Hard refresh browser
3. Clear browser cache

---

## 📱 Quick Commands

### Restart Server
```bash
python manage.py runserver
```

### Check Database
```bash
python check_vault_transactions.py
```

### Push to Git
```bash
git add .
git commit -m "Your message"
git push origin main
```

---

## 🎨 Badge Colors

| Badge | Meaning | Color |
|-------|---------|-------|
| 📅 Daily | Daily vault/loan | Blue |
| 📆 Weekly | Weekly vault/loan | Purple |

---

## ✅ Testing Checklist

- [ ] Processing Fees Summary has 5 filters (including Loan Type)
- [ ] Processing Fees Summary table has Loan Type column
- [ ] Manager Processing Fees has Loan Type filter
- [ ] Manager Processing Fees table has Vault column
- [ ] Expense List has Vault Type filter
- [ ] Expense List table has Vault column
- [ ] Vault page filters work with empty dates
- [ ] All filters show correct badges (📅/📆)

---

## 🆘 Need Help?

1. Check FINAL_FIX_SUMMARY.md for detailed instructions
2. Check VISUAL_GUIDE_WHAT_TO_EXPECT.md for screenshots
3. Run diagnostic script: `python check_vault_transactions.py`
4. Check browser console (F12) for errors
