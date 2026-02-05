"""LLM-based paper analysis using OpenAI API"""

import os
import json
from typing import Dict, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from ..utils.logger import setup_logger
from ..utils.content_extractor import ContentExtractor

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
        detailed_prompt_template: Optional[str] = None,
        config: Optional[Dict] = None,
        include_detailed_analysis: bool = False,
    ):
        """
        Initialize LLM analyzer.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
            base_url: Custom base URL for OpenAI API (defaults to OPENAI_BASE_URL env var or OpenAI default)
            summary_prompt_template: Custom template for summary prompt
            detailed_prompt_template: Custom template for detailed analysis prompt
            config: Configuration dict (for ContentExtractor)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            )

        self.model = model
        self.config = config or {}

        # Get base URL from parameter or environment variable
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        # Initialize OpenAI client with custom base URL if provided
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(
                f"LLM Analyzer initialized with model: {self.model}, base_url: {self.base_url}"
            )
        else:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"LLM Analyzer initialized with model: {self.model}")

        # Initialize content extractor
        self.content_extractor = ContentExtractor(config=self.config)

        # Default prompts
        self.summary_prompt_template = (
            summary_prompt_template or self._default_summary_prompt()
        )
        self.detailed_prompt_template = (
            detailed_prompt_template or self._default_detailed_prompt()
        )

        self.include_detailed_analysis = (
            config.get("include_detailed_analysis", False)
            if config
            else include_detailed_analysis
        )
        # Get use_full_text from html_extraction config section
        html_config = config.get("html_extraction", {}) if config else {}
        self.use_full_text = html_config.get("use_full_text", False)

    def analyze_paper(self, paper: Dict, include_figures: bool = True) -> Dict:
        """
        Generate both summary and detailed analysis for a paper (English + Chinese).
        Extracts content using HTML-first with PDF fallback.

        Args:
            paper: Paper dictionary with title, authors, abstract, etc.
            include_figures: Whether to extract and analyze figures
            include_detailed_analysis: Whether to generate detailed analysis (default: False)

        Returns:
            Dictionary with English and Chinese analysis fields
        """
        logger.info(f"Analyzing paper: {paper.get('title', 'Unknown')[:80]}...")
        logger.info(f"Include detailed analysis: {self.include_detailed_analysis}")

        try:
            # Extract multimodal content (HTML-first, PDF fallback)
            logger.info("Extracting multimodal content...")
            multimodal_content = self.content_extractor.extract_multimodal_content(
                paper
            )

            extraction_method = multimodal_content.get("extraction_method", "pdf")
            html_available = multimodal_content.get("html_available", False)
            introduction = multimodal_content.get("introduction", "")
            methodology = multimodal_content.get("methodology", "")
            conclusion = multimodal_content.get("conclusion", "")
            figures = multimodal_content.get("figures", [])

            logger.info(
                f"Content extraction via {extraction_method.upper()}: "
                f"intro={len(introduction)} chars, method={len(methodology)} chars, "
                f"conclusion={len(conclusion)} chars, figures={len(figures)}"
            )

            if not introduction:
                # Fallback: use abstract as introduction
                logger.warning(
                    "Could not extract Introduction, using abstract as fallback"
                )
                introduction = paper.get("abstract", "")

            # Generate English summary
            summary = self.generate_summary(paper)

            # Generate English detailed analysis with all sections
            if self.include_detailed_analysis:
                if methodology or conclusion:
                    # Use enhanced analysis with sections if available (HTML extraction)
                    detailed = self.generate_detailed_analysis_with_sections(
                        paper, introduction, methodology, conclusion, figures
                    )
                else:
                    # Fall back to figures-only analysis (PDF extraction)
                    detailed = self.generate_detailed_analysis_with_figures(
                        paper, introduction, figures
                    )
            else:
                # Skip detailed analysis if not requested
                detailed = ""

            # Generate Chinese translations
            summary_zh = self.translate_to_chinese(summary, "summary")
            detailed_zh = (
                self.translate_to_chinese(detailed, "detailed analysis")
                if detailed
                else ""
            )
            abstract_zh = self.translate_to_chinese(
                paper.get("abstract", ""), "abstract"
            )
            introduction_zh = (
                self.translate_to_chinese(introduction, "introduction")
                if introduction
                else ""
            )
            methodology_zh = (
                self.translate_to_chinese(methodology, "methodology")
                if methodology
                else ""
            )
            conclusion_zh = (
                self.translate_to_chinese(conclusion, "conclusion")
                if conclusion
                else ""
            )

            # Translate figure captions to Chinese
            for fig in figures:
                caption = fig.get("caption", "")
                if caption:
                    fig["caption_zh"] = self.translate_to_chinese(
                        caption, "figure caption"
                    )
                else:
                    fig["caption_zh"] = ""

            # Get all_sections and section_order from extraction
            all_sections = multimodal_content.get("all_sections", {})
            section_order = multimodal_content.get("section_order", [])

            # Translate all sections if use_full_text mode is enabled
            all_sections_zh = {}
            if self.use_full_text and all_sections:
                logger.info(
                    f"Full text mode enabled, translating {len(all_sections)} sections..."
                )
                for section_name in section_order:
                    if section_name in all_sections and all_sections[section_name]:
                        content = all_sections[section_name]
                        # Translate section content
                        readable_name = section_name.replace("_", " ").title()
                        logger.info(
                            f"Translating section: {readable_name} ({len(content)} chars)"
                        )
                        all_sections_zh[section_name] = self.translate_to_chinese(
                            content, f"section: {readable_name}"
                        )
                logger.info(f"Translated {len(all_sections_zh)} sections to Chinese")

            result = {
                "summary": summary,
                "detailed_analysis": detailed,
                "introduction": introduction,
                "methodology": methodology,
                "conclusion": conclusion,
                "figures": figures,  # Include figures list
                "summary_zh": summary_zh,
                "detailed_analysis_zh": detailed_zh,
                "abstract_zh": abstract_zh,
                "introduction_zh": introduction_zh,
                "methodology_zh": methodology_zh,
                "conclusion_zh": conclusion_zh,
                "all_sections": all_sections,
                "section_order": section_order,
                "all_sections_zh": all_sections_zh,
                "analysis_model": self.model,
                "num_figures_analyzed": len(figures),
                "extraction_method": extraction_method,
                "html_available": html_available,
            }

            logger.info(
                f"✓ Analysis completed successfully (English + Chinese + {len(figures)} figures, method={extraction_method})"
            )
            return result

        except Exception as e:
            logger.error(f"Error analyzing paper: {str(e)}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "detailed_analysis": f"Error generating analysis: {str(e)}",
                "introduction": "",
                "methodology": "",
                "conclusion": "",
                "figures": [],  # Empty figures list on error
                "summary_zh": f"生成摘要时出错: {str(e)}",
                "detailed_analysis_zh": f"生成分析时出错: {str(e)}",
                "abstract_zh": "",
                "introduction_zh": "",
                "methodology_zh": "",
                "conclusion_zh": "",
                "all_sections": {},
                "section_order": [],
                "all_sections_zh": {},
                "analysis_model": self.model,
                "num_figures_analyzed": 0,
                "extraction_method": "error",
                "html_available": False,
            }

    def analyze_paper_with_web_search(
        self, paper: Dict, include_figures: bool = True
    ) -> Dict:
        """
        Generate deep-dive analysis with web search context enrichment.
        Uses OpenAI tool-calling to search for documentation, repos, and related content.

        Args:
            paper: Paper dictionary with title, authors, abstract, etc.
            include_figures: Whether to extract and analyze figures

        Returns:
            Dictionary with analysis fields + web_sources
        """
        logger.info(
            f"[DEEP DIVE] Analyzing paper with web search: {paper.get('title', 'Unknown')[:80]}..."
        )

        try:
            # Extract multimodal content (HTML-first, PDF fallback)
            logger.info("Extracting multimodal content...")
            multimodal_content = self.content_extractor.extract_multimodal_content(
                paper
            )

            extraction_method = multimodal_content.get("extraction_method", "pdf")
            html_available = multimodal_content.get("html_available", False)
            introduction = multimodal_content.get("introduction", "")
            methodology = multimodal_content.get("methodology", "")
            conclusion = multimodal_content.get("conclusion", "")
            figures = multimodal_content.get("figures", [])

            logger.info(
                f"Content extraction via {extraction_method.upper()}: "
                f"intro={len(introduction)} chars, method={len(methodology)} chars, "
                f"conclusion={len(conclusion)} chars, figures={len(figures)}"
            )

            if not introduction:
                logger.warning(
                    "Could not extract Introduction, using abstract as fallback"
                )
                introduction = paper.get("abstract", "")

            # Generate summary (standard, no web search needed)
            summary = self.generate_summary(paper)

            # Generate deep-dive analysis WITH web search
            detailed, web_sources = self.generate_analysis_with_web_context(
                paper, introduction, figures
            )

            # Generate Chinese translations
            summary_zh = self.translate_to_chinese(summary, "summary")
            detailed_zh = self.translate_to_chinese(detailed, "detailed analysis")
            abstract_zh = self.translate_to_chinese(
                paper.get("abstract", ""), "abstract"
            )
            introduction_zh = (
                self.translate_to_chinese(introduction, "introduction")
                if introduction
                else ""
            )
            methodology_zh = (
                self.translate_to_chinese(methodology, "methodology")
                if methodology
                else ""
            )
            conclusion_zh = (
                self.translate_to_chinese(conclusion, "conclusion")
                if conclusion
                else ""
            )

            # Get all_sections and section_order from extraction
            all_sections = multimodal_content.get("all_sections", {})
            section_order = multimodal_content.get("section_order", [])

            # Translate all sections if use_full_text mode is enabled
            all_sections_zh = {}
            if self.use_full_text and all_sections:
                logger.info(
                    f"[DEEP DIVE] Full text mode enabled, translating {len(all_sections)} sections..."
                )
                for section_name in section_order:
                    if section_name in all_sections and all_sections[section_name]:
                        content = all_sections[section_name]
                        readable_name = section_name.replace("_", " ").title()
                        logger.info(
                            f"Translating section: {readable_name} ({len(content)} chars)"
                        )
                        all_sections_zh[section_name] = self.translate_to_chinese(
                            content, f"section: {readable_name}"
                        )
                logger.info(f"Translated {len(all_sections_zh)} sections to Chinese")

            result = {
                "summary": summary,
                "detailed_analysis": detailed,
                "introduction": introduction,
                "methodology": methodology,
                "conclusion": conclusion,
                "figures": figures,  # Include figures list
                "summary_zh": summary_zh,
                "detailed_analysis_zh": detailed_zh,
                "abstract_zh": abstract_zh,
                "introduction_zh": introduction_zh,
                "methodology_zh": methodology_zh,
                "conclusion_zh": conclusion_zh,
                "all_sections": all_sections,
                "section_order": section_order,
                "all_sections_zh": all_sections_zh,
                "analysis_model": self.model,
                "num_figures_analyzed": len(figures),
                "web_sources": web_sources,
                "analysis_mode": "deep_dive_with_web_search",
                "extraction_method": extraction_method,
                "html_available": html_available,
            }

            logger.info(
                f"✓ Deep dive analysis completed with {len(web_sources)} web sources"
            )
            return result

        except Exception as e:
            logger.error(f"Error in deep dive analysis: {str(e)}")
            # Fallback to standard analysis
            logger.info("Falling back to standard analysis without web search")
            return self.analyze_paper(paper, include_figures=include_figures)

    def generate_analysis_with_web_context(
        self, paper: Dict, introduction: str, figures: list
    ) -> tuple[str, List[Dict]]:
        """
        Generate detailed analysis using web search tool for context enrichment.

        Args:
            paper: Paper dictionary
            introduction: Extracted introduction text
            figures: List of figure dicts

        Returns:
            Tuple of (analysis_text, web_sources)
        """
        # Build figure descriptions
        figure_descriptions = []
        if figures:
            for fig in figures[:3]:
                figure_descriptions.append(
                    f"- Figure {fig['figure_num']} (Page {fig['page_num']}): {fig['caption']}"
                )

        figure_context = (
            "\n".join(figure_descriptions)
            if figure_descriptions
            else "No figures extracted."
        )

        # Enhanced prompt with web search instructions
        prompt = f"""You are an expert AI research assistant analyzing an academic paper with access to web search.

