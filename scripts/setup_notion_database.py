"""Automated Notion database setup - Add required properties"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


def setup_database_properties():
    """Add required properties to Notion database"""

    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')

    if not api_key or not database_id:
        print("❌ Error: NOTION_API_KEY or NOTION_DATABASE_ID not set")
        return False

    print("\n" + "="*80)
    print("NOTION DATABASE SETUP - ADD PROPERTIES")
    print("="*80 + "\n")

    print(f"Database ID: {database_id[:8]}...{database_id[-8:]}\n")

    # Required properties configuration
    required_properties = {
        'Authors': {
            'rich_text': {}
        },
        'Published Date': {
            'date': {}
        },
        'ArXiv ID': {
            'rich_text': {}
        },
        'PDF Link': {
            'url': {}
        },
        'HTML Link': {
            'url': {}
        },
        'GitHub': {
            'url': {}
        },
        'Categories': {
            'multi_select': {
                'options': []
            }
        },
        'Keywords': {
            'multi_select': {
                'options': []
            }
        },
        'Relevance Score': {
            'number': {
                'format': 'number'
            }
        }
    }

    try:
        client = Client(auth=api_key)

        # Get current properties
        db = client.databases.retrieve(database_id=database_id)
        existing_properties = db.get('properties', {})

        print(f"Current properties: {len(existing_properties)}\n")

        if len(existing_properties) == 0:
            print("⚠️  WARNING: Database has 0 properties!")
            print("\nThis usually means the integration is NOT connected to the database.\n")
            print("Please follow these steps:")
            print("  1. Open your Notion database in your browser")
            print("  2. Click the ••• (three dots) menu in the top right")
            print("  3. Click 'Connections' or 'Add connections'")
            print("  4. Select your integration and click 'Confirm'")
            print("  5. Re-run this script\n")
            print("="*80)
            return False

        # Check which properties are missing
        missing_properties = {}
        for prop_name, prop_config in required_properties.items():
            if prop_name not in existing_properties:
                missing_properties[prop_name] = prop_config

        if not missing_properties:
            print("✅ All required properties already exist!\n")
            print("Your database is properly configured.")
            return True

        print(f"Found {len(missing_properties)} missing properties:\n")

        for prop_name in missing_properties.keys():
            prop_type = list(missing_properties[prop_name].keys())[0]
            print(f"  • {prop_name} ({prop_type})")

        print("\n" + "="*80)
        print("ADDING PROPERTIES")
        print("="*80 + "\n")

        # Prepare update payload
        # We need to include all existing properties plus new ones
        all_properties = existing_properties.copy()

        added = []
        failed = []

        for prop_name, prop_config in missing_properties.items():
            try:
                all_properties[prop_name] = prop_config
                prop_type = list(prop_config.keys())[0]
                print(f"  ✓ Adding: {prop_name} ({prop_type})")
                added.append(prop_name)
            except Exception as e:
                print(f"  ✗ Failed: {prop_name} - {str(e)}")
                failed.append(prop_name)

        # Update database with new properties
        print("\nUpdating database...")

        try:
            client.databases.update(
                database_id=database_id,
                properties=all_properties
            )

            print("\n" + "="*80)
            print("SETUP COMPLETE")
            print("="*80 + "\n")

            print(f"  ✓ Successfully added {len(added)} properties")
            if failed:
                print(f"  ✗ Failed to add {len(failed)} properties")
                for prop in failed:
                    print(f"    - {prop}")

            print("\n✅ Your Notion database is now configured!\n")
            print("You can verify by running:")
            print("  python scripts/check_notion_properties.py")

            return len(failed) == 0

        except Exception as e:
            print(f"\n❌ Error updating database: {str(e)}\n")
            print("This might be because:")
            print("  1. The integration doesn't have 'Update content' permission")
            print("  2. You need to add properties manually in Notion")
            print("\nPlease add the properties manually (see docs/NOTION_DATABASE_SETUP.md)")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        print("Please check:")
        print("  1. Your Notion API key is correct")
        print("  2. Your database ID is correct")
        print("  3. The integration is connected to the database")
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Setup Notion database properties')
    parser.add_argument('--force', action='store_true', help='Force re-create all properties')

    args = parser.parse_args()

    success = setup_database_properties()

    if success:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80 + "\n")
        print("1. Run a test to verify everything works:")
        print("   python src/main.py --dry-run --max-papers 1")
        print("\n2. If test succeeds, run the full pipeline:")
        print("   python src/main.py")
        print()
    else:
        print("\n" + "="*80)
        print("SETUP FAILED")
        print("="*80 + "\n")
        print("Please manually add properties to your Notion database.")
        print("See: docs/NOTION_DATABASE_SETUP.md for detailed instructions")
        print()
        sys.exit(1)
