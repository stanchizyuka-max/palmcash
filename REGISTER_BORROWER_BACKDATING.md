# Backdating Added to Register Borrower Wizard

## ✅ What Was Added

Added **Application Date** (backdating) field to the **Register Borrower Wizard** at **Step 3 (Loan Application)**.

---

## 📍 Field Position

### Step 3 - Loan Application

**Order of fields:**
1. Borrower name (display only)
2. **Application Date** ← **NEW FIELD**
3. Loan Amount (K)
4. Repayment Type
5. Duration
6. Purpose
7. Group (optional)

---

## 🎯 Field Details

### Label
"Application Date *"

### Features
- ✅ **Required field** (marked with red asterisk)
- ✅ **Defaults to today's date** in the browser
- ✅ **Cannot select future dates** (max=today)
- ✅ **Date picker widget** (HTML5 date input)
- ✅ **Help text**: "Select the date when this application was actually made. Defaults to today. Cannot be in the future."
- ✅ **Info icon** with explanation

### Validation
- ❌ Cannot be empty (required)
- ❌ Cannot be in the future
- ✅ Must be valid date format (YYYY-MM-DD)

---

## 🔧 Technical Implementation

### Template Changes
**File**: `templates/clients/register_borrower_wizard.html`

Added the application_date field in Step 3, right after the borrower name display:

```html
<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">
    Application Date <span class="text-red-500">*</span>
  </label>
  <input type="date" name="application_date" required
    value="{{ post_data.application_date|default:today }}"
    max="{{ today }}"
    class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
  <p class="text-xs text-gray-500 mt-1">
    <i class="fas fa-info-circle mr-1"></i>
    Select the date when this application was actually made. Defaults to today. Cannot be in the future.
  </p>
</div>
```

### View Changes
**File**: `clients/views.py`

#### 1. Added `today` to context
Updated `_base_context()` method to pass today's date to the template:

```python
from datetime import date
ctx = {
    'step': step,
    'steps_meta': self.STEPS_META,
    'today': date.today().isoformat(),  # NEW
}
```

#### 2. Updated `_handle_step3()` method
Added processing for the application_date field:

```python
from django.utils import timezone
from datetime import datetime, date

# Get application_date from POST
application_date_str = request.POST.get('application_date', '').strip()

# Validate it's provided
if not application_date_str:
    errors.append('Application date is required.')

# Validate and convert to timezone-aware datetime
application_datetime = None
if application_date_str:
    try:
        application_date = datetime.strptime(application_date_str, '%Y-%m-%d').date()
        
        # Check if date is in the future
        if application_date > date.today():
            errors.append('Application date cannot be in the future.')
        else:
            # Convert to timezone-aware datetime at start of day
            application_datetime = timezone.make_aware(
                datetime.combine(application_date, datetime.min.time())
            )
    except ValueError:
        errors.append('Invalid application date format.')

# Set the application date on the LoanApplication
if application_datetime:
    app.created_at = application_datetime

app.save()
```

---

## 🎬 How It Works

### User Flow

1. **Officer registers borrower** (Step 1 - Basic Info)
2. **Officer enters borrower details** (Step 2 - Details)
3. **Officer creates loan application** (Step 3 - Loan Application)
   - **Selects application date** (defaults to today)
   - If client came yesterday but officer is registering today, officer can select yesterday's date
   - Cannot select future dates
4. **Officer records processing fee** (Step 4 - Processing Fee)

### Example Scenario

**Situation**: Client came to the branch on **May 7, 2026** to apply for a loan, but the officer was busy and couldn't register them until **May 8, 2026**.

**Solution**: 
- Officer registers the borrower on May 8
- In Step 3, officer selects **May 7, 2026** as the Application Date
- The loan application's `created_at` timestamp is set to May 7, 2026 00:00:00
- Reports and analytics will show the application was made on May 7

---

## ✅ Validation Rules

### Server-Side Validation

1. **Required**: Application date must be provided
   - Error: "Application date is required."

2. **Future Date Check**: Cannot select future dates
   - Error: "Application date cannot be in the future."

3. **Format Check**: Must be valid date format
   - Error: "Invalid application date format."

### Client-Side Validation

1. **HTML5 Required**: Browser enforces required field
2. **HTML5 Max Date**: Browser prevents selecting future dates (max="{{ today }}")
3. **Date Picker**: Browser provides native date picker widget

---

## 🔄 Consistency with Loan Application Form

The backdating implementation in the Register Borrower Wizard is **identical** to the standalone Loan Application form:

| Feature | Loan Application Form | Register Borrower Wizard |
|---------|----------------------|--------------------------|
| Field Name | Application Date | Application Date |
| Required | ✅ Yes | ✅ Yes |
| Default Value | Today | Today |
| Max Date | Today | Today |
| Help Text | ✅ Yes | ✅ Yes |
| Validation | Server + Client | Server + Client |
| Sets `created_at` | ✅ Yes | ✅ Yes |

---

## 📊 Database Impact

### Field Updated
- **Model**: `LoanApplication`
- **Field**: `created_at` (DateTimeField)
- **Value**: Timezone-aware datetime at start of selected date

### Example
```python
# User selects: 2026-05-07
# Database stores: 2026-05-07 00:00:00+02:00 (Africa/Lusaka timezone)
```

---

## 🧪 Testing Checklist

- [ ] Field appears in Step 3 of Register Borrower Wizard
- [ ] Field defaults to today's date
- [ ] Cannot select future dates (browser validation)
- [ ] Cannot submit without selecting a date (required validation)
- [ ] Selecting past date works correctly
- [ ] Application's `created_at` is set to selected date
- [ ] Error message appears if date is in future (server validation)
- [ ] Error message appears if date is missing (server validation)
- [ ] Help text is visible and clear
- [ ] Date picker widget works in browser

---

## 📝 Files Modified

1. **templates/clients/register_borrower_wizard.html**
   - Added application_date field in Step 3
   - Added help text and validation attributes

2. **clients/views.py**
   - Updated `_base_context()` to pass today's date
   - Updated `_handle_step3()` to process and validate application_date
   - Set `created_at` on LoanApplication based on selected date

---

## 🎯 Summary

**Feature**: Backdating for loan applications in Register Borrower Wizard

**Location**: Step 3 (Loan Application)

**Position**: Second field, right after borrower name

**Status**: ✅ Complete and ready to use

**Consistency**: Matches standalone Loan Application form exactly

**Validation**: Both client-side (HTML5) and server-side (Django)

**User Benefit**: Officers can register applications with the correct date, even if they're entering data after the fact

---

## 🔗 Related Documentation

- `LOAN_APPLICATION_BACKDATING.md` - Backdating in standalone loan application form
- `BACKDATING_QUICK_GUIDE.md` - Quick reference for backdating feature
- `ADD_BACKDATING_TO_REMAINING_FORMS.md` - List of forms that need backdating

---

**Date Added**: May 8, 2026  
**Added By**: Kiro AI Assistant  
**Status**: ✅ Complete