Paper Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', [])[:5])}
Categories: {', '.join(paper.get('categories', []))}
ArXiv ID: {paper.get('arxiv_id', 'Unknown')}
PDF: {paper.get('pdf_url', '')}
ArXiv: {paper.get('entry_url', '')}

Abstract:
{paper.get('abstract', 'No abstract available')}

Introduction (Extracted):
{introduction[:2000] if introduction else 'Introduction not available.'}

Figures Identified:
{figure_context}

---

IMPORTANT INSTRUCTIONS FOR WEB SEARCH:

When you encounter specialized terms, frameworks, or methodologies in this paper, use web search to find:
1. **Official documentation** for mentioned frameworks/libraries
2. **GitHub repositories** for open-source implementations
3. **Related blog posts** or technical articles explaining key concepts
4. **Comparison articles** if the paper references competing approaches

Search for terms like:
- Specific robotics frameworks (e.g., "RT-1", "RT-2", "PaLM-E")
- World model implementations
- Novel architectures mentioned
- Dataset names
- Benchmark comparisons

---

Provide a comprehensive analysis with the following sections:

## Core Methodology & Architecture
Explain the main approach. If frameworks/architectures are mentioned, search for their documentation to provide accurate context.

## Technical Innovations
What's novel? Search for related work to compare and contrast.

