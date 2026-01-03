# PalmCash Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Setup ✅
```bash
# Check if all systems are ready
python manage.py check
```

### Step 2: Create Borrower Groups
1. Go to: `http://localhost:8000/clients/groups/`
2. Click "Create Group"
3. Fill in:
   - Group Name
   - Branch Location
   - Payment Day (e.g., Monday)
   - Max Members (optional)
4. Click "Create"

### Step 3: Add Borrowers to Group
1. Go to group detail page
2. Click "Add Member"
3. Select borrower
4. Click "Add"

### Step 4: Create Loan Application
1. Go to: `http://localhost:8000/loans/apply/`
2. Fill in loan details:
   - Loan Type (Daily/Weekly)
   - Principal Amount
   - Term (days/weeks)
   - Purpose
3. Click "Apply"

### Step 5: Approve & Disburse Loan
1. Go to: `http://localhost:8000/loans/`
2. Find pending loan
3. Click "Approve" (if ≥15 groups)
4. Record security deposit (10%)
5. Click "Disburse"

---

## 📊 Key Dashboards

| Role | Dashboard | URL |
|------|-----------|-----|
| Admin | System Statistics | `/admin/` |
| Manager | Portfolio Overview | `/dashboard/` |
| Officer | My Groups | `/clients/groups/` |
| Borrower | My Loans | `/loans/` |

---

## 🔑 Key Requirements

### For Loan Approval
- ✅ Officer must have ≥15 active groups
- ✅ Borrower must be in officer's group
- ✅ Loan application must be complete

### For Loan Disbursement
- ✅ Loan must be approved
- ✅ Security deposit (10%) must be paid
- ✅ Deposit must be verified by manager

### For Group Creation
- ✅ Officer must have permission
- ✅ Group name must be unique
- ✅ Branch and payment day required

---

## 💰 Financial Calculations

```
Total Loan = Principal + (Principal × Interest Rate)
Payment = Total Loan ÷ Term
Security Deposit = Principal × 10%
Profit = Interest Income - Expenses
```

---

## 🎯 Common Tasks

### Create a Group
```
/clients/groups/create/
```

### View Groups
```
/clients/groups/
```

### Apply for Loan
```
/loans/apply/
```

### View Loans
```
/loans/
```

### Approve Loan
```
/loans/{id}/approve/
```

### Record Deposit
```
/loans/{id}/record-deposit/
```

### Disburse Loan
```
/loans/{id}/disburse/
```

### View Reports
```
/reports/daily-transactions/
/reports/financial/
/reports/loans/
```

---

## 🔐 User Roles

### Admin
- Full system access
- Manage users
- Verify deposits
- View all reports

### Manager
- Approve expenses
- Verify deposits
- Monitor officers
- View reports

### Loan Officer
- Create groups
- Approve loans (if ≥15 groups)
- Disburse loans
- Record deposits

### Borrower
- Apply for loans
- Make payments
- View loan status

---

## ⚠️ Common Issues

### "Officer has < 15 groups"
**Solution**: Create more groups and assign to officer

### "Deposit not verified"
**Solution**: Manager must verify deposit first

### "Group name already exists"
**Solution**: Use unique group name

### "Officer not found"
**Solution**: Run `python setup_officer_assignments.py`

---

## 📞 Support

For help:
1. Check documentation files
2. Review error messages
3. Check browser console
4. Contact admin

---

## 📚 Documentation

- **Full Guide**: `SYSTEM_DASHBOARDS_SUMMARY.md`
- **Quick Reference**: `DASHBOARD_QUICK_REFERENCE.md`
- **Architecture**: `SYSTEM_ARCHITECTURE_OVERVIEW.md`
- **Officer Setup**: `OFFICER_ASSIGNMENT_SETUP.md`

---

**PalmCash Quick Start** | December 2025
