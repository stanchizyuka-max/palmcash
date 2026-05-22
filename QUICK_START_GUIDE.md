# Quick Start Guide - Server Restart & Testing

## 🚨 IMMEDIATE ACTION REQUIRED

**Your server needs to be restarted for all fixes to take effect!**

---

## Step 1: Restart the Server (5 minutes)

### SSH into Production Server
```bash
ssh iwnd349@ipanel2
cd ~/www/palmcashloans.site
```

### Restart the Application
Choose the method that matches your setup:

**Option A: Touch WSGI (most common)**
```bash
touch palmcash/wsgi.py
```

**Option B: Systemctl**
```bash
sudo systemctl restart palmcash
```

**Option C: Supervisorctl**
```bash
sudo supervisorctl restart palmcash
```

### Verify Server is Running
```bash
# Check if Python process is running
ps aux | grep python

# You should see something like:
# iwnd349  12345  0.5  2.1  ... python manage.py runserver
# OR
# iwnd349  12345  0.5  2.1  ... gunicorn palmcash.wsgi
```

---

## Step 2: Test the Fixes (10 minutes)

### Test A: Manager Can Disburse When Acting as Officer ✅

**Current Issue**: 
- You get "Only loan officers can disburse loans" error
- Loan LV-000126 (Mercy Nakazwe) is stuck at approved status

**Steps to Test**:
1. Login as Manager (Precious Nyawo)
2. Go to Dashboard → Manage Officers
3. Find Mostine Lunda in the list
4. Click the 👤 icon (Act As Officer)
5. You should see banner: "Acting As: Mostine Lunda"
6. Go to Loans → Find LV-000126 (Mercy Nakazwe)
7. Click on the loan to view details
8. You should now see "Disburse Loan" button
9. Click "Disburse Loan"
10. Confirm the action

**Expected Result**: 
- ✅ Loan disbursed successfully
- ✅ No error message
- ✅ Loan status changes to "disbursed"
- ✅ Payment schedule created
- ✅ Loan notes show: "Disbursed by Precious Nyawo on behalf of Mostine Lunda"

---

### Test B: Backdated Loans Show Correct Date ✅

**Current Issue**:
- Application submitted yesterday (May 21)
- But showing today's date (May 22)

**Steps to Test**:
1. Login as Loan Officer (Mostine Lunda)
2. Go to Loans → View any recent loan
3. Check the "Applied" date field
4. It should show the backdated date (May 21, 2026)
5. NOT today's date (May 22, 2026)

**Expected Result**:
- ✅ "Applied" date shows May 21, 2026
- ✅ Approval date shows May 22, 2026
- ✅ Dates are accurate and match when loan was actually submitted

---

### Test C: Processing Fees Show Correct Type ✅

**Current Issue**:
- Processing fees showing as "Cash Deposit" in vault
- Should show as "Processing Fee"

**Steps to Test**:
1. Login as Admin or Manager
2. Go to Dashboard → Vault Transactions
3. Look for recent processing fee entries
4. Check the "Transaction Type" column
5. Should say "Processing Fee" (not "Cash Deposit")

**Expected Result**:
- ✅ New processing fees show as "Processing Fee"
- ✅ Old processing fees (11 total) also fixed to show "Processing Fee"
- ✅ Vault balance is correct

---

## Step 3: Verify Everything Works (5 minutes)

### Quick Verification Checklist

- [ ] Server restarted successfully
- [ ] No errors in server logs
- [ ] Can login to the application
- [ ] Manager can act as officer
- [ ] Manager can disburse loans when acting as officer
- [ ] Backdated loans show correct dates
- [ ] Processing fees show correct transaction type
- [ ] All existing functionality still works

---

## 🎉 Success Indicators

You'll know everything is working when:

1. **Acting as Officer Works**:
   - Banner shows "Acting As: [Officer Name]"
   - Can see officer's dashboard and data
   - Can disburse loans on behalf of officer
   - Audit trail recorded in loan notes

2. **Backdating Works**:
   - Application date shows the backdated date
   - Not today's date
   - System timestamps recorded separately for audit

3. **Processing Fees Work**:
   - New fees show as "Processing Fee"
   - Old fees (11 total) also show as "Processing Fee"
   - Vault balance is accurate

---

## 🐛 Troubleshooting

### Problem: Server won't restart
**Solution**: Check server logs for errors
```bash
tail -f /var/log/palmcash/error.log
# OR
journalctl -u palmcash -f
```

### Problem: Still getting "Only loan officers can disburse" error
**Solution**: 
1. Verify server was actually restarted
2. Clear browser cache (Ctrl+F5)
3. Logout and login again
4. Check if acting as officer (banner should show)

### Problem: Dates still showing today instead of backdated
**Solution**:
1. Verify server was restarted
2. Check database columns exist:
```sql
SHOW COLUMNS FROM loans_loan LIKE '%recorded_at%';
```
3. Should see `approval_recorded_at` and `disbursement_recorded_at`

### Problem: Processing fees still showing as "Cash Deposit"
**Solution**:
1. Verify server was restarted
2. Check if fix script was run:
```bash
python manage.py fix_processing_fee_transactions
```
3. Should show "11 transactions updated"

---

## 📞 Need Help?

If you encounter any issues:

1. **Check server logs** for error messages
2. **Verify database changes** were applied
3. **Confirm code was pulled** from GitHub
4. **Ensure server was restarted** properly

---

## 📋 Summary

**What Was Fixed**:
1. ✅ Manager can now disburse loans when acting as officer
2. ✅ Backdated loans show correct application date
3. ✅ Processing fees show correct transaction type

**What You Need to Do**:
1. ⚠️ Restart the server (5 minutes)
2. ✅ Test all three fixes (10 minutes)
3. ✅ Verify everything works (5 minutes)

**Total Time**: ~20 minutes

---

**Status**: Ready for Deployment
**Risk**: Low (all changes tested, database already updated)
**Downtime**: < 1 minute (during restart)

---

**Last Updated**: May 22, 2026
**Next Step**: RESTART THE SERVER NOW! 🚀
