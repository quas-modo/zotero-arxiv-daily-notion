# Why Only "Title" Works - Quick Answer

## The Problem

**Error**: "Inserting attributes except title failed"

**Root Cause**: Your Notion integration is **not connected** to the database.

## Why This Happens

```
Your System          Notion Integration          Notion Database
    │                        │                          │
    ├─ Send paper data ────→ │                          │
    │                        ├─ Try to insert ────→ ❌  │ (No access)
    │                        │                          │
    │                        │ ← Only "Title" works     │
    │                        │   (Required by Notion)   │
    └─ Receive error ←───────┘                          │
```

## The Fix (2 Minutes)

### Step 1: Connect Integration
```
1. Open Notion database in browser
2. Click ••• (three dots) → "Add connections"
3. Select your integration
4. Click "Confirm"
```

### Step 2: Add Properties
```bash
python scripts/setup_notion_database.py
```

This automatically adds:
- Authors (Text)
- Published Date (Date)
- ArXiv ID (Text)
- PDF Link (URL)
- HTML Link (URL)
- GitHub (URL)
- Categories (Multi-select)
- Keywords (Multi-select)
- Relevance Score (Number)

### Step 3: Verify
```bash
python scripts/check_notion_properties.py
```

Should show: "✅ All expected properties exist!"

## After Setup

Run a test:
```bash
python src/main.py --dry-run --max-papers 1
```

Then run normally:
```bash
python src/main.py
```

## Visual Guide

**Before (Not Connected)**:
```
Integration: ❌ No access to database
Properties visible: 0
Can insert: Only "Title" (required by Notion)
```

**After (Connected)**:
```
Integration: ✅ Connected to database
Properties visible: 10
Can insert: All properties (Title, Authors, Date, etc.)
```

## Still Not Working?

Check these:

1. **Wrong Database ID**
   ```bash
   # Get database ID from URL:
   # https://notion.so/workspace/DATABASE_ID?v=VIEW_ID
   # Update .env:
   NOTION_DATABASE_ID=your_database_id_here
   ```

2. **Wrong API Key**
   ```bash
   # Get from: https://www.notion.so/my-integrations
   # Update .env:
   NOTION_API_KEY=secret_your_token_here
   ```

3. **Integration Deleted**
   - Create a new integration at https://www.notion.so/my-integrations
   - Copy the token
   - Update .env file
   - Connect to database (Step 1 above)

## Summary

**The issue**: Integration sees 0 properties because it's not connected
**The fix**: Connect integration → Add properties → Test
**Time needed**: ~2 minutes

See full guide: `docs/NOTION_DATABASE_SETUP.md`