## Implementation Details
If code is available or frameworks are mentioned, search for GitHub repos and documentation links.

## Evaluation & Benchmarks
What datasets and metrics were used? Search for dataset documentation if needed.

## Strengths & Limitations
Critical evaluation.

## Practical Applications & Real-World Context
Search for blog posts or articles showing real-world applications of similar techniques.

## Related Work & Ecosystem
How does this fit into the broader research landscape? Search for related papers or surveys.

---

Use markdown formatting. Include inline citations to your web search results like [Source: Title](URL).
"""

        try:
            # Call OpenAI with web_search tool enabled
            logger.info("Calling OpenAI with web search tool...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who analyzes academic papers. You have access to web search to find documentation, code repositories, and related articles for better context. Use web search proactively when you encounter specialized terms, frameworks, or concepts that would benefit from additional context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=[{"type": "web_search"}],  # Enable web search tool
                temperature=0.7,
                max_tokens=4000,
            )

            # Extract the analysis text
            analysis = response.choices[0].message.content.strip()

            # Extract web sources from tool calls (if any)
            web_sources = []

            # Check if the response includes tool calls
            if (
                hasattr(response.choices[0].message, "tool_calls")
                and response.choices[0].message.tool_calls
            ):
                for tool_call in response.choices[0].message.tool_calls:
                    if tool_call.type == "web_search":
                        # Parse the tool call results
                        try:
                            search_results = json.loads(tool_call.function.arguments)
                            if "results" in search_results:
                                for result in search_results["results"]:
                                    web_sources.append(
                                        {
                                            "title": result.get("title", "Untitled"),
                                            "url": result.get("url", ""),
                                            "snippet": result.get("snippet", ""),
                                            "source_type": "web_search",
                                        }
                                    )
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse tool call results: {str(e)}"
                            )

            # Also extract inline citations from the text
            # Look for [Source: Title](URL) patterns
            import re

            citation_pattern = r"\[Source: ([^\]]+)\]\(([^\)]+)\)"
            citations = re.findall(citation_pattern, analysis)

            for title, url in citations:
                if not any(s["url"] == url for s in web_sources):
                    web_sources.append(
                        {
                            "title": title,
                            "url": url,
                            "snippet": "",
                            "source_type": "inline_citation",
                        }
                    )

            logger.info(f"Generated analysis with {len(web_sources)} web sources")
            logger.debug(f"Web sources: {json.dumps(web_sources, indent=2)}")

            return analysis, web_sources

        except Exception as e:
            logger.error(f"Error generating analysis with web search: {str(e)}")
            logger.info("Falling back to standard detailed analysis")

            # Fallback to standard analysis
            analysis = self.generate_detailed_analysis_with_figures(
                paper, introduction, figures
            )
            return analysis, []

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
            title=paper.get("title", "Unknown"),
            authors=", ".join(paper.get("authors", [])[:5]),
            abstract=paper.get("abstract", "No abstract available"),
            pdf_url=paper.get("pdf_url", ""),
            arxiv_url=paper.get("entry_url", ""),
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who summarizes academic papers clearly and concisely.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
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
            title=paper.get("title", "Unknown"),
            authors=", ".join(paper.get("authors", [])[:5]),
            abstract=paper.get("abstract", "No abstract available"),
            categories=", ".join(paper.get("categories", [])),
            arxiv_id=paper.get("arxiv_id", "Unknown"),
            pdf_url=paper.get("pdf_url", ""),
            arxiv_url=paper.get("entry_url", ""),
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who provides comprehensive analysis of academic papers. You explain complex concepts clearly and highlight practical implications.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            analysis = response.choices[0].message.content.strip()
            logger.debug(f"Generated detailed analysis ({len(analysis)} chars)")
            return analysis

        except Exception as e:
            logger.error(f"Error generating detailed analysis: {str(e)}")
            raise

    def generate_detailed_analysis_with_figures(
        self, paper: Dict, introduction: str, figures: list
    ) -> str:
        """
        Generate comprehensive detailed analysis with multimodal context (text + figures).

        Args:
            paper: Paper dictionary
            introduction: Extracted introduction text
            figures: List of figure dicts with image_data, caption, page_num

        Returns:
            Detailed analysis text
        """
        # Check if model supports vision (gpt-4o, gpt-4-turbo, gpt-4-vision-preview)
        supports_vision = any(
            model in self.model.lower()
            for model in ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"]
        )

        # Build figure descriptions
        figure_descriptions = []
        if figures:
            for fig in figures[:3]:  # Limit to top 3 figures
                figure_num = fig.get("figure_number", "?")
                caption = fig.get("caption", "No caption")
                page_num = fig.get("page_num", "?")
                figure_descriptions.append(
                    f"- Figure {figure_num} (Page {page_num}): {caption}"
                )

        figure_context = (
            "\n".join(figure_descriptions)
            if figure_descriptions
            else "No figures extracted."
        )

        # Enhanced prompt with multimodal context
        prompt = f"""You are an expert AI research assistant analyzing an academic paper with access to both text and visual content.

