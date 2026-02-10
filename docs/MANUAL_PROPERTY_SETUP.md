# Manual Property Setup Guide

If the automatic setup doesn't work, add these properties manually:

## How to Add a Property in Notion

1. Open your database
2. Click the **"+"** button in the property header row (or scroll right and click "+")
3. Type the property name
4. Select the property type from the dropdown
5. Press Enter

## Required Properties

### 1. Title (Should Already Exist)
- **Name**: "Title" or "Name"
- **Type**: Title
- This is created automatically when you create a database

### 2. Authors
- **Name**: Authors
- **Type**: Text

### 3. Published Date
- **Name**: Published Date
- **Type**: Date

### 4. ArXiv ID
- **Name**: ArXiv ID
- **Type**: Text

### 5. PDF Link
- **Name**: PDF Link
- **Type**: URL

### 6. HTML Link
- **Name**: HTML Link
- **Type**: URL

### 7. GitHub
- **Name**: GitHub
- **Type**: URL

### 8. Categories
- **Name**: Categories
- **Type**: Multi-select
- (Options will be added automatically as papers are processed)

### 9. Keywords
- **Name**: Keywords
- **Type**: Multi-select
- (Options will be added automatically as papers are processed)

### 10. Relevance Score
- **Name**: Relevance Score
- **Type**: Number
- **Format**: Number (with 2 decimal places)

## Verification

After adding all properties, run:

```bash
python scripts/check_notion_properties.py
```

You should see:
```
✓ Existing properties: 10/10
✗ Missing properties: 0

✅ All expected properties exist with correct types!
Your database is correctly configured.
```

## Visual Example

Your database header should look like this:

```
┌──────┬─────────┬────────────────┬──────────┬──────────┬───────────┐
│Title │ Authors │ Published Date │ ArXiv ID │ PDF Link │ HTML Link │ ...
├──────┼─────────┼────────────────┼──────────┼──────────┼───────────┤
│      │         │                │          │          │           │
```

## Common Issues

### Issue: Can't find "+ Add Property"
**Fix**: Scroll to the right in your database until you see the "+" button

### Issue: Property type not available
**Fix**: Make sure you're creating properties in a database, not a page

### Issue: Properties added but script still shows 0
**Fix**: The integration is still not connected. Go back to Step 2 above.
