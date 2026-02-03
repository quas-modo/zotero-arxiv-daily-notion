"""Tests for relevance filter"""

import unittest
from src.filters.relevance_filter import RelevanceFilter


class TestRelevanceFilter(unittest.TestCase):
    """Test cases for RelevanceFilter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.filter = RelevanceFilter(
            primary_keywords=['LLM', 'RAG', 'Multi-Agent'],
            secondary_keywords=['NLP', 'Transformer'],
            min_score=0.3,
            boost_github=True
        )

    def test_scoring_high_relevance(self):
        """Test scoring for highly relevant paper"""
        paper = {
            'title': 'Large Language Models for Retrieval Augmented Generation',
            'abstract': 'We present a novel approach using LLMs and RAG techniques...',
            'categories': ['AI', 'CL'],
            'github_links': ['https://github.com/example/llm-rag']
        }

        score, details = self.filter._calculate_relevance_score(paper)

        # Should have high score (multiple primary keywords + GitHub)
        self.assertGreater(score, 0.5)
        self.assertGreater(len(details['primary_matches']), 0)
        self.assertTrue(details['has_github'])

    def test_scoring_low_relevance(self):
        """Test scoring for low relevance paper"""
        paper = {
            'title': 'A Study on Quantum Computing',
            'abstract': 'This paper explores quantum algorithms...',
            'categories': ['QC'],
            'github_links': []
        }

        score, details = self.filter._calculate_relevance_score(paper)

        # Should have low score
        self.assertLess(score, 0.3)
        self.assertEqual(len(details['primary_matches']), 0)

    def test_filtering(self):
        """Test paper filtering"""
        papers = [
            {
                'title': 'LLM-based Multi-Agent Systems',
                'abstract': 'Using large language models for agent coordination...',
                'categories': ['AI'],
                'github_links': []
            },
            {
                'title': 'Unrelated Topic',
                'abstract': 'About something completely different...',
                'categories': ['OTHER'],
                'github_links': []
            },
            {
                'title': 'RAG for Question Answering',
                'abstract': 'Retrieval augmented generation improves QA...',
                'categories': ['CL'],
                'github_links': ['https://github.com/example/rag']
            }
        ]

        filtered = self.filter.filter_papers(papers, max_papers=2)

        # Should filter out low-relevance paper
        self.assertLessEqual(len(filtered), 2)

        # Top papers should have scores
        for paper in filtered:
            self.assertIn('relevance_score', paper)
            self.assertIn('match_details', paper)
            self.assertGreaterEqual(paper['relevance_score'], 0.3)

    def test_keyword_matching(self):
        """Test matched keywords extraction"""
        paper = {
            'title': 'Multi-Agent LLM Systems',
            'abstract': 'We explore multi-agent systems using transformers...',
            'categories': ['AI'],
        }

        matches = self.filter.get_matched_keywords(paper)

        # Should match both primary and secondary keywords
        self.assertIn('llm', matches)
        self.assertIn('multi-agent', matches)
        self.assertIn('transformer', matches)


if __name__ == '__main__':
    unittest.main()