Paper Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', [])[:5])}
Categories: {', '.join(paper.get('categories', []))}
ArXiv ID: {paper.get('arxiv_id', 'Unknown')}
PDF: {paper.get('pdf_url', '')}
ArXiv: {paper.get('entry_url', '')}

Abstract:
{paper.get('abstract', 'No abstract available')}

Introduction (Extracted):
{introduction[:2000] if introduction else 'Introduction not available.'}

Figures Identified:
{figure_context}

Provide a comprehensive analysis focusing on:

## Core Methodology
Explain the main approach and technical innovation. If architecture diagrams or methodology figures are present, describe how they contribute to understanding the approach.

## Key Technical Contributions
What are the novel aspects? What problems do they solve?

## Structural Innovations
If figures show system architecture or model structure, explain the key design choices and their implications.

## Evaluation & Results
What metrics/benchmarks were used? What were the key findings?

## Strengths & Limitations
Critical analysis of the approach.

## Practical Applications
Real-world use cases and implications.

## Related Work Context
How this fits into the broader research landscape.

Use markdown formatting. Be specific and technical. Reference the figures when describing methodology or architecture."""

        try:
            # If vision model and figures available with image data, include images
            if supports_vision and figures:
                # Check if any figures have image_data (downloaded)
                figures_with_data = [f for f in figures[:3] if f.get("image_data")]

                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who analyzes academic papers using both text and visual information. You can examine figures, diagrams, and charts to provide deeper insights into methodology and results.",
                    },
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                ]

                # Add images only if we have downloaded data
                if figures_with_data:
                    for fig in figures_with_data:
                        image_format = fig.get("image_format", "png")
                        messages[1]["content"].append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{fig['image_data']}"
                                },
                            }
                        )
                    logger.info(
                        f"Analyzing with {len(figures_with_data)} figures using vision model"
                    )
                else:
                    logger.info(
                        "No image data available, using text-only analysis with figure captions"
                    )

            else:
                # Text-only analysis
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who provides comprehensive analysis of academic papers. You explain complex concepts clearly and highlight practical implications.",
                    },
                    {"role": "user", "content": prompt},
                ]

            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=3000
            )

            analysis = response.choices[0].message.content.strip()
            logger.debug(
                f"Generated multimodal analysis ({len(analysis)} chars, {len(figures)} figures)"
            )
            return analysis

        except Exception as e:
            logger.error(f"Error generating multimodal analysis: {str(e)}")
            # Fallback to regular analysis
            logger.info("Falling back to text-only analysis")
            return self.generate_detailed_analysis(paper)

    def generate_detailed_analysis_with_sections(
        self,
        paper: Dict,
        introduction: str,
        methodology: str,
        conclusion: str,
        figures: list,
    ) -> str:
        """
        Generate comprehensive detailed analysis with structured sections from HTML extraction.
        Enhanced version that uses Introduction, Methodology, and Conclusion separately.

        Args:
            paper: Paper dictionary
            introduction: Extracted introduction text
            methodology: Extracted methodology text
            conclusion: Extracted conclusion text
            figures: List of figure dicts with image_data, caption, etc.

        Returns:
            Detailed analysis text
        """
        # Check if model supports vision
        supports_vision = any(
            model in self.model.lower()
            for model in ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"]
        )

        # Build figure descriptions
        figure_descriptions = []
        if figures:
            for fig in figures[:3]:
                fig_num = fig.get("figure_number", "?")
                caption = fig.get("caption", "No caption")
                figure_descriptions.append(f"- Figure {fig_num}: {caption}")

        figure_context = (
            "\n".join(figure_descriptions)
            if figure_descriptions
            else "No figures extracted."
        )

        # Enhanced prompt that references all three sections
        prompt = f"""You are an expert AI research assistant analyzing an academic paper with structured content extraction.

