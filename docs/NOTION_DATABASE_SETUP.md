# Notion Database Setup Guide

## Issue: Database Properties Not Accessible

Your Notion database appears to have 0 properties, which means either:
1. The integration is not connected to the database (**most likely**)
2. The database is empty/new
3. The database ID is incorrect

## Quick Fix: Connect Integration to Database

### Step 1: Connect Your Integration

1. Open your Notion database in your browser
2. Click the **`•••`** (three dots) menu in the top right
3. Scroll down and click **"Connections"** or **"Add connections"**
4. Find and select your integration (the one you created for this system)
5. Click **"Confirm"** to grant access

### Step 2: Verify Connection

Run this command to verify the connection:

```bash
python scripts/check_notion_properties.py
```

You should see a message saying "Found X properties" (likely 1 property: "Name" or "Title").

---

## Option 2: Create Properties Manually

If your database is new or missing properties, add them manually:

### Required Properties

Open your Notion database and add these properties (click **"+"** in the property bar):

1. **Title** (should already exist as "Name")
   - Type: Title
   - This is required by Notion

2. **Authors**
   - Type: Text
   - For paper authors

3. **Published Date**
   - Type: Date
   - For publication date

4. **ArXiv ID**
   - Type: Text
   - For the paper's ArXiv ID

5. **PDF Link**
   - Type: URL
   - For the PDF download link

6. **HTML Link**
   - Type: URL
   - For the HTML version link

7. **GitHub**
   - Type: URL
   - For GitHub repository links

8. **Categories**
   - Type: Multi-select
   - For ArXiv categories (cs.AI, cs.LG, etc.)

9. **Keywords**
   - Type: Multi-select
   - For matched keywords

10. **Relevance Score**
    - Type: Number
    - Format: Number with 2 decimal places
    - For the relevance score

---

## Option 3: Use the Automated Setup Script

I'll create a script that can help set up properties automatically:

```bash
python scripts/setup_notion_database.py
```

(Coming next...)

---

## Troubleshooting

### "0 properties found" Error

**Cause**: Integration not connected to database

**Fix**:
1. Go to your Notion database
2. Click `•••` → Connections
3. Add your integration
4. Re-run `check_notion_properties.py`

### "Integration not found" Error

**Cause**: Wrong integration token or it was deleted

**Fix**:
1. Go to https://www.notion.so/my-integrations
2. Check your integration exists
3. Copy the **Internal Integration Token**
4. Update `.env` file: `NOTION_API_KEY=secret_...`

### "Database not found" Error

**Cause**: Wrong database ID or no access

**Fix**:
1. Open your Notion database
2. Copy the URL: `https://notion.so/workspace/DATABASE_ID?v=...`
3. The DATABASE_ID is the part between the last `/` and `?`
4. Update `.env` file: `NOTION_DATABASE_ID=...`

---

## Quick Video Guide

1. **Connect Integration**: https://www.notion.so/help/add-and-manage-connections-with-the-api
2. **Create Properties**: Click "+" in property bar, select type

---

## After Setup

Run this to verify everything works:

```bash
python scripts/check_notion_properties.py
```

You should see:
```
✓ Found 10+ properties in database:
  • Title (title)
  • Authors (rich_text)
  • Published Date (date)
  ...

✅ All expected properties exist with correct types!
Your database is correctly configured.
```

Then test the integration:

```bash
python src/main.py --dry-run --max-papers 1
```

This will process 1 paper without actually creating the Notion entry, so you can verify the system works.
