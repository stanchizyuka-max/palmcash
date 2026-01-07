# Admin Officer Transfer - NameError Fix

## Problem
When trying to transfer a loan officer to a different branch via the admin dashboard, the application threw a `NameError`:

```
NameError at /dashboard/admin/officers/transfer/
name 'messages' is not defined
```

**Error Location**: `/home/stan13/palmcash/palmcash/dashboard/views.py`, line 1935

## Root Cause
The `admin_officer_transfer()` function in `dashboard/views.py` was using Django's `messages` framework to display success/error messages, but the `messages` module was not imported at the top of the file.

Additionally, the `redirect` function was also not imported, which would have caused another error after the messages issue was fixed.

## Solution
Added the missing imports to the top of `dashboard/views.py`:

```python
from django.shortcuts import render, redirect
from django.contrib import messages
```

## Changes Made
**File**: `palmcash/palmcash/dashboard/views.py`

**Before**:
```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
```

**After**:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
```

## Verification
The fix has been applied and verified. The `admin_officer_transfer()` function now has access to:
- `messages.success()` - to display success messages
- `messages.error()` - to display error messages
- `redirect()` - to redirect after the transfer

## Testing
To verify the fix works:
1. Log in as admin
2. Go to Dashboard → Admin → Officers
3. Click "Transfer Officer"
4. Select an officer and new branch
5. Click "Transfer"
6. You should see a success message and be redirected to the officers list

## Related Functions
The following functions in `dashboard/views.py` also use the `messages` framework:
- `admin_officer_transfer()` - Transfer officers between branches
- `admin_transfer_history()` - View transfer history
- Other admin functions that provide user feedback

All these functions now have access to the `messages` module.
