"""Paper relevance filtering based on keywords and scoring"""

from typing import List, Dict, Set
import re
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RelevanceFilter:
    """Filters and ranks papers based on relevance to research interests"""

    def __init__(
        self,
        primary_keywords: List[str],
        secondary_keywords: List[str] = None,
        min_score: float = 0.3,
        boost_github: bool = True
    ):
        """
        Initialize relevance filter.

        Args:
            primary_keywords: High-priority keywords (higher weight)
            secondary_keywords: Secondary keywords (lower weight)
            min_score: Minimum relevance score (0-1) to keep papers
            boost_github: Whether to boost papers with GitHub links
        """
        self.primary_keywords = [kw.lower() for kw in primary_keywords]
        self.secondary_keywords = [kw.lower() for kw in (secondary_keywords or [])]
        self.min_score = min_score
        self.boost_github = boost_github

        # Compile regex patterns for efficient matching
        self.primary_patterns = [re.compile(r'\b' + re.escape(kw.lower()) + r'\b')
                                for kw in self.primary_keywords]
        self.secondary_patterns = [re.compile(r'\b' + re.escape(kw.lower()) + r'\b')
                                  for kw in self.secondary_keywords]

    def filter_papers(self, papers: List[Dict], max_papers: int = 10) -> List[Dict]:
        """
        Filter and rank papers by relevance.

        Args:
            papers: List of paper dictionaries
            max_papers: Maximum number of papers to return

        Returns:
            List of top-ranked papers with relevance scores
        """
        logger.info(f"Filtering {len(papers)} papers (min_score: {self.min_score})")

        # Score all papers
        scored_papers = []
        for paper in papers:
            score, details = self._calculate_relevance_score(paper)

            if score >= self.min_score:
                paper_with_score = paper.copy()
                paper_with_score['relevance_score'] = score
                paper_with_score['match_details'] = details
                scored_papers.append(paper_with_score)

        # Sort by relevance score (descending)
        scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Take top N papers
        top_papers = scored_papers[:max_papers]

        logger.info(f"Selected {len(top_papers)} papers after filtering")
        for i, paper in enumerate(top_papers, 1):
            logger.info(f"  #{i} [{paper['relevance_score']:.2f}] {paper['title'][:80]}...")

        return top_papers

    def _calculate_relevance_score(self, paper: Dict) -> tuple[float, Dict]:
        """
        Calculate relevance score for a paper.

        Args:
            paper: Paper dictionary

        Returns:
            Tuple of (score, match_details)
        """
        # Combine searchable text
        searchable_text = ' '.join([
            paper.get('title', ''),
            paper.get('abstract', ''),
            ' '.join(paper.get('categories', [])),
        ]).lower()

        # Count keyword matches
        primary_matches = set()
        secondary_matches = set()

        # Check primary keywords
        for kw, pattern in zip(self.primary_keywords, self.primary_patterns):
            if pattern.search(searchable_text):
                primary_matches.add(kw)

        # Check secondary keywords
        for kw, pattern in zip(self.secondary_keywords, self.secondary_patterns):
            if pattern.search(searchable_text):
                secondary_matches.add(kw)

        # Calculate base score
        # Primary keywords: 0.4 points each (up to 1.0)
        # Secondary keywords: 0.1 points each (up to 0.3)
        primary_score = min(len(primary_matches) * 0.4, 1.0)
        secondary_score = min(len(secondary_matches) * 0.1, 0.3)

        base_score = primary_score + secondary_score

        # Bonus factors
        bonus = 0.0

        # GitHub bonus (papers with code are often more practical)
        if self.boost_github and paper.get('github_links'):
            bonus += 0.15

        # Title match bonus (keywords in title are more relevant)
        title_lower = paper.get('title', '').lower()
        title_primary_matches = sum(1 for kw in self.primary_keywords if kw in title_lower)
        if title_primary_matches > 0:
            bonus += 0.1 * title_primary_matches

        # Recent papers bonus (more recent = slightly more relevant)
        # This is already handled by ArXiv fetch order, so optional

        # Calculate final score (cap at 1.0)
        final_score = min(base_score + bonus, 1.0)

        # Match details for logging/debugging
        details = {
            'primary_matches': list(primary_matches),
            'secondary_matches': list(secondary_matches),
            'has_github': bool(paper.get('github_links')),
            'title_matches': title_primary_matches,
            'base_score': base_score,
            'bonus': bonus,
        }

        return final_score, details

    def get_matched_keywords(self, paper: Dict) -> Set[str]:
        """
        Get all keywords that matched for a paper.

        Args:
            paper: Paper dictionary

        Returns:
            Set of matched keywords
        """
        searchable_text = ' '.join([
            paper.get('title', ''),
            paper.get('abstract', ''),
        ]).lower()

        matches = set()

        for kw, pattern in zip(self.primary_keywords, self.primary_patterns):
            if pattern.search(searchable_text):
                matches.add(kw)

        for kw, pattern in zip(self.secondary_keywords, self.secondary_patterns):
            if pattern.search(searchable_text):
                matches.add(kw)

        return matches

    def explain_score(self, paper: Dict) -> str:
        """
        Generate human-readable explanation of relevance score.

        Args:
            paper: Paper dictionary (must have 'match_details')

        Returns:
            Explanation string
        """
        if 'match_details' not in paper:
            return "No match details available"

        details = paper['match_details']
        score = paper['relevance_score']

        explanation = [
            f"Relevance Score: {score:.2f}",
            f"Primary Keywords: {', '.join(details['primary_matches']) if details['primary_matches'] else 'None'}",
            f"Secondary Keywords: {', '.join(details['secondary_matches']) if details['secondary_matches'] else 'None'}",
        ]

        if details['has_github']:
            explanation.append("✓ Has GitHub repository")

        if details['title_matches'] > 0:
            explanation.append(f"✓ {details['title_matches']} keyword(s) in title")

        return "\n".join(explanation)
