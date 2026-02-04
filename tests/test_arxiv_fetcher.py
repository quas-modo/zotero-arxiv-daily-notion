"""Tests for ArXiv fetcher"""

import sys
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fetchers.arxiv_fetcher import ArxivFetcher


class TestArxivFetcher(unittest.TestCase):
    """Test cases for ArxivFetcher class"""

    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = ArxivFetcher(
            categories=['cs.AI', 'cs.CL'],
            max_results=5
        )

    def test_fetch_papers(self):
        """Test fetching papers from ArXiv"""
        papers = self.fetcher.fetch_daily_papers(days_back=7)

        # Should fetch some papers
        self.assertGreater(len(papers), 0)

        # Check paper structure
        if papers:
            paper = papers[0]
            self.assertIn('arxiv_id', paper)
            self.assertIn('title', paper)
            self.assertIn('authors', paper)
            self.assertIn('abstract', paper)
            self.assertIn('pdf_url', paper)
            self.assertIn('categories', paper)

    def test_fetch_by_id(self):
        """Test fetching specific paper by ID"""
        # Fetch a known paper (GPT-3 paper)
        paper = self.fetcher.fetch_paper_by_id('2005.14165')

        self.assertIsNotNone(paper)
        if paper:
            self.assertEqual(paper['arxiv_id'], '2005.14165')
            self.assertIn('GPT-3', paper['title'] or '')

    def test_github_extraction(self):
        """Test GitHub link extraction"""
        # This is harder to test without knowing which papers have GitHub links
        # So we'll just verify the method doesn't crash
        papers = self.fetcher.fetch_daily_papers(days_back=7)

        for paper in papers[:3]:
            # Should have github_links field (may be empty list)
            self.assertIn('github_links', paper)
            self.assertIsInstance(paper['github_links'], list)


if __name__ == '__main__':
    unittest.main()
