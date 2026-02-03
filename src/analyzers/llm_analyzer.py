"""LLM-based paper analysis using OpenAI API"""

import os
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from ..utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


class LLMAnalyzer:
    """Analyzes academic papers using LLM"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        summary_prompt_template: Optional[str] = None,
        detailed_prompt_template: Optional[str] = None
    ):
        """
        Initialize LLM analyzer.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
            base_url: Custom base URL for OpenAI API (defaults to OPENAI_BASE_URL env var or OpenAI default)
            summary_prompt_template: Custom template for summary prompt
            detailed_prompt_template: Custom template for detailed analysis prompt
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        self.model = model

        # Get base URL from parameter or environment variable
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL')

        # Initialize OpenAI client with custom base URL if provided
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(f"LLM Analyzer initialized with model: {self.model}, base_url: {self.base_url}")
        else:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"LLM Analyzer initialized with model: {self.model}")

        # Default prompts
        self.summary_prompt_template = summary_prompt_template or self._default_summary_prompt()
        self.detailed_prompt_template = detailed_prompt_template or self._default_detailed_prompt()

    def analyze_paper(self, paper: Dict) -> Dict:
        """
        Generate both summary and detailed analysis for a paper (English + Chinese).

        Args:
            paper: Paper dictionary with title, authors, abstract, etc.

        Returns:
            Dictionary with English and Chinese analysis fields
        """
        logger.info(f"Analyzing paper: {paper.get('title', 'Unknown')[:80]}...")

        try:
            # Generate English summary
            summary = self.generate_summary(paper)

            # Generate English detailed analysis
            detailed = self.generate_detailed_analysis(paper)

            # Generate Chinese translations
            summary_zh = self.translate_to_chinese(summary, "summary")
            detailed_zh = self.translate_to_chinese(detailed, "detailed analysis")
            abstract_zh = self.translate_to_chinese(paper.get('abstract', ''), "abstract")

            result = {
                'summary': summary,
                'detailed_analysis': detailed,
                'summary_zh': summary_zh,
                'detailed_analysis_zh': detailed_zh,
                'abstract_zh': abstract_zh,
                'analysis_model': self.model
            }

            logger.info("✓ Analysis completed successfully (English + Chinese)")
            return result

        except Exception as e:
            logger.error(f"Error analyzing paper: {str(e)}")
            return {
                'summary': f"Error generating summary: {str(e)}",
                'detailed_analysis': f"Error generating analysis: {str(e)}",
                'summary_zh': f"生成摘要时出错: {str(e)}",
                'detailed_analysis_zh': f"生成分析时出错: {str(e)}",
                'abstract_zh': '',
                'analysis_model': self.model
            }

    def generate_summary(self, paper: Dict) -> str:
        """
        Generate concise TL;DR summary.

        Args:
            paper: Paper dictionary

        Returns:
            Summary text
        """
        # Format prompt with paper details
        prompt = self.summary_prompt_template.format(
            title=paper.get('title', 'Unknown'),
            authors=', '.join(paper.get('authors', [])[:5]),
            abstract=paper.get('abstract', 'No abstract available')
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI research assistant who summarizes academic papers clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            summary = response.choices[0].message.content.strip()
            logger.debug(f"Generated summary ({len(summary)} chars)")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    def generate_detailed_analysis(self, paper: Dict) -> str:
        """
        Generate comprehensive detailed analysis.

        Args:
            paper: Paper dictionary

        Returns:
            Detailed analysis text
        """
        # Format prompt with paper details
        prompt = self.detailed_prompt_template.format(
            title=paper.get('title', 'Unknown'),
            authors=', '.join(paper.get('authors', [])[:5]),
            abstract=paper.get('abstract', 'No abstract available'),
            categories=', '.join(paper.get('categories', [])),
            arxiv_id=paper.get('arxiv_id', 'Unknown')
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI research assistant who provides comprehensive analysis of academic papers. You explain complex concepts clearly and highlight practical implications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            analysis = response.choices[0].message.content.strip()
            logger.debug(f"Generated detailed analysis ({len(analysis)} chars)")
            return analysis

        except Exception as e:
            logger.error(f"Error generating detailed analysis: {str(e)}")
            raise

    def translate_to_chinese(self, text: str, content_type: str = "text") -> str:
        """
        Translate English text to Chinese.

        Args:
            text: English text to translate
            content_type: Type of content (for context)

        Returns:
            Chinese translation
        """
        if not text or len(text.strip()) == 0:
            return ""

        prompt = f"""Translate the following academic {content_type} from English to Chinese.
Maintain the technical accuracy and professional tone. Keep markdown formatting if present.

English text:
{text}

Provide ONLY the Chinese translation, no explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in academic and technical content. Translate accurately while maintaining technical terminology."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )

            translation = response.choices[0].message.content.strip()
            logger.debug(f"Translated {content_type} to Chinese ({len(translation)} chars)")
            return translation

        except Exception as e:
            logger.error(f"Error translating to Chinese: {str(e)}")
            return f"[Translation error: {str(e)}]"

    def batch_analyze(self, papers: list[Dict], max_concurrent: int = 3) -> list[Dict]:
        """
        Analyze multiple papers (sequentially for now).

        Args:
            papers: List of paper dictionaries
            max_concurrent: Maximum concurrent API calls (not implemented yet)

        Returns:
            List of papers with analysis added
        """
        logger.info(f"Starting batch analysis of {len(papers)} papers")

        analyzed_papers = []

        for i, paper in enumerate(papers, 1):
            logger.info(f"Processing paper {i}/{len(papers)}")

            try:
                analysis = self.analyze_paper(paper)

                # Add analysis to paper
                paper_with_analysis = paper.copy()
                paper_with_analysis.update(analysis)

                analyzed_papers.append(paper_with_analysis)

            except Exception as e:
                logger.error(f"Failed to analyze paper {i}: {str(e)}")
                # Add paper with error message
                paper_with_error = paper.copy()
                paper_with_error['summary'] = f"Analysis failed: {str(e)}"
                paper_with_error['detailed_analysis'] = f"Analysis failed: {str(e)}"
                analyzed_papers.append(paper_with_error)

        logger.info(f"Batch analysis completed: {len(analyzed_papers)}/{len(papers)} successful")
        return analyzed_papers

    def _default_summary_prompt(self) -> str:
        """Default prompt template for summary generation"""
        return """You are an AI research assistant. Analyze this academic paper and provide a concise TL;DR summary.

Paper Title: {title}
Authors: {authors}
Abstract: {abstract}

Provide a clear, concise summary with:
1. **Core Contribution** (1-2 sentences): What is the main innovation or finding?
2. **Key Innovation** (1-2 sentences): What makes this approach novel or different?
3. **Practical Impact** (1-2 sentences): Why does this matter? What are the real-world applications?

Keep the entire summary under 150 words. Write in clear, accessible language suitable for researchers in related fields."""

    def _default_detailed_prompt(self) -> str:
        """Default prompt template for detailed analysis"""
        return """You are an AI research assistant. Provide a comprehensive analysis of this academic paper.

Paper Title: {title}
Authors: {authors}
Categories: {categories}
ArXiv ID: {arxiv_id}
Abstract: {abstract}

Provide a detailed analysis with the following sections:

## Background & Motivation
Why is this problem important? What gap in existing research does this address?

## Methodology
What approach did the authors take? Include key technical details, architecture, or algorithms.

## Key Findings
What are the main results and contributions? Include any significant metrics or benchmarks.

## Strengths & Limitations
Critical evaluation: What are the strong points? What are potential weaknesses or limitations?

## Practical Applications
What are the real-world use cases? How might this be applied in practice?

## Related Work
How does this fit into the broader research landscape? What are the connections to other recent work?

Write in clear, accessible language using markdown formatting. Be specific and technical where appropriate, but explain complex concepts clearly."""
