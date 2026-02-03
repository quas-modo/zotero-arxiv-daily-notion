"""Notion API client for paper management"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv
from ..utils.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)


class NotionClient:
    """Client for interacting with Notion API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None
    ):
        """
        Initialize Notion client.

        Args:
            api_key: Notion integration token (defaults to NOTION_API_KEY env var)
            database_id: Notion database ID (defaults to NOTION_DATABASE_ID env var)
        """
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        if not self.api_key:
            raise ValueError("Notion API key not provided. Set NOTION_API_KEY environment variable.")

        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        if not self.database_id:
            raise ValueError("Notion database ID not provided. Set NOTION_DATABASE_ID environment variable.")

        self.client = Client(auth=self.api_key)
        logger.info(f"Notion client initialized with database: {self.database_id[:8]}...")

    def create_paper_entry(self, paper: Dict) -> Dict:
        """
        Create a new entry in Notion database for a paper.

        Args:
            paper: Paper dictionary with all metadata and analysis

        Returns:
            Created Notion page object
        """
        logger.info(f"Creating Notion entry for: {paper.get('title', 'Unknown')[:60]}...")

        try:
            # Prepare properties
            properties = self._format_properties(paper)

            # Prepare content blocks
            children = self._format_content_blocks(paper)

            # Create page
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )

            logger.info(f"✓ Notion entry created: {response['id']}")
            return response

        except Exception as e:
            logger.error(f"Error creating Notion entry: {str(e)}")
            raise

    def _format_properties(self, paper: Dict) -> Dict:
        """Format paper data as Notion properties"""

        properties = {
            # Title (required, title type)
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": paper.get('title', 'Untitled')[:2000]
                        }
                    }
                ]
            }
        }

        # Authors (rich text)
        authors_text = ', '.join(paper.get('authors', [])[:10])
        if authors_text:
            properties["Authors"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": authors_text[:2000]
                        }
                    }
                ]
            }

        # Published Date (date)
        if paper.get('published_date'):
            pub_date = paper['published_date']
            if isinstance(pub_date, datetime):
                properties["Published Date"] = {
                    "date": {
                        "start": pub_date.strftime('%Y-%m-%d')
                    }
                }

        # ArXiv ID (rich text)
        if paper.get('arxiv_id'):
            properties["ArXiv ID"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": paper['arxiv_id']
                        }
                    }
                ]
            }

        # PDF Link (url)
        if paper.get('pdf_url'):
            properties["PDF Link"] = {
                "url": paper['pdf_url']
            }

        # GitHub Link (url)
        if paper.get('github_links') and paper['github_links']:
            properties["GitHub"] = {
                "url": paper['github_links'][0]
            }

        # Categories (multi-select)
        if paper.get('categories'):
            properties["Categories"] = {
                "multi_select": [
                    {"name": cat[:100]} for cat in paper['categories'][:10]
                ]
            }

        # Keywords/Tags (multi-select)
        if paper.get('match_details', {}).get('primary_matches'):
            keywords = paper['match_details']['primary_matches']
            if paper['match_details'].get('secondary_matches'):
                keywords += paper['match_details']['secondary_matches']

            properties["Keywords"] = {
                "multi_select": [
                    {"name": kw[:100]} for kw in keywords[:10]
                ]
            }

        # Relevance Score (number)
        if 'relevance_score' in paper:
            properties["Relevance Score"] = {
                "number": round(paper['relevance_score'], 2)
            }

        return properties

    def _format_content_blocks(self, paper: Dict) -> List[Dict]:
        """Format paper content as Notion blocks"""

        blocks = []

        # Add abstract
        if paper.get('abstract'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Abstract"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": paper['abstract'][:2000]}}]
                }
            })

        # Add summary if available
        if paper.get('summary'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Summary (TL;DR)"}}]
                }
            })

            # Split summary into chunks (Notion has 2000 char limit per block)
            summary_text = paper['summary']
            for chunk in self._split_text(summary_text, 2000):
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })

        # Add detailed analysis if available
        if paper.get('detailed_analysis'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Detailed Analysis"}}]
                }
            })

            # Process markdown-style content
            analysis_text = paper['detailed_analysis']
            blocks.extend(self._parse_markdown_to_blocks(analysis_text))

        # Add Chinese translations section
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "中文翻译 (Chinese Translation)"}}]
            }
        })

        # Add Chinese abstract
        if paper.get('abstract_zh'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "摘要 (Abstract)"}}]
                }
            })
            for chunk in self._split_text(paper['abstract_zh'], 2000):
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })

        # Add Chinese summary
        if paper.get('summary_zh'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "概要 (Summary)"}}]
                }
            })
            for chunk in self._split_text(paper['summary_zh'], 2000):
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })

        # Add Chinese detailed analysis
        if paper.get('detailed_analysis_zh'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "详细分析 (Detailed Analysis)"}}]
                }
            })
            blocks.extend(self._parse_markdown_to_blocks(paper['detailed_analysis_zh']))

        # Add links section
        links = []
        if paper.get('pdf_url'):
            links.append(f"📄 PDF: {paper['pdf_url']}")
        if paper.get('entry_url'):
            links.append(f"🔗 ArXiv: {paper['entry_url']}")
        if paper.get('github_links'):
            for i, link in enumerate(paper['github_links'][:3], 1):
                links.append(f"💻 GitHub: {link}")

        if links:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Links"}}]
                }
            })
            for link_text in links:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": link_text}}]
                    }
                })

        return blocks

    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """Split text into chunks that fit Notion's character limit"""
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            # Try to split at paragraph or sentence
            split_pos = text.rfind('\n\n', 0, max_length)
            if split_pos == -1:
                split_pos = text.rfind('. ', 0, max_length)
            if split_pos == -1:
                split_pos = max_length

            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip()

        return chunks

    def _parse_markdown_to_blocks(self, text: str) -> List[Dict]:
        """Parse markdown-style text into Notion blocks"""
        blocks = []
        lines = text.split('\n')

        current_paragraph = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    for chunk in self._split_text(para_text, 2000):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        })
                    current_paragraph = []
                continue

            # Heading 2 (##)
            if line.startswith('## '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    for chunk in self._split_text(para_text, 2000):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        })
                    current_paragraph = []

                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[3:][:2000]}}]
                    }
                })
            # Bullet point
            elif line.startswith('- ') or line.startswith('* '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    for chunk in self._split_text(para_text, 2000):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        })
                    current_paragraph = []

                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:][:2000]}}]
                    }
                })
            else:
                current_paragraph.append(line)

        # Add remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            for chunk in self._split_text(para_text, 2000):
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })

        return blocks

    def batch_create_entries(self, papers: List[Dict]) -> List[Dict]:
        """
        Create multiple Notion entries.

        Args:
            papers: List of paper dictionaries

        Returns:
            List of created Notion pages
        """
        logger.info(f"Creating {len(papers)} Notion entries...")

        results = []
        for i, paper in enumerate(papers, 1):
            try:
                logger.info(f"Processing paper {i}/{len(papers)}")
                result = self.create_paper_entry(paper)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create entry for paper {i}: {str(e)}")
                continue

        logger.info(f"Successfully created {len(results)}/{len(papers)} Notion entries")
        return results

    def check_database_exists(self) -> bool:
        """Check if the configured database exists and is accessible"""
        try:
            self.client.databases.retrieve(database_id=self.database_id)
            logger.info("✓ Database is accessible")
            return True
        except Exception as e:
            logger.error(f"Cannot access database: {str(e)}")
            return False

    def get_database_properties(self) -> Dict:
        """Get the properties schema of the database"""
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            return db.get('properties', {})
        except Exception as e:
            logger.error(f"Error retrieving database properties: {str(e)}")
            return {}
