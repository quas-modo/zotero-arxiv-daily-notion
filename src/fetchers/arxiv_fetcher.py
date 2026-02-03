"""ArXiv paper fetching functionality"""

import arxiv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ArxivFetcher:
    """Fetches papers from ArXiv API"""

    def __init__(self, categories: List[str], max_results: int = 50):
        """
        Initialize ArXiv fetcher.

        Args:
            categories: List of ArXiv categories (e.g., ['cs.AI', 'cs.CL'])
            max_results: Maximum number of papers to fetch
        """
        self.categories = categories
        self.max_results = max_results
        self.client = arxiv.Client()

    def fetch_daily_papers(self, days_back: int = 1) -> List[Dict]:
        """
        Fetch papers submitted in the last N days.

        Args:
            days_back: Number of days to look back

        Returns:
            List of paper dictionaries
        """
        logger.info(f"Fetching papers from ArXiv (categories: {', '.join(self.categories)})")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        papers = []

        for category in self.categories:
            try:
                # Build search query for category and date range
                query = f"cat:{category}"

                # Search ArXiv
                search = arxiv.Search(
                    query=query,
                    max_results=self.max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                # Fetch results
                results = self.client.results(search)

                for result in results:
                    # Filter by submission date
                    if result.published.replace(tzinfo=None) < start_date:
                        continue

                    paper_dict = self._parse_paper(result)

                    # Avoid duplicates (papers can be in multiple categories)
                    if not any(p['arxiv_id'] == paper_dict['arxiv_id'] for p in papers):
                        papers.append(paper_dict)

                logger.info(f"Found {len([p for p in papers if category in p['categories']])} papers in {category}")

            except Exception as e:
                logger.error(f"Error fetching papers from {category}: {str(e)}")
                continue

        logger.info(f"Total papers fetched: {len(papers)}")
        return papers

    def _parse_paper(self, result: arxiv.Result) -> Dict:
        """
        Parse ArXiv result into a standardized dictionary.

        Args:
            result: ArXiv search result

        Returns:
            Paper dictionary with standardized fields
        """
        # Extract ArXiv ID
        arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]

        # Extract GitHub links from abstract or comments
        github_links = self._extract_github_links(result)

        # Get categories
        categories = [cat.split('.')[-1] for cat in result.categories]

        return {
            'arxiv_id': arxiv_id,
            'title': result.title,
            'authors': [author.name for author in result.authors],
            'abstract': result.summary.replace('\n', ' ').strip(),
            'published_date': result.published,
            'updated_date': result.updated,
            'categories': categories,
            'primary_category': result.primary_category.split('.')[-1] if result.primary_category else categories[0],
            'pdf_url': result.pdf_url,
            'entry_url': result.entry_id,
            'github_links': github_links,
            'comment': result.comment if result.comment else "",
        }

    def _extract_github_links(self, result: arxiv.Result) -> List[str]:
        """Extract GitHub repository links from paper metadata"""
        github_links = []

        # Pattern to match GitHub URLs
        github_pattern = r'https?://github\.com/[\w\-]+/[\w\-.]+'

        # Search in comment field
        if result.comment:
            links = re.findall(github_pattern, result.comment)
            github_links.extend(links)

        # Search in abstract (some papers include code links there)
        links = re.findall(github_pattern, result.summary)
        github_links.extend(links)

        # Remove duplicates
        return list(set(github_links))

    def fetch_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch a specific paper by its ArXiv ID.

        Args:
            arxiv_id: ArXiv paper ID (e.g., '2301.12345')

        Returns:
            Paper dictionary or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            return self._parse_paper(result)
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {str(e)}")
            return None

    def search_by_keywords(self, keywords: List[str], max_results: int = 20) -> List[Dict]:
        """
        Search papers by keywords.

        Args:
            keywords: List of search keywords
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        # Build search query
        query = " OR ".join([f'"{kw}"' for kw in keywords])

        logger.info(f"Searching ArXiv with query: {query}")

        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )

            results = self.client.results(search)
            papers = [self._parse_paper(result) for result in results]

            logger.info(f"Found {len(papers)} papers matching keywords")
            return papers

        except Exception as e:
            logger.error(f"Error searching papers: {str(e)}")
            return []