Paper Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', [])[:5])}
Categories: {', '.join(paper.get('categories', []))}
ArXiv ID: {paper.get('arxiv_id', 'Unknown')}
PDF: {paper.get('pdf_url', '')}
HTML: {paper.get('html_url', '')}
ArXiv: {paper.get('entry_url', '')}

Abstract:
{paper.get('abstract', 'No abstract available')}

Introduction Section:
{introduction[:2000] if introduction else 'Introduction not available.'}

Methodology Section:
{methodology[:2500] if methodology else 'Methodology not available.'}

Conclusion Section:
{conclusion[:1500] if conclusion else 'Conclusion not available.'}

Figures Identified:
{figure_context}

---

Provide a comprehensive analysis focusing on:

## Core Methodology & Architecture
Based on the Methodology section, explain the main technical approach and innovations. Reference specific techniques, algorithms, or architectures mentioned. If figures illustrate the architecture, describe how they contribute to understanding.

## Motivation & Problem Formulation
From the Introduction, what problem does this paper address? Why is it important? What gap exists in current research?

## Technical Contributions & Innovations
What are the novel aspects? What specific problems do they solve? How do they differ from prior work?

## Results & Evaluation
From the Conclusion section, what were the key findings? What metrics/benchmarks were used? How does performance compare to baselines?

