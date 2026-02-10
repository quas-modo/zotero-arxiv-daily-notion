"""Utility to read scholar-inbox.com exported recommendations"""

import json
import csv
from pathlib import Path
from typing import Dict, List
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ScholarInboxReader:
    """Reader for scholar-inbox.com exported data"""

    @staticmethod
    def read_json(file_path: str) -> List[Dict]:
        """
        Read scholar-inbox data from JSON export.

        Expected JSON format:
        [
            {
                "title": "Paper Title",
                "abstract": "Paper abstract...",
                "authors": ["Author 1", "Author 2"],
                "arxiv_id": "2301.12345",  # optional
                "url": "https://...",  # optional
            },
            ...
        ]

        Args:
            file_path: Path to JSON file

        Returns:
            List of paper dicts formatted for embedding
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Scholar-inbox file not found: {file_path}")
            return []

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            papers = []
            for item in data:
                title = item.get('title', '').strip()
                if not title:
                    continue

                abstract = item.get('abstract', '').strip()

                # Combine title and abstract for embedding
                text = f"{title}"
                if abstract:
                    text += f" {abstract}"

                papers.append({
                    'title': title,
                    'abstract': abstract,
                    'text': text,
                    'source': 'scholar-inbox'
                })

            logger.info(f"✓ Loaded {len(papers)} papers from scholar-inbox JSON: {file_path}")
            return papers

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading scholar-inbox file: {e}")
            return []

    @staticmethod
    def read_csv(file_path: str) -> List[Dict]:
        """
        Read scholar-inbox data from CSV export.

        Expected CSV columns:
        - title (required)
        - abstract (optional)
        - authors (optional, comma-separated)
        - arxiv_id (optional)
        - url (optional)

        Args:
            file_path: Path to CSV file

        Returns:
            List of paper dicts formatted for embedding
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Scholar-inbox file not found: {file_path}")
            return []

        try:
            papers = []

            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    title = row.get('title', '').strip()
                    if not title:
                        continue

                    abstract = row.get('abstract', '').strip()

                    # Combine title and abstract for embedding
                    text = f"{title}"
                    if abstract:
                        text += f" {abstract}"

                    papers.append({
                        'title': title,
                        'abstract': abstract,
                        'text': text,
                        'source': 'scholar-inbox'
                    })

            logger.info(f"✓ Loaded {len(papers)} papers from scholar-inbox CSV: {file_path}")
            return papers

        except Exception as e:
            logger.error(f"Error reading scholar-inbox CSV: {e}")
            return []

    @staticmethod
    def read_file(file_path: str) -> List[Dict]:
        """
        Auto-detect format and read scholar-inbox data.

        Args:
            file_path: Path to JSON or CSV file

        Returns:
            List of paper dicts formatted for embedding
        """
        path = Path(file_path)

        if not path.exists():
            logger.info(f"Scholar-inbox file not found: {file_path} (skipping)")
            return []

        # Detect format by extension
        if path.suffix.lower() == '.json':
            return ScholarInboxReader.read_json(file_path)
        elif path.suffix.lower() == '.csv':
            return ScholarInboxReader.read_csv(file_path)
        else:
            logger.warning(f"Unsupported file format: {path.suffix}. Use .json or .csv")
            return []
