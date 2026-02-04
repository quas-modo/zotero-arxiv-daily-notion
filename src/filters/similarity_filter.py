"""Similarity-based paper filter using semantic embeddings"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SimilarityFilter:
    """Filter papers based on semantic similarity to reference papers"""

    def __init__(
        self,
        min_similarity: float = 0.6,
        top_k: int = 20,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Initialize similarity filter.

        Args:
            min_similarity: Minimum similarity score (0-1) to keep a paper
            top_k: Maximum number of papers to keep
            model_name: Sentence transformer model name
            cache_dir: Directory to cache embeddings (default: data/embeddings)
            enable_cache: Whether to cache embeddings to disk
        """
        self.min_similarity = min_similarity
        self.top_k = top_k
        self.model_name = model_name
        self.enable_cache = enable_cache

        # Set cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent.parent / "data" / "embeddings"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"✓ Model loaded (embedding dimension: {self.model.get_sentence_embedding_dimension()})")

        # Storage for reference papers and embeddings
        self.reference_papers = []
        self.reference_embeddings = None

    def add_reference_papers(self, papers: List[Dict], source: str = "unknown"):
        """
        Add reference papers to compare against.

        Args:
            papers: List of paper dicts with 'title', 'abstract', 'text' keys
            source: Source of papers (e.g., 'zotero', 'scholar-inbox')
        """
        if not papers:
            logger.warning(f"No papers provided from source: {source}")
            return

        logger.info(f"Adding {len(papers)} reference papers from {source}")

        # Try to load cached embeddings
        cache_file = self.cache_dir / f"{source}_embeddings.pkl"
        cache_meta_file = self.cache_dir / f"{source}_metadata.json"

        if self.enable_cache and cache_file.exists() and cache_meta_file.exists():
            try:
                # Load cached data
                with open(cache_file, 'rb') as f:
                    cached_embeddings = pickle.load(f)

                with open(cache_meta_file, 'r', encoding='utf-8') as f:
                    cached_metadata = json.load(f)

                # Verify cache is still valid
                if (cached_metadata.get('model_name') == self.model_name and
                    cached_metadata.get('num_papers') == len(papers)):
                    logger.info(f"✓ Loaded cached embeddings for {source}")
                    self.reference_papers.extend(papers)

                    if self.reference_embeddings is None:
                        self.reference_embeddings = cached_embeddings
                    else:
                        self.reference_embeddings = np.vstack([
                            self.reference_embeddings,
                            cached_embeddings
                        ])
                    return
                else:
                    logger.info("Cache invalidated, regenerating embeddings")
            except Exception as e:
                logger.warning(f"Error loading cache: {e}, regenerating embeddings")

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(papers)} papers...")
        texts = [p['text'] for p in papers]
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Store reference papers and embeddings
        self.reference_papers.extend(papers)

        if self.reference_embeddings is None:
            self.reference_embeddings = embeddings
        else:
            self.reference_embeddings = np.vstack([
                self.reference_embeddings,
                embeddings
            ])

        # Cache embeddings
        if self.enable_cache:
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(embeddings, f)

                metadata = {
                    'model_name': self.model_name,
                    'num_papers': len(papers),
                    'source': source,
                    'embedding_dim': self.model.get_sentence_embedding_dimension()
                }

                with open(cache_meta_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

                logger.info(f"✓ Cached embeddings to {cache_file}")
            except Exception as e:
                logger.warning(f"Failed to cache embeddings: {e}")

        logger.info(f"✓ Added {len(papers)} reference papers (total: {len(self.reference_papers)})")

    def filter_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter papers by similarity to reference papers.

        Args:
            papers: List of paper dicts with 'title' and 'abstract' keys

        Returns:
            Filtered list of papers with similarity scores
        """
        if not papers:
            logger.warning("No papers to filter")
            return []

        if self.reference_embeddings is None or len(self.reference_papers) == 0:
            logger.warning("No reference papers loaded. Returning all papers.")
            return papers

        logger.info(f"Filtering {len(papers)} papers by similarity to {len(self.reference_papers)} reference papers")

        # Generate embeddings for new papers
        texts = []
        for paper in papers:
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            text = f"{title}"
            if abstract:
                text += f" {abstract}"
            texts.append(text)

        logger.info("Generating embeddings for new papers...")
        new_embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Calculate similarity scores
        logger.info("Calculating similarity scores...")
        similarity_matrix = cosine_similarity(new_embeddings, self.reference_embeddings)

        # Get max similarity for each paper
        max_similarities = similarity_matrix.max(axis=1)

        # Add similarity scores to papers
        for i, paper in enumerate(papers):
            paper['similarity_score'] = float(max_similarities[i])

            # Find most similar reference paper
            most_similar_idx = similarity_matrix[i].argmax()
            if most_similar_idx < len(self.reference_papers):
                paper['most_similar_to'] = self.reference_papers[most_similar_idx].get('title', 'Unknown')
            else:
                paper['most_similar_to'] = 'Unknown'

        # Filter by minimum similarity
        filtered_papers = [
            p for p in papers
            if p['similarity_score'] >= self.min_similarity
        ]

        logger.info(f"Papers above threshold ({self.min_similarity}): {len(filtered_papers)}/{len(papers)}")

        # Sort by similarity score
        filtered_papers.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Keep top-k
        if len(filtered_papers) > self.top_k:
            filtered_papers = filtered_papers[:self.top_k]
            logger.info(f"Keeping top {self.top_k} papers")

        # Log statistics
        if filtered_papers:
            scores = [p['similarity_score'] for p in filtered_papers]
            logger.info(f"Similarity scores - Min: {min(scores):.3f}, Max: {max(scores):.3f}, Avg: {np.mean(scores):.3f}")

        # Log selected papers with ranking
        logger.info(f"Selected {len(filtered_papers)} papers after similarity filtering")
        for i, paper in enumerate(filtered_papers, 1):
            title = paper.get('title', 'Unknown')[:80]
            similarity = paper.get('similarity_score', 0.0)
            logger.info(f"  #{i} [{similarity:.3f}] {title}...")

        return filtered_papers

    def clear_cache(self):
        """Clear all cached embeddings"""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl")) + list(self.cache_dir.glob("*.json"))
            for file in cache_files:
                file.unlink()
            logger.info(f"✓ Cleared {len(cache_files)} cache files")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict:
        """Get statistics about reference papers and model"""
        return {
            'num_reference_papers': len(self.reference_papers),
            'model_name': self.model_name,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'min_similarity': self.min_similarity,
            'top_k': self.top_k,
            'cache_enabled': self.enable_cache,
            'cache_dir': str(self.cache_dir)
        }
