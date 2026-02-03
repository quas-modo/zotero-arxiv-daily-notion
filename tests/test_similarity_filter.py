"""Tests for similarity-based filtering"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from src.filters.similarity_filter import SimilarityFilter


@pytest.fixture
def sample_reference_papers():
    """Sample reference papers for testing"""
    return [
        {
            'title': 'Attention Is All You Need',
            'abstract': 'We propose the Transformer, a model architecture based solely on attention mechanisms.',
            'text': 'Attention Is All You Need We propose the Transformer, a model architecture based solely on attention mechanisms.'
        },
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'abstract': 'We introduce BERT, a new language representation model using bidirectional transformers.',
            'text': 'BERT: Pre-training of Deep Bidirectional Transformers We introduce BERT, a new language representation model using bidirectional transformers.'
        },
        {
            'title': 'GPT-3: Language Models are Few-Shot Learners',
            'abstract': 'We train GPT-3, a 175B parameter autoregressive language model.',
            'text': 'GPT-3: Language Models are Few-Shot Learners We train GPT-3, a 175B parameter autoregressive language model.'
        }
    ]


@pytest.fixture
def sample_new_papers():
    """Sample new papers to filter"""
    return [
        {
            'title': 'T5: Text-to-Text Transfer Transformer',
            'abstract': 'We introduce T5, a unified framework that converts all text processing problems to text-to-text format using transformers.',
            'arxiv_id': '1910.10683'
        },
        {
            'title': 'Convolutional Neural Networks for Image Classification',
            'abstract': 'We present a novel CNN architecture for classifying images into categories.',
            'arxiv_id': '1234.56789'
        },
        {
            'title': 'Reinforcement Learning for Robotics',
            'abstract': 'We apply deep reinforcement learning to robotic manipulation tasks.',
            'arxiv_id': '9876.54321'
        }
    ]


def test_similarity_filter_initialization():
    """Test SimilarityFilter initialization"""
    filter_obj = SimilarityFilter(
        min_similarity=0.7,
        top_k=5,
        model_name='all-MiniLM-L6-v2'
    )

    assert filter_obj.min_similarity == 0.7
    assert filter_obj.top_k == 5
    assert filter_obj.model_name == 'all-MiniLM-L6-v2'
    assert filter_obj.model is not None


def test_add_reference_papers(sample_reference_papers):
    """Test adding reference papers"""
    filter_obj = SimilarityFilter(enable_cache=False)

    filter_obj.add_reference_papers(sample_reference_papers, source='test')

    assert len(filter_obj.reference_papers) == 3
    assert filter_obj.reference_embeddings is not None
    assert filter_obj.reference_embeddings.shape[0] == 3


def test_filter_papers_with_similarity(sample_reference_papers, sample_new_papers):
    """Test filtering papers based on similarity"""
    filter_obj = SimilarityFilter(
        min_similarity=0.3,
        top_k=10,
        enable_cache=False
    )

    # Add reference papers (all transformer/NLP related)
    filter_obj.add_reference_papers(sample_reference_papers, source='test')

    # Filter new papers
    filtered = filter_obj.filter_papers(sample_new_papers)

    # Should have similarity scores
    assert all('similarity_score' in p for p in filtered)

    # T5 paper should have high similarity (also transformer-based)
    t5_paper = next((p for p in filtered if 'T5' in p['title']), None)
    assert t5_paper is not None
    assert t5_paper['similarity_score'] > 0.5  # Should be fairly similar

    # Papers should be sorted by similarity
    scores = [p['similarity_score'] for p in filtered]
    assert scores == sorted(scores, reverse=True)


def test_filter_papers_empty_reference():
    """Test filtering when no reference papers are loaded"""
    filter_obj = SimilarityFilter(enable_cache=False)

    papers = [
        {
            'title': 'Test Paper',
            'abstract': 'This is a test abstract.'
        }
    ]

    # Should return all papers when no reference papers
    filtered = filter_obj.filter_papers(papers)
    assert len(filtered) == len(papers)


def test_filter_papers_top_k(sample_reference_papers, sample_new_papers):
    """Test top-k filtering"""
    filter_obj = SimilarityFilter(
        min_similarity=0.0,  # Accept all
        top_k=2,  # But only keep top 2
        enable_cache=False
    )

    filter_obj.add_reference_papers(sample_reference_papers, source='test')
    filtered = filter_obj.filter_papers(sample_new_papers)

    # Should only keep top 2
    assert len(filtered) <= 2


def test_filter_papers_minimum_threshold(sample_reference_papers, sample_new_papers):
    """Test minimum similarity threshold"""
    filter_obj = SimilarityFilter(
        min_similarity=0.9,  # Very high threshold
        top_k=100,
        enable_cache=False
    )

    filter_obj.add_reference_papers(sample_reference_papers, source='test')
    filtered = filter_obj.filter_papers(sample_new_papers)

    # All filtered papers should meet threshold
    assert all(p['similarity_score'] >= 0.9 for p in filtered)


def test_get_stats(sample_reference_papers):
    """Test getting filter statistics"""
    filter_obj = SimilarityFilter(
        min_similarity=0.6,
        top_k=10,
        enable_cache=False
    )

    filter_obj.add_reference_papers(sample_reference_papers, source='test')

    stats = filter_obj.get_stats()

    assert stats['num_reference_papers'] == 3
    assert stats['model_name'] == 'all-MiniLM-L6-v2'
    assert stats['min_similarity'] == 0.6
    assert stats['top_k'] == 10
    assert 'embedding_dimension' in stats


def test_most_similar_tracking(sample_reference_papers, sample_new_papers):
    """Test that most similar paper is tracked"""
    filter_obj = SimilarityFilter(
        min_similarity=0.0,
        enable_cache=False
    )

    filter_obj.add_reference_papers(sample_reference_papers, source='test')
    filtered = filter_obj.filter_papers(sample_new_papers)

    # All papers should have most_similar_to field
    assert all('most_similar_to' in p for p in filtered)

    # T5 should be most similar to one of the transformer papers
    t5_paper = next((p for p in filtered if 'T5' in p['title']), None)
    if t5_paper:
        assert t5_paper['most_similar_to'] in [
            'Attention Is All You Need',
            'BERT: Pre-training of Deep Bidirectional Transformers',
            'GPT-3: Language Models are Few-Shot Learners'
        ]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
