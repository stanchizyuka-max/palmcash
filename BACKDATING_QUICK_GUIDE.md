# Quick Guide: Backdating Loan Applications

## 🎯 What It Does

Allows you to record loan applications with the **actual date** the client applied, even if you're entering it days later.

---

## 📍 Where to Find It

**Path**: Dashboard → Submit Loan Application

**Location in Form**: Right after the "Borrower" field

---

## 🖼️ What You'll See

```
┌──────────────────────────────────────────────────────┐
│ Submit Loan Application                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Borrower *                                           │
│ [Select borrower ▼]                                  │
│                                                      │
│ Application Date (defaults to today)                 │
│ [2026-05-07] 📅                                     │
│ ℹ️ Select a past date if this application was made  │
│    on a previous day. Cannot be in the future.      │
│                                                      │
│ Loan Amount (K) *                                    │
│ [Enter amount]                                       │
│                                                      │
│ ... (rest of form)                                   │
└──────────────────────────────────────────────────────┘
```

---

## ✅ How to Use

### Normal Application (Today)
1. Open loan application form
2. **Leave Application Date as is** (defaults to today)
3. Fill in other fields
4. Submit

### Backdated Application (Past Date)
1. Open loan application form
2. **Click on Application Date field**
3. **Select the past date** when client actually applied
4. Fill in other fields
5. Submit

---

## 📅 Examples

### Example 1: Client Applied Yesterday
```
Situation: Client came yesterday but you're entering today
Action: Change Application Date to yesterday's date
Result: Application shows yesterday's date in reports ✅
```

### Example 2: Catching Up on Paperwork
```
Situation: You have 5 applications from last week on paper
Action: For each one, set Application Date to the day it was made
Result: All applications show correct dates ✅
```

### Example 3: System Was Down
```
Situation: System was down Monday-Tuesday, now it's Wednesday
Action: Enter Monday's applications with Monday's date
Result: Reports show applications on correct days ✅
```

---

## ⚠️ Rules

### ✅ Allowed:
- Today's date (default)
- Yesterday's date
- Any past date
- Leaving it empty (defaults to today)

### ❌ Not Allowed:
- Tomorrow's date
- Any future date
- Dates before the system existed (use common sense)

---

## 💡 Tips

1. **Default is fine** - If application is made today, just leave it as is
2. **Be accurate** - Select the actual date client applied
3. **Document why** - If backdating significantly, note the reason
4. **Check reports** - Applications appear in the month/week they were made

---

## 🔍 How to Verify

After submitting:
1. Go to **Loan Applications List**
2. Find your application
3. Check the **Created Date** column
4. Should show the date you selected ✅

---

## 🆘 Troubleshooting

### Problem: Can't select a date
**Solution**: Make sure you're clicking on the date field, not just typing

### Problem: Future date not working
**Solution**: This is intentional - you can't apply for tomorrow!

### Problem: Date not showing in reports
**Solution**: Check the application details - date should be there

---

## 📊 Impact

### Before Backdating:
```
Client applied: Monday, May 5
Officer entered: Wednesday, May 7
System recorded: Wednesday, May 7 ❌
Report shows: Wednesday (WRONG)
```

### After Backdating:
```
Client applied: Monday, May 5
Officer entered: Wednesday, May 7
Application Date selected: Monday, May 5
System recorded: Monday, May 5 ✅
Report shows: Monday (CORRECT)
```

---

## ✅ Summary

**Feature**: Application Date field  
**Purpose**: Record accurate application dates  
**Location**: Loan application form  
**Default**: Today  
**Validation**: No future dates  

Simple, accurate, and flexible! 🎉