## Strengths & Limitations
Critical analysis: What are the strong points of the approach? What are potential weaknesses, assumptions, or limitations mentioned in the paper?

## Practical Applications & Impact
What are the real-world use cases? How might this research impact the field or be applied in practice?

## Related Work Context
How does this fit into the broader research landscape? What connections exist to other recent work?

---

Use markdown formatting. Be specific and technical. Reference the extracted sections to provide accurate analysis. When methodology or results are described, cite the relevant section (Introduction, Methodology, or Conclusion)."""

        try:
            # If vision model and figures available, include images
            if supports_vision and figures:
                # Check if any figures have image_data (downloaded)
                figures_with_data = [f for f in figures[:3] if f.get("image_data")]

                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who analyzes academic papers using structured text extraction and visual information. You can examine figures, diagrams, and charts alongside Introduction, Methodology, and Conclusion sections to provide comprehensive insights.",
                    },
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                ]

                # Add images only if we have downloaded data
                if figures_with_data:
                    for fig in figures_with_data:
                        # Determine format
                        if fig.get("image_format"):
                            img_format = fig["image_format"]
                        else:
                            # Extract from data URI or default to png
                            img_data = fig["image_data"]
                            if img_data.startswith("data:image/"):
                                img_format = img_data.split(";")[0].split("/")[-1]
                            else:
                                img_format = "png"

                        # Handle both base64 strings and data URIs
                        if fig["image_data"].startswith("data:"):
                            image_url = fig["image_data"]
                        else:
                            image_url = (
                                f"data:image/{img_format};base64,{fig['image_data']}"
                            )

                        messages[1]["content"].append(
                            {"type": "image_url", "image_url": {"url": image_url}}
                        )
                    logger.info(
                        f"Analyzing with {len(figures_with_data)} figures using vision model (with structured sections)"
                    )
                else:
                    logger.info(
                        "No image data available, using text-only analysis with figure captions and structured sections"
                    )

            else:
                # Text-only analysis
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert AI research assistant who provides comprehensive analysis of academic papers using structured text extraction. You analyze Introduction, Methodology, and Conclusion sections separately to provide detailed insights.",
                    },
                    {"role": "user", "content": prompt},
                ]

            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=3000
            )

            analysis = response.choices[0].message.content.strip()
            logger.debug(
                f"Generated structured section analysis ({len(analysis)} chars, {len(figures)} figures)"
            )
            return analysis

        except Exception as e:
            logger.error(f"Error generating structured section analysis: {str(e)}")
            # Fallback to figures-only analysis
            logger.info("Falling back to figures-only analysis")
            return self.generate_detailed_analysis_with_figures(
                paper, introduction, figures
            )

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
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in academic and technical content. Translate accurately while maintaining technical terminology.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=3000,
            )

            translation = response.choices[0].message.content.strip()
            logger.debug(
                f"Translated {content_type} to Chinese ({len(translation)} chars)"
            )
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
                paper_with_error["summary"] = f"Analysis failed: {str(e)}"
                paper_with_error["detailed_analysis"] = f"Analysis failed: {str(e)}"
                analyzed_papers.append(paper_with_error)

        logger.info(
            f"Batch analysis completed: {len(analyzed_papers)}/{len(papers)} successful"
        )
        return analyzed_papers

    def _default_summary_prompt(self) -> str:
        """Default prompt template for summary generation"""
        return """You are an AI research assistant. Analyze this academic paper and provide a concise TL;DR summary.

Paper Title: {title}
Authors: {authors}
Abstract: {abstract}
PDF: {pdf_url}
ArXiv: {arxiv_url}

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
PDF: {pdf_url}
ArXiv: {arxiv_url}

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
