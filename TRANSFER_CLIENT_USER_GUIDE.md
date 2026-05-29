# Transfer Client Feature - User Guide

## Overview
The Transfer Client feature has been redesigned into a two-step workflow for easier client management.

---

## STEP 1: Find the Client

### How to Access
1. Navigate to **Dashboard** → **Admin** → **Transfer Client**
2. You'll see a list of all clients in a table format

### Search for a Client
Use the search bar to find clients by:
- **Name** (first or last name)
- **Phone number**
- **National ID (NRC)**
- **Email address**

**Example**: Type "Joyce" to find all clients named Joyce

### Filter Clients
Use the dropdown filters to narrow down results:

1. **Branch** (Admins only)
   - Filter by specific branch
   - Managers automatically see only their branch

2. **Group**
   - Filter by borrower group
   - Shows group name

3. **Loan Officer**
   - Filter by assigned loan officer
   - Shows officer name

4. **Loan Status**
   - **Has Active Loans**: Clients with active loans
   - **No Active Loans**: Clients without active loans

### Understanding the Table

| Column | Description |
|--------|-------------|
| **Client Name** | Full name and email |
| **NRC / Phone** | National ID and phone number |
| **Current Branch** | Branch where client is assigned |
| **Current Group** | Current borrower group |
| **Loan Officer** | Assigned loan officer |
| **Active Loans** | Badge showing loan status:<br>🟢 Green = No active loans<br>🟡 Yellow = Has active loans |
| **Action** | "Transfer" button |

### Pagination
- Shows 25 clients per page
- Use **Previous** / **Next** buttons to navigate
- Page numbers shown at bottom

---

## STEP 2: Transfer the Client

### Starting the Transfer
1. Find the client in the list (STEP 1)
2. Click the **"Transfer"** button next to their name
3. You'll see the transfer form for that specific client

### Client Information Card
Review the client's current details:
- Full name, phone, NRC, email
- Current branch
- Current group
- Current loan officer
- Active loan count

### Selecting Destination Group
1. Click the **"Destination Group"** dropdown
2. Select the new group
3. You'll see:
   - Group name
   - Current capacity (e.g., 5/25 members)
   - Branch name
   - Assigned loan officer

**Note**: The system will show you the branch and officer for the selected group below the dropdown.

### Providing a Reason
1. In the **"Reason for Transfer"** field, explain why you're transferring this client
2. Be specific (e.g., "Client relocated to new area", "Group consolidation", "Better officer match")

### Confirming the Transfer
1. Click **"Transfer Client"** button
2. A confirmation modal will appear
3. Review the details
4. Click **"Confirm Transfer"** to proceed
5. Or click **"Cancel"** to go back

### If Client Has Active Loans
If the client has active loans, you'll see a **yellow warning box**:
- Lists all active loans
- Shows current loan officer
- Asks if you want to transfer loans to the new officer

**Options**:
- **Transfer Client and Loans**: Transfers both client and their loans
- **Cancel**: Go back without transferring

---

## Business Rules

### ✅ What You CAN Do
- Transfer clients with active loans
- Transfer clients with pending loans
- Transfer clients between groups in the same branch
- Transfer clients between branches (admins only)

### ❌ What You CANNOT Do
- Transfer to an inactive group
- Transfer to a group at full capacity
- Transfer completed loans (they stay with original officer)
- Transfer rejected loans (they stay with original officer)

### 🔒 Manager Restrictions
- Managers can only transfer clients **within their own branch**
- Cannot see or transfer clients from other branches
- Cannot transfer clients to groups in other branches

### 🔓 Admin Permissions
- Admins can transfer clients **across all branches**
- Can see all clients in the system
- Can transfer to any active group

---

## What Happens After Transfer

### Immediate Changes
1. ✅ Client moved to new group
2. ✅ Client's branch updated (if group is in different branch)
3. ✅ Active/pending loans transferred to new officer (if confirmed)
4. ✅ Success message displayed
5. ✅ Returned to client list

### Audit Trail
Every transfer is logged with:
- Client name
- Previous group
- New group
- Reason for transfer
- Who performed the transfer
- Date and time
- Loans transferred (if applicable)

### Loan Officer Changes
If loans are transferred:
- New officer sees loans in their dashboard
- Old officer no longer sees the loans
- Loan history preserved
- Payment schedules unchanged

---

## Tips for Efficient Use

### 1. Use Filters First
Before searching, apply filters to narrow down the list:
- Filter by group if you know the client's current group
- Filter by loan status if you're consolidating clients with/without loans

### 2. Search Multiple Ways
If you can't find a client:
- Try searching by phone number instead of name
- Try searching by NRC
- Check if filters are applied (click "Reset" to clear)

### 3. Verify Before Transfer
Always check the client information card to ensure:
- You have the correct client
- You know their current group
- You understand their loan status

### 4. Provide Clear Reasons
Good reasons help with auditing:
- ✅ "Client relocated from Chazanga to Kamwala area"
- ✅ "Group consolidation - merging small groups"
- ✅ "Better officer-client match for improved service"
- ❌ "Transfer" (too vague)
- ❌ "Move" (not descriptive)

### 5. Check Group Capacity
Before transferring, ensure destination group has space:
- Look at capacity in dropdown (e.g., 5/25 members)
- If group is full, you'll get an error
- Consider creating a new group if needed

---

## Troubleshooting

### "Client not found"
- Check if filters are applied
- Try searching by different criteria (phone, NRC, email)
- Verify client exists in your branch (for managers)

### "Destination group is at capacity"
- Choose a different group with available space
- Or increase the group's max capacity (if you have permission)
- Or create a new group

### "Destination group is not active"
- Choose an active group
- Or reactivate the group (if you have permission)

### "You do not have access to this client"
- Managers can only access clients in their branch
- Contact an admin if you need to transfer across branches

### Transfer button doesn't work
- Ensure you've selected a destination group
- Ensure you've provided a reason
- Check for error messages at the top of the form

---

## Quick Reference

### Keyboard Shortcuts
- **Escape**: Close confirmation modal
- **Enter** in search: Apply search/filters

### Status Badges
- 🟢 **Green Badge**: No active loans - safe to transfer
- 🟡 **Yellow Badge**: Has active loans - will prompt for loan transfer

### Button Colors
- 🔵 **Blue**: Primary action (Transfer, Confirm)
- ⚫ **Gray**: Secondary action (Cancel, Back)
- 🟠 **Orange**: Warning action (Transfer with loans)

---

## Need Help?
- Contact your system administrator
- Check the audit logs for transfer history
- Review the Transfer Information box on each page for reminders
