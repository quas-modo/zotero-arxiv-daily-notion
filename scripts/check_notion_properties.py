"""Check and display Notion database properties"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


def check_database_properties():
    """Check what properties exist in the Notion database"""

    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')

    if not api_key or not database_id:
        print("❌ Error: NOTION_API_KEY or NOTION_DATABASE_ID not set")
        print("\nPlease set these environment variables in your .env file:")
        print("  NOTION_API_KEY=your_integration_token")
        print("  NOTION_DATABASE_ID=your_database_id")
        return

    print("\n" + "="*80)
    print("NOTION DATABASE PROPERTY CHECK")
    print("="*80 + "\n")

    print(f"Database ID: {database_id[:8]}...{database_id[-8:]}\n")

    try:
        client = Client(auth=api_key)
        db = client.databases.retrieve(database_id=database_id)

        properties = db.get('properties', {})

        print(f"✓ Found {len(properties)} properties in database:\n")
        print("-" * 80)

        for prop_name, prop_details in properties.items():
            prop_type = prop_details.get('type', 'unknown')
            print(f"  • {prop_name:<25} ({prop_type})")

        print("-" * 80)

        # Expected properties for the system
        expected_properties = {
            'Title': 'title',
            'Authors': 'rich_text',
            'Published Date': 'date',
            'ArXiv ID': 'rich_text',
            'PDF Link': 'url',
            'HTML Link': 'url',
            'GitHub': 'url',
            'Categories': 'multi_select',
            'Keywords': 'multi_select',
            'Relevance Score': 'number'
        }

        print("\n" + "="*80)
        print("EXPECTED PROPERTIES FOR SYSTEM")
        print("="*80 + "\n")

        missing = []
        existing = []
        type_mismatch = []

        for prop_name, expected_type in expected_properties.items():
            if prop_name in properties:
                actual_type = properties[prop_name].get('type')
                if actual_type == expected_type:
                    existing.append(prop_name)
                    print(f"  ✓ {prop_name:<25} ({expected_type})")
                else:
                    type_mismatch.append((prop_name, expected_type, actual_type))
                    print(f"  ⚠️  {prop_name:<25} (expected: {expected_type}, found: {actual_type})")
            else:
                missing.append((prop_name, expected_type))
                print(f"  ✗ {prop_name:<25} ({expected_type}) - MISSING")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80 + "\n")

        print(f"  ✓ Existing properties: {len(existing)}/{len(expected_properties)}")
        print(f"  ✗ Missing properties: {len(missing)}")
        print(f"  ⚠️  Type mismatches: {len(type_mismatch)}")

        if missing:
            print("\n" + "="*80)
            print("HOW TO FIX - ADD MISSING PROPERTIES")
            print("="*80 + "\n")

            print("Go to your Notion database and add these properties:\n")

            for prop_name, prop_type in missing:
                notion_type = {
                    'rich_text': 'Text',
                    'date': 'Date',
                    'url': 'URL',
                    'multi_select': 'Multi-select',
                    'number': 'Number',
                    'title': 'Title'
                }.get(prop_type, prop_type)

                print(f"  {len([p for p in missing if missing.index((prop_name, prop_type)) < missing.index((prop_name, prop_type)) + 1])}. Add property: {prop_name}")
                print(f"     Type: {notion_type}")

                if prop_type == 'number':
                    print(f"     Format: Number (decimal, 2 places)")

                print()

        if type_mismatch:
            print("\n" + "="*80)
            print("TYPE MISMATCHES - PLEASE FIX")
            print("="*80 + "\n")

            for prop_name, expected, actual in type_mismatch:
                print(f"  • {prop_name}: Change from '{actual}' to '{expected}'")

        if not missing and not type_mismatch:
            print("\n✅ All expected properties exist with correct types!")
            print("Your database is correctly configured.")

        print("\n" + "="*80)

    except Exception as e:
        print(f"❌ Error accessing Notion database: {str(e)}\n")
        print("Possible issues:")
        print("  1. Invalid API key or database ID")
        print("  2. Integration not connected to the database")
        print("  3. Network connection issue")
        print("\nTo fix:")
        print("  1. Check your .env file has correct credentials")
        print("  2. Go to your Notion database → ... → Connections")
        print("  3. Add your integration to the database")


if __name__ == '__main__':
    check_database_properties()
