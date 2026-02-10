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

    def get_existing_identifiers(self, limit: int = 1000) -> Dict[str, str]:
        """
        Get all unique identifiers from existing Zotero papers for deduplication.

        Args:
            limit: Maximum number of papers to check

        Returns:
            Dict mapping identifiers (arxiv_id, doi, title_normalized) to zotero_key
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled")
            return {}

        try:
            items = self.get_all_papers(limit=limit)
            identifier_map = {}

            for item in items:
                data = item.get('data', {})
                zotero_key = item.get('key', '')

                # Extract ArXiv ID from URL or extra field
                url = data.get('url', '').lower()
                if 'arxiv.org' in url:
                    # Extract ArXiv ID from URL like https://arxiv.org/abs/2301.12345
                    import re
                    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)
                    if match:
                        arxiv_id = match.group(1)
                        identifier_map[f"arxiv:{arxiv_id}"] = zotero_key

                # Extract DOI
                doi = data.get('DOI', '').strip()
                if doi:
                    identifier_map[f"doi:{doi.lower()}"] = zotero_key

                # Normalize title as fallback identifier
                title = data.get('title', '').strip().lower()
                if title:
                    # Remove common punctuation and extra spaces
                    normalized_title = ' '.join(title.split())
                    identifier_map[f"title:{normalized_title}"] = zotero_key

            logger.info(f"Loaded {len(identifier_map)} unique identifiers from Zotero")
            return identifier_map

        except Exception as e:
            logger.error(f"Error getting Zotero identifiers: {str(e)}")
            return {}

    def check_duplicate(self, paper: Dict, identifier_map: Dict[str, str]) -> Optional[str]:
        """
        Check if a paper already exists in Zotero.

        Args:
            paper: Paper dictionary with arxiv_id, doi, or title
            identifier_map: Map from get_existing_identifiers()

        Returns:
            Zotero key if duplicate found, None otherwise
        """
        # Check ArXiv ID
        if paper.get('arxiv_id'):
            arxiv_key = f"arxiv:{paper['arxiv_id']}"
            if arxiv_key in identifier_map:
                return identifier_map[arxiv_key]

        # Check DOI
        if paper.get('doi'):
            doi_key = f"doi:{paper['doi'].lower()}"
            if doi_key in identifier_map:
                return identifier_map[doi_key]

        # Check normalized title as fallback
        if paper.get('title'):
            title = paper['title'].strip().lower()
            normalized_title = ' '.join(title.split())
            title_key = f"title:{normalized_title}"
            if title_key in identifier_map:
                return identifier_map[title_key]

        return None

    def filter_new_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter out papers that already exist in Zotero library.

        Args:
            papers: List of paper dictionaries to check

        Returns:
            List of papers that don't exist in Zotero (new papers only)
        """
        if not self.enabled:
            logger.warning("Zotero is not enabled, returning all papers")
            return papers

        logger.info(f"Checking {len(papers)} papers for duplicates in Zotero...")

        # Get existing identifiers
        identifier_map = self.get_existing_identifiers()

        if not identifier_map:
            logger.warning("No existing identifiers found in Zotero")
            return papers

        # Filter out duplicates
        new_papers = []
        duplicate_count = 0

        for paper in papers:
            duplicate_key = self.check_duplicate(paper, identifier_map)
            if duplicate_key:
                duplicate_count += 1
                logger.debug(f"Duplicate found: {paper.get('title', '')[:60]}... (Zotero key: {duplicate_key})")
            else:
                new_papers.append(paper)

        logger.info(f"Filtered out {duplicate_count} duplicates, {len(new_papers)} new papers remain")

        return new_papers
