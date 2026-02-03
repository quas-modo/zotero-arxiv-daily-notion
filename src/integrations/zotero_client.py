"""Zotero API client for paper management (Optional)"""

import os
from typing import Dict, List, Optional
from pyzotero import zotero
from dotenv import load_dotenv
from ..utils.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)


class ZoteroClient:
    """Client for interacting with Zotero API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        library_id: Optional[str] = None,
        library_type: str = 'user'
    ):
        """
        Initialize Zotero client.

        Args:
            api_key: Zotero API key (defaults to ZOTERO_API_KEY env var)
            library_id: Zotero library ID (defaults to ZOTERO_LIBRARY_ID env var)
            library_type: Library type ('user' or 'group')
        """
        self.api_key = api_key or os.getenv('ZOTERO_API_KEY')
        self.library_id = library_id or os.getenv('ZOTERO_LIBRARY_ID')
        self.library_type = library_type or os.getenv('ZOTERO_LIBRARY_TYPE', 'user')

        if not self.api_key or not self.library_id:
            logger.warning("Zotero credentials not provided. Zotero integration disabled.")
            self.enabled = False
            return

        try:
            self.client = zotero.Zotero(
                self.library_id,
                self.library_type,
                self.api_key
            )
            self.enabled = True
            logger.info(f"Zotero client initialized (library_id: {self.library_id})")
        except Exception as e:
            logger.error(f"Failed to initialize Zotero client: {str(e)}")
            self.enabled = False

    def add_paper(self, paper: Dict) -> Optional[Dict]:
        """
        Add a paper to Zotero library.

        Args:
            paper: Paper dictionary

        Returns:
            Created Zotero item or None if failed
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled")
            return None

        try:
            # Create item template
            template = self.client.item_template('journalArticle')

            # Fill in paper details
            template['title'] = paper.get('title', '')
            template['abstractNote'] = paper.get('abstract', '')
            template['date'] = paper.get('published_date', '').strftime('%Y-%m-%d') if paper.get('published_date') else ''
            template['url'] = paper.get('entry_url', '')

            # Add creators (authors)
            template['creators'] = []
            for author_name in paper.get('authors', []):
                # Split name (simple approach)
                name_parts = author_name.split()
                if len(name_parts) >= 2:
                    template['creators'].append({
                        'creatorType': 'author',
                        'firstName': ' '.join(name_parts[:-1]),
                        'lastName': name_parts[-1]
                    })
                else:
                    template['creators'].append({
                        'creatorType': 'author',
                        'name': author_name
                    })

            # Add tags
            template['tags'] = []
            if paper.get('categories'):
                for cat in paper['categories']:
                    template['tags'].append({'tag': cat})

            # Add auto-imported tag
            template['tags'].append({'tag': 'auto-imported'})
            template['tags'].append({'tag': 'arxiv'})

            # Create item
            result = self.client.create_items([template])

            logger.info(f"✓ Added to Zotero: {paper.get('title', 'Unknown')[:60]}...")
            return result

        except Exception as e:
            logger.error(f"Error adding to Zotero: {str(e)}")
            return None

    def batch_add_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        Add multiple papers to Zotero.

        Args:
            papers: List of paper dictionaries

        Returns:
            List of created items
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled")
            return []

        results = []
        for paper in papers:
            result = self.add_paper(paper)
            if result:
                results.append(result)

        logger.info(f"Added {len(results)}/{len(papers)} papers to Zotero")
        return results

    def get_all_papers(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve all papers from Zotero library.

        Args:
            limit: Maximum number of papers to retrieve (default: 100)

        Returns:
            List of paper dictionaries from Zotero
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled")
            return []

        try:
            # Fetch items from library
            items = self.client.top(limit=limit)
            logger.info(f"Retrieved {len(items)} items from Zotero library")
            return items

        except Exception as e:
            logger.error(f"Error retrieving Zotero items: {str(e)}")
            return []

    def get_papers_for_embedding(self, limit: int = 100) -> List[Dict]:
        """
        Get papers formatted for embedding generation.

        Args:
            limit: Maximum number of papers to retrieve

        Returns:
            List of dicts with 'title', 'abstract', 'text' keys
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled")
            return []

        try:
            items = self.get_all_papers(limit=limit)
            papers = []

            for item in items:
                data = item.get('data', {})

                # Only include items with titles (actual papers)
                title = data.get('title', '').strip()
                if not title:
                    continue

                abstract = data.get('abstractNote', '').strip()

                # Combine title and abstract for embedding
                text = f"{title}"
                if abstract:
                    text += f" {abstract}"

                papers.append({
                    'title': title,
                    'abstract': abstract,
                    'text': text,
                    'zotero_key': item.get('key', ''),
                    'item_type': data.get('itemType', 'unknown')
                })

            logger.info(f"Prepared {len(papers)} Zotero papers for embedding")
            return papers

        except Exception as e:
            logger.error(f"Error preparing Zotero papers for embedding: {str(e)}")
            return []
