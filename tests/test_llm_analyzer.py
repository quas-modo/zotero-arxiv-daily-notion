"""Tests for LLM analyzer"""

import unittest
import os
from src.analyzers.llm_analyzer import LLMAnalyzer


class TestLLMAnalyzer(unittest.TestCase):
    """Test cases for LLMAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        # Skip tests if no API key
        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest("OPENAI_API_KEY not set")

        self.analyzer = LLMAnalyzer(model='gpt-4o-mini')  # Use cheaper model for testing

    def test_generate_summary(self):
        """Test summary generation"""
        paper = {
            'title': 'Attention Is All You Need',
            'authors': ['Vaswani', 'Shazeer', 'Parmar'],
            'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
        }

        summary = self.analyzer.generate_summary(paper)

        # Should generate non-empty summary
        self.assertIsNotNone(summary)
        self.assertGreater(len(summary), 50)
        self.assertLess(len(summary), 1000)

    def test_generate_detailed_analysis(self):
        """Test detailed analysis generation"""
        paper = {
            'title': 'Attention Is All You Need',
            'authors': ['Vaswani', 'Shazeer', 'Parmar'],
            'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
            'categories': ['CL', 'LG'],
            'arxiv_id': '1706.03762'
        }

        analysis = self.analyzer.generate_detailed_analysis(paper)

        # Should generate comprehensive analysis
        self.assertIsNotNone(analysis)
        self.assertGreater(len(analysis), 200)

        # Should contain section headers
        self.assertIn('Background', analysis.lower() or 'Motivation' in analysis.lower())

    def test_analyze_paper(self):
        """Test full paper analysis"""
        paper = {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'authors': ['Devlin', 'Chang', 'Lee', 'Toutanova'],
            'abstract': 'We introduce BERT, a new language representation model which stands for Bidirectional Encoder Representations from Transformers.',
            'categories': ['CL'],
            'arxiv_id': '1810.04805'
        }

        result = self.analyzer.analyze_paper(paper)

        # Should have both summary and detailed analysis
        self.assertIn('summary', result)
        self.assertIn('detailed_analysis', result)
        self.assertIn('analysis_model', result)

        self.assertGreater(len(result['summary']), 50)
        self.assertGreater(len(result['detailed_analysis']), 200)


if __name__ == '__main__':
    unittest.main()
