"""Save analyzed papers to output files"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def save_analyzed_papers(papers: List[Dict], output_dir: str = "data/outputs"):
    """
    Save analyzed papers to JSON and markdown files.

    Args:
        papers: List of analyzed paper dictionaries
        output_dir: Directory to save outputs
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as JSON
    json_file = output_path / f"analyzed_papers_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, default=str)
    print(f"✓ Saved JSON: {json_file}")

    # Save as Markdown report
    md_file = output_path / f"analysis_report_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Paper Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Papers:** {len(papers)}\n\n")
        f.write("---\n\n")

        for i, paper in enumerate(papers, 1):
            f.write(f"## {i}. {paper.get('title', 'Untitled')}\n\n")

            # Metadata
            f.write(f"**Authors:** {', '.join(paper.get('authors', [])[:5])}\n\n")
            f.write(f"**ArXiv ID:** {paper.get('arxiv_id', 'N/A')}\n\n")
            f.write(f"**Published:** {paper.get('published_date', 'N/A')}\n\n")
            f.write(f"**Relevance Score:** {paper.get('combined_score', paper.get('relevance_score', 0)):.2f}\n\n")

            if paper.get('similarity_score'):
                f.write(f"**Similarity Score:** {paper.get('similarity_score', 0):.2f}\n\n")

            # Links
            f.write(f"**Links:**\n")
            if paper.get('pdf_url'):
                f.write(f"- [PDF]({paper['pdf_url']})\n")
            if paper.get('entry_url'):
                f.write(f"- [ArXiv]({paper['entry_url']})\n")
            if paper.get('github_links'):
                for link in paper['github_links']:
                    f.write(f"- [GitHub]({link})\n")
            f.write("\n")

            # Abstract
            if paper.get('abstract'):
                f.write(f"### Abstract\n\n{paper['abstract']}\n\n")

            # Figures Section
            if paper.get('figures') and len(paper['figures']) > 0:
                f.write(f"### Figures\n\n")
                for fig in paper['figures']:
                    figure_num = fig.get('figure_number', fig.get('figure_num', '?'))
                    caption = fig.get('caption', 'No caption available')
                    image_url = fig.get('image_url', '')

                    # Use image URL (preferred - no download needed)
                    if image_url:
                        f.write(f"![Figure {figure_num}]({image_url})\n\n")
                        # Add caption
                        f.write(f"**Figure {figure_num}:** {caption}\n\n")
                    else:
                        # Fallback: use base64 data if URL not available (PDF extraction)
                        image_data = fig.get('image_data', '')
                        if image_data:
                            # For base64, check if it's already a data URI
                            if image_data.startswith('data:'):
                                f.write(f"![Figure {figure_num}]({image_data})\n\n")
                            else:
                                # Assume PNG format if not specified
                                image_format = fig.get('image_format', 'png')
                                f.write(f"![Figure {figure_num}](data:image/{image_format};base64,{image_data})\n\n")
                            # Add caption
                            f.write(f"**Figure {figure_num}:** {caption}\n\n")
                        else:
                            # No image available, just show caption
                            f.write(f"**Figure {figure_num}:** {caption}\n\n")

                f.write("---\n\n")

            # Summary
            if paper.get('summary'):
                f.write(f"### Summary (TL;DR)\n\n{paper['summary']}\n\n")

            # Detailed Analysis
            if paper.get('detailed_analysis'):
                f.write(f"### Detailed Analysis\n\n{paper['detailed_analysis']}\n\n")

            # Chinese translations
            f.write("---\n\n")
            f.write("## 中文翻译 (Chinese Translation)\n\n")

            # Chinese abstract
            if paper.get('abstract_zh'):
                f.write(f"### 摘要 (Abstract)\n\n{paper['abstract_zh']}\n\n")

            # Chinese summary
            if paper.get('summary_zh'):
                f.write(f"### 概要 (Summary)\n\n{paper['summary_zh']}\n\n")

            # Chinese detailed analysis
            if paper.get('detailed_analysis_zh'):
                f.write(f"### 详细分析 (Detailed Analysis)\n\n{paper['detailed_analysis_zh']}\n\n")

            f.write("---\n\n")

    print(f"✓ Saved Markdown: {md_file}")

    return json_file, md_file
