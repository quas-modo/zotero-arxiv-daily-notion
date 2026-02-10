"""Notion API client for paper management"""

import os
import re
from typing import Dict, List, Optional
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv
from ..utils.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)


class NotionClient:
    """Client for interacting with Notion API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize Notion client.

        Args:
            api_key: Notion integration token (defaults to NOTION_API_KEY env var)
            database_id: Notion database ID (defaults to NOTION_DATABASE_ID env var)
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Notion API key not provided. Set NOTION_API_KEY environment variable."
            )

        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        if not self.database_id:
            raise ValueError(
                "Notion database ID not provided. Set NOTION_DATABASE_ID environment variable."
            )

        self.config = config or {}

        self.client = Client(auth=self.api_key)
        logger.info(
            f"Notion client initialized with database: {self.database_id[:8]}..."
        )

    def create_paper_entry(self, paper: Dict) -> Dict:
        """
        Create a new entry in Notion database for a paper.

        Args:
            paper: Paper dictionary with all metadata and analysis

        Returns:
            Created Notion page object
        """
        logger.info(
            f"Creating Notion entry for: {paper.get('title', 'Unknown')[:60]}..."
        )

        # Prepare properties
        properties = self._format_properties(paper)

        # Prepare content blocks
        children = self._format_content_blocks(paper)

        try:
            # Create page
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children,
            )

            logger.info(f"✓ Notion entry created: {response['id']}")
            return response

        except Exception as e:
            error_msg = str(e)
            # If error is about missing property, try to remove it and retry once
            if "is not a property that exists" in error_msg:
                # Extract property name from error message
                match = re.search(r'"([^"]+)" is not a property', error_msg)
                if match:
                    missing_prop = match.group(1)
                    logger.warning(
                        f"Property '{missing_prop}' not found in database, removing and retrying"
                    )
                    properties.pop(missing_prop, None)

                    # Retry without the missing property
                    try:
                        response = self.client.pages.create(
                            parent={"database_id": self.database_id},
                            properties=properties,
                            children=children,
                        )
                        logger.info(
                            f"✓ Notion entry created after removing invalid property: {response['id']}"
                        )
                        return response
                    except Exception as retry_error:
                        logger.error(
                            f"Error creating Notion entry after retry: {str(retry_error)}"
                        )
                        raise

            logger.error(f"Error creating Notion entry: {error_msg}")
            raise

    def _format_properties(self, paper: Dict) -> Dict:
        """Format paper data as Notion properties"""

        properties = {
            # Title (required, title type)
            "Title": {
                "title": [{"text": {"content": paper.get("title", "Untitled")[:2000]}}]
            }
        }

        # Authors (rich text)
        authors_text = ", ".join(paper.get("authors", [])[:10])
        if authors_text:
            properties["Authors"] = {
                "rich_text": [{"text": {"content": authors_text[:2000]}}]
            }

        # Published Date (date)
        if paper.get("published_date"):
            pub_date = paper["published_date"]
            if isinstance(pub_date, datetime):
                properties["Published Date"] = {
                    "date": {"start": pub_date.strftime("%Y-%m-%d")}
                }

        # ArXiv ID (rich text)
        if paper.get("arxiv_id"):
            properties["ArXiv ID"] = {
                "rich_text": [{"text": {"content": paper["arxiv_id"]}}]
            }

        # PDF Link (url)
        if paper.get("pdf_url"):
            properties["PDF Link"] = {"url": paper["pdf_url"]}

        # HTML Link (url) - only if available
        if paper.get("html_url") and paper.get("html_available", False):
            properties["HTML Link"] = {"url": paper["html_url"]}

        # GitHub Link (url)
        if paper.get("github_links") and paper["github_links"]:
            properties["GitHub"] = {"url": paper["github_links"][0]}

        # Categories (multi-select)
        if paper.get("categories"):
            properties["Categories"] = {
                "multi_select": [
                    {"name": cat[:100]} for cat in paper["categories"][:10]
                ]
            }

        # Keywords/Tags (multi-select)
        if paper.get("match_details", {}).get("primary_matches"):
            keywords = paper["match_details"]["primary_matches"]
            if paper["match_details"].get("secondary_matches"):
                keywords += paper["match_details"]["secondary_matches"]

            properties["Keywords"] = {
                "multi_select": [{"name": kw[:100]} for kw in keywords[:10]]
            }

        # Relevance Score (number)
        if "relevance_score" in paper:
            properties["Relevance Score"] = {
                "number": round(paper["relevance_score"], 2)
            }

        return properties

    def _format_content_blocks(self, paper: Dict) -> List[Dict]:
        """Format paper content as Notion blocks with rich formatting"""

        blocks = []

        # Add quick info callout
        quick_info = []
        if paper.get("published_date"):
            pub_date = paper["published_date"]
            if isinstance(pub_date, datetime):
                quick_info.append(f"📅 Published: {pub_date.strftime('%Y-%m-%d')}")
        if paper.get("categories"):
            quick_info.append(f"🏷️ Categories: {', '.join(paper['categories'][:3])}")
        if paper.get("relevance_score"):
            quick_info.append(f"⭐ Relevance Score: {paper['relevance_score']:.2f}")

        if quick_info:
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": " | ".join(quick_info)}}],
                        "icon": {"emoji": "📊"},
                        "color": "gray_background",
                    },
                }
            )

        # Add extraction metadata callout (if available)
        if paper.get("extraction_method"):
            extraction_info = []
            extraction_method = paper.get("extraction_method", "unknown")
            html_available = paper.get("html_available", False)

            if extraction_method == "html" and html_available:
                extraction_info.append(
                    "✅ Extracted from HTML (structured sections available)"
                )
            elif extraction_method == "pdf":
                extraction_info.append("📄 Extracted from PDF")
            else:
                extraction_info.append(f"📑 Extraction method: {extraction_method}")

            if paper.get("num_figures_analyzed", 0) > 0:
                extraction_info.append(
                    f"🖼️ {paper['num_figures_analyzed']} figures analyzed"
                )

            if extraction_info:
                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {"text": {"content": " | ".join(extraction_info)}}
                            ],
                            "icon": {"emoji": "🔍"},
                            "color": "blue_background",
                        },
                    }
                )

        # ========================================
        # CHINESE CONTENT FIRST
        # ========================================
        blocks.append(
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {"text": {"content": "🇨🇳 中文版本 (Chinese Version)"}}
                    ],
                    "color": "red",
                },
            }
        )

        # Add Chinese abstract as callout
        if paper.get("abstract_zh"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📄 摘要 (Abstract)"}}],
                        "color": "default",
                    },
                }
            )
            for chunk in self._split_text(paper["abstract_zh"], 2000):
                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": self._parse_inline_formatting(chunk),
                            "icon": {"emoji": "📋"},
                            "color": "default_background",
                        },
                    }
                )

        # Add Chinese summary as callout
        if paper.get("summary_zh"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "✨ 概要 (Summary)"}}],
                        "color": "orange",
                    },
                }
            )
            for chunk in self._split_text(paper["summary_zh"], 2000):
                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": self._parse_inline_formatting(chunk),
                            "icon": {"emoji": "✨"},
                            "color": "orange_background",
                        },
                    }
                )

        # Add Chinese introduction (from PDF extraction)
        if paper.get("introduction_zh"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📖 引言 (Introduction)"}}],
                        "color": "purple",
                    },
                }
            )

            # Use extracted introduction from PDF
            intro_text = paper["introduction_zh"]
            for chunk in self._split_text(intro_text, 4000):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_inline_formatting(chunk),
                            "color": "default",
                        },
                    }
                )

        # Add Chinese detailed analysis
        if paper.get("detailed_analysis_zh"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})

            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"text": {"content": "🔍 详细分析 (Detailed Analysis)"}}
                        ],
                        "color": "default",
                    },
                }
            )
            blocks.extend(self._parse_markdown_to_blocks(paper["detailed_analysis_zh"]))

        # Add figures section if figures are available
        if paper.get("figures") and len(paper["figures"]) > 0:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "🖼️ Figures"}}],
                        "color": "green",
                    },
                }
            )

            # Add each figure with caption
            for fig in paper["figures"]:
                figure_num = fig.get("figure_number", fig.get("figure_num", "?"))
                caption = fig.get("caption", "No caption available")
                caption_zh = fig.get("caption_zh", "")
                image_url = fig.get("image_url", "")

                # Add figure image block
                if image_url:
                    blocks.append(
                        {
                            "object": "block",
                            "type": "image",
                            "image": {
                                "type": "external",
                                "external": {"url": image_url},
                            },
                        }
                    )

                # Add Chinese caption if available
                if caption_zh:
                    blocks.append(
                        {
                            "object": "block",
                            "type": "quote",
                            "quote": {
                                "rich_text": [
                                    {
                                        "text": {
                                            "content": f"图 {figure_num}: {caption_zh}"
                                        }
                                    }
                                ],
                                "color": "default",
                            },
                        }
                    )

                # Add English caption as quote block
                blocks.append(
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [
                                {"text": {"content": f"Figure {figure_num}: {caption}"}}
                            ],
                            "color": "gray_background",
                        },
                    }
                )

            blocks.append({"object": "block", "type": "divider", "divider": {}})

        # Add all sections in Chinese (full text translation) if available
        all_sections_zh = paper.get("all_sections_zh", {})
        section_order = paper.get("section_order", [])

        if all_sections_zh and section_order:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "📚 全文章节翻译 (Full Text Sections)"
                                }
                            }
                        ],
                        "color": "purple",
                    },
                }
            )

            # Add callout explaining this section
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"以下是论文各章节的中文翻译，共 {len(all_sections_zh)} 个章节。"
                                }
                            }
                        ],
                        "icon": {"emoji": "📖"},
                        "color": "purple_background",
                    },
                }
            )

            # Add each section in order
            for section_name in section_order:
                if section_name in all_sections_zh and all_sections_zh[section_name]:
                    content_zh = all_sections_zh[section_name]
                    # Convert section name to readable Chinese title
                    readable_name = section_name.replace("_", " ").title()

                    # Add section heading as toggle (collapsible)
                    section_blocks = []
                    for chunk in self._split_text(content_zh, 2000):
                        section_blocks.append(
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": self._parse_inline_formatting(chunk),
                                    "color": "default",
                                },
                            }
                        )

                    # Use toggle block to keep it organized
                    blocks.append(
                        {
                            "object": "block",
                            "type": "toggle",
                            "toggle": {
                                "rich_text": [
                                    {"text": {"content": f"📑 {readable_name}"}}
                                ],
                                "color": "default",
                                "children": (
                                    section_blocks
                                    if section_blocks
                                    else [
                                        {
                                            "object": "block",
                                            "type": "paragraph",
                                            "paragraph": {
                                                "rich_text": [
                                                    {"text": {"content": "(内容为空)"}}
                                                ]
                                            },
                                        }
                                    ]
                                ),
                            },
                        }
                    )

            blocks.append({"object": "block", "type": "divider", "divider": {}})

        # ========================================
        # ENGLISH CONTENT SECOND
        # ========================================
        if not self.config.get("has_english"):
            return blocks

        blocks.append({"object": "block", "type": "divider", "divider": {}})

        blocks.append(
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🇬🇧 English Version"}}],
                    "color": "blue",
                },
            }
        )

        # Add English abstract in a toggle block
        if paper.get("abstract"):
            blocks.append(
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"text": {"content": "📄 Abstract"}}],
                        "color": "default",
                        "children": [
                            {
                                "object": "block",
                                "type": "quote",
                                "quote": {
                                    "rich_text": [
                                        {"text": {"content": paper["abstract"][:2000]}}
                                    ],
                                    "color": "default",
                                },
                            }
                        ],
                    },
                }
            )

        # Add English introduction (from PDF extraction)
        if paper.get("introduction"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📖 Introduction"}}],
                        "color": "purple",
                    },
                }
            )

            # Use extracted introduction from PDF
            intro_text = paper["introduction"]
            for chunk in self._split_text(intro_text, 2000):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_inline_formatting(chunk),
                            "color": "default",
                        },
                    }
                )

        # Add English summary as a callout
        if paper.get("summary"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "✨ Summary (TL;DR)"}}],
                        "color": "blue",
                    },
                }
            )

            summary_text = paper["summary"]
            for chunk in self._split_text(summary_text, 2000):
                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": self._parse_inline_formatting(chunk),
                            "icon": {"emoji": "✨"},
                            "color": "blue_background",
                        },
                    }
                )

        # Add English detailed analysis if available
        if paper.get("detailed_analysis"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})

            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "🔍 Detailed Analysis"}}],
                        "color": "default",
                    },
                }
            )

            # Process markdown-style content
            analysis_text = paper["detailed_analysis"]
            blocks.extend(self._parse_markdown_to_blocks(analysis_text))

        # Add links section with proper formatting
        if paper.get("pdf_url") or paper.get("entry_url") or paper.get("github_links"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})

            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "🔗 Links & Resources"}}],
                        "color": "default",
                    },
                }
            )

            # PDF Link
            if paper.get("pdf_url"):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"text": {"content": "📄 PDF: "}},
                                {
                                    "text": {
                                        "content": paper["pdf_url"],
                                        "link": {"url": paper["pdf_url"]},
                                    }
                                },
                            ]
                        },
                    }
                )

            # HTML Link (if available)
            if paper.get("html_url") and paper.get("html_available", False):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"text": {"content": "🌐 HTML: "}},
                                {
                                    "text": {
                                        "content": paper["html_url"],
                                        "link": {"url": paper["html_url"]},
                                    }
                                },
                            ]
                        },
                    }
                )

            # ArXiv Link
            if paper.get("entry_url"):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"text": {"content": "🔗 ArXiv: "}},
                                {
                                    "text": {
                                        "content": paper["entry_url"],
                                        "link": {"url": paper["entry_url"]},
                                    }
                                },
                            ]
                        },
                    }
                )

            # GitHub Links
            if paper.get("github_links"):
                for i, link in enumerate(paper["github_links"][:3], 1):
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"text": {"content": f"💻 GitHub ({i}): "}},
                                    {"text": {"content": link, "link": {"url": link}}},
                                ]
                            },
                        }
                    )

        # Add web search sources section (if available from deep dive mode)
        if paper.get("web_sources") and len(paper["web_sources"]) > 0:
            blocks.append({"object": "block", "type": "divider", "divider": {}})

            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "🌐 Web Search Sources (Deep Dive Mode)"
                                }
                            }
                        ],
                        "color": "purple",
                    },
                }
            )

            # Add callout explaining web sources
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"Found {len(paper['web_sources'])} web sources to provide additional context on frameworks, implementations, and related work mentioned in this paper."
                                }
                            }
                        ],
                        "icon": {"emoji": "🔍"},
                        "color": "purple_background",
                    },
                }
            )

            # Add each web source as a link with description
            for i, source in enumerate(
                paper["web_sources"][:10], 1
            ):  # Limit to 10 sources
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                snippet = source.get("snippet", "")

                # Create rich text with title as link
                rich_text_elements = [
                    {"text": {"content": f"{i}. ", "link": None}},
                ]

                if url:
                    rich_text_elements.append(
                        {
                            "text": {"content": title, "link": {"url": url}},
                            "annotations": {"bold": True},
                        }
                    )
                else:
                    rich_text_elements.append(
                        {"text": {"content": title}, "annotations": {"bold": True}}
                    )

                # Add snippet if available
                if snippet:
                    rich_text_elements.append(
                        {"text": {"content": f"\n   {snippet[:200]}..."}}
                    )

                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": rich_text_elements},
                    }
                )

        return blocks

    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """Split text into chunks that fit Notion's character limit"""
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            # Try to split at paragraph or sentence
            split_pos = text.rfind("\n\n", 0, max_length)
            if split_pos == -1:
                split_pos = text.rfind(". ", 0, max_length)
            if split_pos == -1:
                split_pos = max_length

            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip()

        return chunks

    def _parse_markdown_to_blocks(self, text: str) -> List[Dict]:
        """Parse markdown-style text into rich Notion blocks with proper formatting"""
        blocks = []
        lines = text.split("\n")

        i = 0
        current_paragraph = []
        in_code_block = False
        code_lines = []
        code_language = ""

        def flush_paragraph():
            """Helper to add accumulated paragraph lines as blocks"""
            if current_paragraph:
                para_text = "\n".join(current_paragraph)
                rich_text = self._parse_inline_formatting(para_text)
                for chunk_rich_text in self._split_rich_text(rich_text, 2000):
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": chunk_rich_text},
                        }
                    )
                current_paragraph.clear()

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Code block start/end
            if stripped.startswith("```"):
                flush_paragraph()

                if not in_code_block:
                    # Start code block
                    in_code_block = True
                    code_language = stripped[3:].strip() or "plain text"
                    code_lines = []
                else:
                    # End code block
                    in_code_block = False
                    code_text = "\n".join(code_lines)
                    for chunk in self._split_text(code_text, 2000):
                        blocks.append(
                            {
                                "object": "block",
                                "type": "code",
                                "code": {
                                    "rich_text": [{"text": {"content": chunk}}],
                                    "language": (
                                        code_language
                                        if code_language
                                        in [
                                            "python",
                                            "javascript",
                                            "java",
                                            "typescript",
                                            "cpp",
                                            "c",
                                            "go",
                                            "rust",
                                            "ruby",
                                            "php",
                                            "sql",
                                            "bash",
                                            "shell",
                                        ]
                                        else "plain text"
                                    ),
                                },
                            }
                        )
                    code_lines = []
                i += 1
                continue

            # Inside code block
            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Empty line
            if not stripped:
                flush_paragraph()
                i += 1
                continue

            # Heading 1 (#)
            if stripped.startswith("# ") and not stripped.startswith("## "):
                flush_paragraph()
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": stripped[2:][:2000]}}],
                            "color": "blue",
                        },
                    }
                )
                i += 1
                continue

            # Heading 2 (##)
            if stripped.startswith("## ") and not stripped.startswith("### "):
                flush_paragraph()
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"text": {"content": stripped[3:][:2000]}}],
                            "color": "default",
                        },
                    }
                )
                i += 1
                continue

            # Heading 3 (###)
            if stripped.startswith("### "):
                flush_paragraph()
                # Use toggle block for subsections
                content = stripped[4:][:2000]
                blocks.append(
                    {
                        "object": "block",
                        "type": "toggle",
                        "toggle": {
                            "rich_text": [{"text": {"content": content}}],
                            "color": "gray_background",
                        },
                    }
                )
                i += 1
                continue

            # Callout/Quote (>)
            if stripped.startswith("> "):
                flush_paragraph()
                quote_lines = [stripped[2:]]
                i += 1
                while i < len(lines) and lines[i].strip().startswith("> "):
                    quote_lines.append(lines[i].strip()[2:])
                    i += 1
                quote_text = " ".join(quote_lines)
                blocks.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{"text": {"content": quote_text[:2000]}}],
                            "icon": {"emoji": "💡"},
                            "color": "blue_background",
                        },
                    }
                )
                continue

            # Numbered list (1. 2. etc)
            if stripped and stripped[0].isdigit() and ". " in stripped[:4]:
                flush_paragraph()
                dot_pos = stripped.find(". ")
                content = stripped[dot_pos + 2 :]
                rich_text = self._parse_inline_formatting(content)
                blocks.append(
                    {
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": (
                                rich_text
                                if len(str(rich_text)) <= 2000
                                else [{"text": {"content": content[:2000]}}]
                            )
                        },
                    }
                )
                i += 1
                continue

            # Bullet point (- or *)
            if stripped.startswith("- ") or stripped.startswith("* "):
                flush_paragraph()
                content = stripped[2:]
                rich_text = self._parse_inline_formatting(content)
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": (
                                rich_text
                                if len(str(rich_text)) <= 2000
                                else [{"text": {"content": content[:2000]}}]
                            )
                        },
                    }
                )
                i += 1
                continue

            # Divider (---)
            if stripped in ["---", "***", "___"]:
                flush_paragraph()
                blocks.append({"object": "block", "type": "divider", "divider": {}})
                i += 1
                continue

            # Regular paragraph
            current_paragraph.append(line)
            i += 1

        # Flush any remaining paragraph
        flush_paragraph()

        return blocks

    def _parse_inline_formatting(self, text: str) -> List[Dict]:
        """Parse inline markdown formatting (bold, italic, code) into Notion rich text"""
        import re

        # For simplicity, handle basic formatting
        # This is a simplified version - a full parser would be more complex
        rich_text = []

        # Split by inline code first (backticks)
        code_pattern = r"`([^`]+)`"
        parts = re.split(code_pattern, text)

        for idx, part in enumerate(parts):
            if not part:
                continue

            # Odd indices are code (inside backticks)
            if idx % 2 == 1:
                rich_text.append(
                    {"text": {"content": part[:2000]}, "annotations": {"code": True}}
                )
                continue

            # Parse bold and italic
            # **bold** or __bold__
            bold_pattern = r"\*\*(.+?)\*\*|__(.+?)__"
            # *italic* or _italic_
            italic_pattern = r"\*(.+?)\*|_(.+?)_"

            # For simplicity, just handle bold
            segments = re.split(bold_pattern, part)
            for seg_idx, segment in enumerate(segments):
                if not segment:
                    continue

                # Check if this is a captured group (bold text)
                if seg_idx % 3 in [1, 2] and segment:
                    rich_text.append(
                        {
                            "text": {"content": segment[:2000]},
                            "annotations": {"bold": True},
                        }
                    )
                elif seg_idx % 3 == 0:
                    # Handle italic in remaining text
                    italic_segments = re.split(italic_pattern, segment)
                    for it_idx, it_seg in enumerate(italic_segments):
                        if not it_seg:
                            continue
                        if it_idx % 3 in [1, 2] and it_seg:
                            rich_text.append(
                                {
                                    "text": {"content": it_seg[:2000]},
                                    "annotations": {"italic": True},
                                }
                            )
                        elif it_idx % 3 == 0:
                            rich_text.append({"text": {"content": it_seg[:2000]}})

        # Fallback if parsing failed
        if not rich_text:
            rich_text = [{"text": {"content": text[:2000]}}]

        return rich_text

    def _split_rich_text(
        self, rich_text: List[Dict], max_length: int = 2000
    ) -> List[List[Dict]]:
        """Split rich text array into chunks that fit Notion's limit"""
        # Simplified: just return as single chunk if not too long
        total_length = sum(
            len(rt.get("text", {}).get("content", "")) for rt in rich_text
        )
        if total_length <= max_length:
            return [rich_text]

        # If too long, fall back to simple splitting
        chunks = []
        current_chunk = []
        current_length = 0

        for rt in rich_text:
            content = rt.get("text", {}).get("content", "")
            if current_length + len(content) > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [rt]
                current_length = len(content)
            else:
                current_chunk.append(rt)
                current_length += len(content)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [[{"text": {"content": ""}}]]

    def batch_create_entries(self, papers: List[Dict]) -> List[Dict]:
        """
        Create multiple Notion entries.

        Args:
            papers: List of paper dictionaries

        Returns:
            List of created Notion pages
        """
        logger.info(f"Creating {len(papers)} Notion entries...")

        results = []
        for i, paper in enumerate(papers, 1):
            try:
                logger.info(f"Processing paper {i}/{len(papers)}")
                result = self.create_paper_entry(paper)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create entry for paper {i}: {str(e)}")
                continue

        logger.info(f"Successfully created {len(results)}/{len(papers)} Notion entries")
        return results

    def check_database_exists(self) -> bool:
        """Check if the configured database exists and is accessible"""
        try:
            self.client.databases.retrieve(database_id=self.database_id)
            logger.info("✓ Database is accessible")
            return True
        except Exception as e:
            logger.error(f"Cannot access database: {str(e)}")
            return False

    def get_database_properties(self) -> Dict:
        """Get the properties schema of the database"""
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            return db.get("properties", {})
        except Exception as e:
            logger.error(f"Error retrieving database properties: {str(e)}")
            return {}
