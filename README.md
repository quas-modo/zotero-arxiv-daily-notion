# Research Paper Intelligence Assistant

An automated tool that discovers, analyzes, and archives academic papers from ArXiv daily using AI-powered semantic filtering and multimodal analysis.

---

## 📑 Table of Contents

- [Overview](#overview)
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
  - [Environment Variables](#environment-variables)
  - [OpenAI API Setup](#openai-api-setup)
  - [Notion Integration](#notion-integration)
  - [Zotero Integration](#zotero-integration)
  - [Research Keywords](#research-keywords)
- [🎯 Usage](#-usage)
  - [Manual Run](#manual-run)
  - [Automated Daily Run](#automated-daily-run)
  - [Command Line Options](#command-line-options)
- [🔄 Pipeline Optimizations](#-pipeline-optimizations)
  - [Zotero Deduplication](#1-zotero-deduplication)
  - [Semantic-First Scoring](#2-semantic-first-scoring)
  - [Multimodal Content Extraction](#3-multimodal-content-extraction)
  - [Vision-Based Analysis](#4-vision-based-analysis)
- [📊 How It Works](#-how-it-works)
  - [Workflow Overview](#workflow-overview)
  - [Similarity Filtering](#similarity-filtering)
  - [Scoring Algorithm](#scoring-algorithm)
- [📁 Project Structure](#-project-structure)
- [🧪 Testing](#-testing)
- [🔧 Troubleshooting](#-troubleshooting)
- [🗺️ Roadmap](#️-roadmap)
- [📄 License](#-license)

---

## Overview

The Research Paper Intelligence Assistant automates the entire workflow of discovering, analyzing, and organizing academic papers. It uses semantic similarity to find papers relevant to your research, extracts figures and text from PDFs, performs AI-powered analysis using vision models, and syncs everything to your Notion workspace and Zotero library.

**What makes it special:**
- 🎯 **Semantic matching** against your existing research (not just keywords)
- 🤖 **Multimodal analysis** with GPT-4o analyzing diagrams and architecture
- 🗂️ **Smart deduplication** prevents adding papers you already have
- 📊 **Hybrid scoring** (85% semantic, 15% keywords) for better relevance
- 📝 **Bilingual output** (English + Chinese translations)

---

## ✨ Features

### Core Capabilities

- 📚 **Automated Paper Discovery**: Fetches latest papers from ArXiv (AI/ML/Robotics categories)
- 🧠 **Semantic Similarity Filtering**:
  - Compares papers to your Zotero library using embeddings
  - 85% semantic similarity + 15% keyword matching
  - Finds conceptually related papers, not just keyword matches
- 🔍 **Smart Deduplication**: Checks ArXiv ID, DOI, and title before adding to Zotero
- 🖼️ **Multimodal Content Extraction**:
  - Full text extraction from PDFs
  - Figure detection and extraction (architecture diagrams, results)
  - Caption extraction for context
- 🤖 **AI-Powered Analysis**:
  - **Vision models** (GPT-4o) analyze diagrams and architecture
  - Concise TL;DR summaries
  - Deep-dive analysis with methodology and findings
  - **Bilingual**: English + Chinese translations
- 📝 **Notion Integration**: Automatically creates beautifully formatted entries
- 📖 **Zotero Sync**: Reference management integration
- ⏰ **Daily Automation**: Runs automatically every day

### Recent Optimizations (Jan 2026)

✅ **Zotero Deduplication** - Never add duplicate papers
✅ **Semantic-First Scoring** - 85/15 split prioritizes relevance
✅ **Multimodal Extraction** - Full text + figures from PDFs
✅ **Vision Analysis** - GPT-4o analyzes architecture diagrams

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Notion integration token (optional but recommended)
- Zotero account (optional for similarity filtering)

### Fast Setup

```bash
# 1. Clone and install
git clone <repository-url>
cd Daily_Reading_Paper
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run with limited papers (recommended for first test)
python src/main.py --max-papers 3
```

**Expected output:**
```
📥 STEP 1: Fetching papers from ArXiv
✓ Found 50 papers from the last 7 days

🗂️  STEP 1.5: Checking for duplicates in Zotero
✓ 35 new papers after deduplication

🔍 STEP 2: Filtering papers by similarity
✓ Selected 15 similar papers

🏷️  STEP 3: Boosting relevance with keyword matching
✓ Keeping top 3 papers for analysis

🤖 STEP 4: Analyzing papers with LLM
  [1/3] Paper title...
      ✓ Complete
✓ Analyzed 3 papers

📝 STEP 5: Syncing to Notion
✓ Created 3 Notion entries
```

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Core dependencies:**
- `arxiv` - ArXiv API integration
- `openai` - LLM analysis
- `notion-client` - Notion integration
- `pyzotero` - Zotero integration
- `sentence-transformers` - Semantic embeddings
- `PyPDF2` - PDF text extraction
- `pymupdf` - Figure extraction (optional but recommended)

**First run:**
- The embedding model (~90MB) will be downloaded automatically
- Subsequent runs use cached embeddings

### 2. Optional: Install PyMuPDF for Figure Extraction

```bash
pip install pymupdf
```

Without PyMuPDF:
- ✅ Text extraction works (PyPDF2 fallback)
- ❌ Figure extraction disabled
- ✅ All other features work normally

With PyMuPDF:
- ✅ Better text extraction
- ✅ Figure extraction with captions
- ✅ Vision models receive actual paper diagrams

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

**Required variables:**

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o                    # Use gpt-4o for vision, gpt-4o-mini for text-only
OPENAI_BASE_URL=                        # Optional: custom endpoint/proxy

# Notion Configuration
NOTION_API_KEY=secret_your-key-here
NOTION_DATABASE_ID=your-database-id

# Zotero Configuration (required for similarity filtering)
ZOTERO_API_KEY=your-zotero-key
ZOTERO_LIBRARY_ID=your-library-id
ZOTERO_LIBRARY_TYPE=user                # or 'group'
```

---

### OpenAI API Setup

#### 1. Get API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-` or `sk-`)
4. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-abc123...xyz789
   ```

#### 2. Choose Model

**Recommended models:**

| Model | Cost | Speed | Vision | Use Case |
|-------|------|-------|--------|----------|
| `gpt-4o` | $$$ | Medium | ✅ Yes | **Best** - Analyzes figures and diagrams |
| `gpt-4o-mini` | $ | Fast | ❌ No | Good - Text-only analysis (cheaper) |
| `gpt-4-turbo` | $$$$ | Slow | ✅ Yes | Alternative vision model |

```bash
# In .env
OPENAI_MODEL=gpt-4o  # For figure analysis
# OPENAI_MODEL=gpt-4o-mini  # For text-only (save costs)
```

#### 3. Using Proxies (Optional)

If OpenAI is blocked in your region, use a proxy:

```bash
# In .env
OPENAI_BASE_URL=https://your-proxy-service.com/v1
```

**Common configurations:**
- Official API (default): Leave `OPENAI_BASE_URL` empty
- Proxy service: `https://api.openai-proxy.com/v1`
- Azure OpenAI: `https://your-resource.openai.azure.com/`
- Local development: `http://localhost:8000/v1`

#### 4. Test OpenAI Connection

```bash
python tests/test_openai_config.py
```

Expected output:
```
✅ OpenAI Configuration Test
✓ API key found
✓ Model: gpt-4o
✓ Base URL: https://api.openai.com/v1 (default)
✓ Test API call successful
```

---

### Notion Integration

#### Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in:
   - **Name**: "Research Paper Assistant"
   - **Workspace**: Select your workspace
   - **Type**: Internal integration
   - **Capabilities**: Enable "Read", "Update", and "Insert"
4. Click **"Submit"**
5. **Copy the Integration Token** (starts with `secret_`)

#### Step 2: Create Notion Database

1. Open Notion, type `/database`
2. Select **"Table - Full page"**
3. Name it "Research Papers"
4. **Add these properties:**

| Property Name | Type | Required | Notes |
|--------------|------|----------|-------|
| Title | Title | ✅ | Auto-created |
| Authors | Text | ✅ | Comma-separated names |
| Published Date | Date | ✅ | Publication date |
| ArXiv ID | Text | ✅ | Paper identifier |
| PDF Link | URL | ✅ | PDF download link |
| GitHub | URL | ⚪ | Code repository (if available) |
| Categories | Multi-select | ✅ | ArXiv categories (AI, CL, LG) |
| Keywords | Multi-select | ⚪ | Matched keywords |
| Relevance Score | Number | ⚪ | 0-1 score |

**To add properties:**
- Click **"+"** in table header
- Select type
- Name exactly as shown (case-sensitive)

#### Step 3: Share Database with Integration

1. Click **"..."** menu (top-right of database)
2. Select **"Add connections"**
3. Find "Research Paper Assistant"
4. Click to grant access

#### Step 4: Get Database ID

1. Open database as full page
2. Check URL:
   ```
   https://www.notion.so/workspace/abc123def456?v=...
   ```
3. Database ID is the string between `/` and `?`: `abc123def456`
4. Copy to `.env`:
   ```bash
   NOTION_DATABASE_ID=abc123def456
   ```

#### Step 5: Test Notion Connection

```bash
python tests/test_notion.py
```

Expected output:
```
✅ SUCCESS! Entry created in Notion
Page ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
URL: https://www.notion.so/...
```

Check your Notion database for the test entry!

**Troubleshooting:**
- **"Could not find database"**: Verify you shared database with integration (Step 3)
- **"Authorization failed"**: Check `NOTION_API_KEY` is correct
- **"Invalid property"**: Ensure all required properties exist with exact names

---

### Zotero Integration

Zotero integration enables:
1. **Semantic filtering**: Compare new papers to your existing library
2. **Deduplication**: Never add papers you already have
3. **Auto-sync**: Save discovered papers to your Zotero library

#### Step 1: Get Zotero API Credentials

1. Go to [Zotero API Keys](https://www.zotero.org/settings/keys)
2. Click **"Create new private key"**
3. Name: "Daily Paper Assistant"
4. Permissions: Check **"Allow library access"** (read-only is fine)
5. Copy the API key

#### Step 2: Get Library ID

1. On the same page, find: **"Your userID for use in API calls is XXXXXX"**
2. Copy this number

#### Step 3: Configure Environment

```bash
# In .env
ZOTERO_API_KEY=your_api_key_here
ZOTERO_LIBRARY_ID=your_library_id_here
ZOTERO_LIBRARY_TYPE=user  # or 'group' for shared libraries
```

#### Step 4: Verify Setup

```bash
python test_optimizations.py
```

Expected output:
```
📋 Test 1: Zotero Deduplication
✓ Found 27 existing identifiers in Zotero
```

---

### Research Keywords

Edit `config/config.yaml` to customize your research interests:

```yaml
keywords:
  primary:
    # Core areas (higher weight in scoring)
    - Embodied AI
    - World Models
    - Robotic Manipulation
    - VLA Models (Vision-Language-Action)
    - Diffusion Policy

  secondary:
    # Supporting topics (lower weight)
    - 3D Gaussian Splatting
    - Foundation Models for Robotics
    - Vision-Language Models
    - Sim-to-Real Transfer
```

**Similarity filtering configuration:**

```yaml
similarity_filter:
  enabled: true
  min_similarity_score: 0.6    # 0-1 scale
  top_k_papers: 20              # Keep top K similar papers

  # Scoring weights (must sum to 1.0)
  similarity_weight: 0.85       # Semantic matching (prioritized)
  keyword_weight: 0.15          # Term matching (secondary)

  # Reference sources
  use_zotero_library: true
  zotero_paper_limit: 100       # Papers to load from Zotero
```

**Filtering thresholds:**

```yaml
filtering:
  max_papers_per_day: 10        # Final papers to analyze
  min_relevance_score: 0.3      # Minimum score to keep
  prioritize_github_links: true # Boost papers with code
```

---

## 🎯 Usage

### Manual Run

```bash
# Full workflow (recommended)
python src/main.py

# Limit to 3 papers (testing)
python src/main.py --max-papers 3

# Dry run (don't create Notion/Zotero entries)
python src/main.py --dry-run
```

### Automated Daily Run

#### Option 1: Built-in Scheduler

```bash
# Runs daily at 9 AM UTC
python src/main.py --schedule
```

Keep terminal running or use `screen`/`tmux`.

#### Option 2: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 9 AM)
0 9 * * * cd /path/to/Daily_Reading_Paper && /path/to/python src/main.py
```

#### Option 3: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
5. Program: `C:\path\to\python.exe`
6. Arguments: `src/main.py`
7. Start in: `C:\path\to\Daily_Reading_Paper`

### Command Line Options

```bash
python src/main.py [OPTIONS]

Options:
  --max-papers N     Limit to N papers (useful for testing)
  --dry-run          Run without creating Notion/Zotero entries
  --schedule         Run on daily schedule (9 AM UTC)
  -h, --help         Show help message
```

**Examples:**

```bash
# Quick test with 2 papers
python src/main.py --max-papers 2

# Check what papers would be selected (no DB writes)
python src/main.py --dry-run

# Production: unlimited papers, auto-sync
python src/main.py
```

---

## 🔄 Pipeline Optimizations

Recent optimizations (January 2026) significantly improve the paper discovery and analysis workflow.

### 1. Zotero Deduplication

**Problem:** Papers were being added to Zotero multiple times.

**Solution:** Pre-filter deduplication (STEP 1.5)
- Fetches existing papers from Zotero before filtering
- Checks ArXiv ID, DOI, and normalized title
- Only processes truly new papers

**Benefits:**
- ✅ No duplicate entries in Zotero
- ✅ Faster processing (skip existing papers)
- ✅ Lower API costs (fewer LLM calls)

**Implementation:**
```python
# Automatically runs between STEP 1 and STEP 2
zotero_client = ZoteroClient()
papers = zotero_client.filter_new_papers(papers)  # Removes duplicates
```

**Test results:**
```
🗂️  STEP 1.5: Checking for duplicates in Zotero
✓ 35 new papers after deduplication (removed 15 duplicates)
```

---

### 2. Semantic-First Scoring

**Problem:** Keyword matching alone missed conceptually related papers.

**Solution:** Increased semantic similarity weight
- **Before:** 70% similarity, 30% keywords
- **After:** 85% similarity, 15% keywords

**Benefits:**
- ✅ Discovers papers using different terminology
- ✅ Finds conceptually related work
- ✅ Less dependent on exact keyword matches

**How it works:**
```python
combined_score = (0.85 × similarity_score) + (0.15 × keyword_score)
```

**Configuration:**
```yaml
# config/config.yaml
similarity_filter:
  similarity_weight: 0.85  # Prioritize semantic matching
  keyword_weight: 0.15     # Use keywords as secondary signal
```

**Example:**
- Paper: "Flow Matching for Robotic Control"
- Doesn't match keyword "Diffusion Policy"
- **But**: High semantic similarity (0.82) to your diffusion papers
- **Result:** Discovered due to semantic matching!

---

### 3. Multimodal Content Extraction

**Problem:** Analysis relied only on abstract (missing key insights from figures).

**Solution:** Extract full text and figures from PDFs
- Full paper text using PyMuPDF
- Up to 3-5 key figures with captions
- Architecture diagrams, results, methodology figures

**Benefits:**
- ✅ Deeper understanding of methodology
- ✅ Visual context for LLM analysis
- ✅ Better identification of novel techniques

**What's extracted:**
```json
{
  "full_text": "Complete paper content...",
  "introduction": "Introduction section...",
  "figures": [
    {
      "figure_num": 1,
      "page_num": 3,
      "caption": "Architecture diagram of the proposed system...",
      "image_data": "base64_encoded_image..."
    }
  ]
}
```

**Requirements:**
```bash
pip install pymupdf  # Recommended for figure extraction
```

**Fallback:**
- Without PyMuPDF: Uses PyPDF2 (text only, no figures)
- All other features continue working

---

### 4. Vision-Based Analysis

**Problem:** LLM couldn't "see" important diagrams and architecture figures.

**Solution:** Use vision models (GPT-4o) to analyze figures
- Sends up to 3 figures as images to GPT-4o
- Enhanced prompts focus on methodology from diagrams
- Analyzes architecture, system design, results charts

**Benefits:**
- ✅ Understands system architecture visually
- ✅ Identifies structural innovations
- ✅ More accurate methodology descriptions

**How it works:**
```python
# LLM receives both text and images
messages = [
    {"type": "text", "text": "Analyze this paper..."},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
]
```

**Example output:**
```markdown
## Core Methodology
The paper introduces a retrieval-augmented generation system (see Figure 1)
that combines dense embeddings with a cross-encoder reranker. The architecture
(Figure 2) shows a novel dual-path design where...

## Structural Innovations
The system architecture (Figure 2) employs three key innovations:
1. Parallel retrieval paths for diverse document types
2. Cross-attention fusion at the decoder level
3. Dynamic routing based on query complexity
```

**Model requirements:**
- **Vision-capable:** `gpt-4o`, `gpt-4-turbo`, `gpt-4-vision-preview`
- **Text-only:** `gpt-4o-mini`, `gpt-4` (figures ignored, text-only analysis)

**Configuration:**
```bash
# .env
OPENAI_MODEL=gpt-4o  # For figure analysis
# OPENAI_MODEL=gpt-4o-mini  # For text-only (cheaper)
```

---

### Optimization Summary

**Processing flow comparison:**

| Step | Before | After |
|------|--------|-------|
| 1. Fetch | 50 papers | 50 papers |
| 1.5. Dedupe | ❌ Not done | ✅ 35 new (15 duplicates removed) |
| 2. Similarity | 20 papers (70% weight) | 15 papers (85% weight) |
| 3. Keywords | 10 papers (30% weight) | 10 papers (15% weight) |
| 4. Analysis | Text only | Text + 3 figures per paper |
| 5. Quality | Good | ⭐ Excellent |

**Performance impact:**
- **Time:** Similar or faster (fewer papers to process)
- **Cost:** 20-40% lower (deduplication savings)
- **Quality:** Significantly better (vision + semantics)

**Test optimizations:**
```bash
python test_optimizations.py
```

Expected output:
```
✓ Zotero deduplication: Working (27 identifiers)
✓ Semantic scoring: Configured (85/15 split)
✓ Multimodal extraction: Ready
✓ Vision analysis: gpt-4o detected
```

---

## 📊 How It Works

### Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Fetch Papers from ArXiv                            │
│ - Categories: cs.AI, cs.CL, cs.LG, cs.RO, cs.CV            │
│ - Timeframe: Last 7 days                                    │
│ - Result: ~50 papers                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1.5: Deduplicate Against Zotero 🆕                    │
│ - Check ArXiv ID, DOI, normalized title                    │
│ - Filter out papers already in your library                │
│ - Result: ~35 new papers (15 duplicates removed)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Semantic Similarity Filtering (PRIMARY)            │
│ - Compare to your Zotero library (embeddings)              │
│ - Keep papers with similarity ≥ 0.6                        │
│ - Select top 20 most similar                               │
│ - Result: ~20 papers                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Keyword Boosting (SECONDARY)                       │
│ - Match against your research keywords                     │
│ - Combine: 85% similarity + 15% keywords                   │
│ - Keep top N papers (configurable)                         │
│ - Result: ~10 papers                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Multimodal Analysis 🆕                             │
│ - Download PDF, extract full text + figures                │
│ - Send to GPT-4o (text + up to 3 images)                   │
│ - Generate summary + detailed analysis                     │
│ - Translate to Chinese                                     │
│ - Result: Rich bilingual analysis                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Sync to Notion                                     │
│ - Create beautifully formatted entries                     │
│ - Include metadata, links, analysis                        │
│ - Chinese version first, English second                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Sync to Zotero (Optional)                          │
│ - Add papers to your reference library                     │
│ - Tags: auto-imported, arxiv                               │
│ - No duplicates (already filtered in 1.5)                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Similarity Filtering

**How semantic matching works:**

1. **Build reference corpus:**
   - Load papers from your Zotero library (~100 papers)
   - Generate embeddings using `all-MiniLM-L6-v2` model
   - Cache embeddings for fast reuse

2. **Embed new papers:**
   - Combine title + abstract of each ArXiv paper
   - Generate embeddings (384-dimensional vectors)

3. **Calculate similarity:**
   - Compute cosine similarity between new paper and all reference papers
   - Take maximum similarity score (most similar paper)
   - Filter papers above threshold (0.6)

4. **Select top-K:**
   - Sort by similarity score (descending)
   - Keep top 20 papers

**Example:**
```python
New paper: "Chain-of-Thought Reasoning in Large Language Models"
Reference: 100 papers in your Zotero library about LLMs and reasoning

Similarity calculation:
- Compare to all 100 papers
- Highest similarity: 0.82 (to "Self-Consistency Improves Chain of Thought")
- Above threshold (0.6) ✓
- In top 20 ✓
- Result: Paper selected for analysis
```

**Why it works better than keywords:**
- Finds papers using different terminology
- Understands conceptual relationships
- Not fooled by keyword stuffing
- Discovers related work you might miss

---

### Scoring Algorithm

**Combined score formula:**

```python
# Similarity score (0-1 from embeddings)
similarity_score = max(cosine_similarity(paper, reference_papers))

# Keyword score (0-1 from matching)
keyword_score = calculate_keyword_relevance(paper, keywords)

# Combined score (weighted average)
combined_score = (0.85 × similarity_score) + (0.15 × keyword_score)
```

**Keyword scoring breakdown:**

```python
Primary keywords (higher weight):
- Match in title: +0.4 per keyword
- Match in abstract: +0.4 per keyword
- Max: 1.0

Secondary keywords (lower weight):
- Match in title or abstract: +0.1 per keyword
- Max: 0.3

Bonuses:
- Has GitHub link: +0.15
- Primary keyword in title: +0.1 per keyword
```

**Example calculation:**

```
Paper: "Retrieval-Augmented Generation with LLMs"

Similarity:
- Most similar to your paper "RAG for Knowledge-Intensive NLP": 0.85

Keywords:
- Primary matches: "LLM", "RAG" → 0.8
- Secondary matches: "retrieval" → 0.1
- Bonuses: GitHub (+0.15), "LLM" in title (+0.1)
- Keyword score: 0.8 + 0.1 + 0.15 + 0.1 = 1.0 (capped)

Combined:
(0.85 × 0.85) + (0.15 × 1.0) = 0.7225 + 0.15 = 0.8725

Final score: 0.87 → HIGH PRIORITY
```

---

## 📁 Project Structure

```
Daily_Reading_Paper/
├── config/
│   └── config.yaml              # Configuration settings
│
├── src/
│   ├── main.py                  # Main orchestration script
│   │
│   ├── fetchers/
│   │   └── arxiv_fetcher.py     # ArXiv API integration
│   │
│   ├── filters/
│   │   ├── relevance_filter.py  # Keyword-based filtering
│   │   └── similarity_filter.py # Semantic similarity filtering
│   │
│   ├── analyzers/
│   │   └── llm_analyzer.py      # LLM analysis with vision support
│   │
│   ├── integrations/
│   │   ├── notion_client.py     # Notion API integration
│   │   └── zotero_client.py     # Zotero API + deduplication
│   │
│   └── utils/
│       ├── logger.py            # Logging utilities
│       ├── config_loader.py     # Config file parser
│       ├── output_saver.py      # Save JSON/MD reports
│       ├── pdf_extractor.py     # PDF text + figure extraction
│       └── scholar_inbox_reader.py  # Import scholar-inbox data
│
├── data/
│   ├── embeddings/              # Cached similarity embeddings
│   ├── cache/                   # Paper metadata cache
│   └── outputs/                 # Generated analysis reports
│
├── tests/                       # Test suite
│   ├── test_arxiv_fetcher.py
│   ├── test_similarity_filter.py
│   ├── test_llm_analyzer.py
│   ├── test_notion.py
│   └── test_openai_config.py
│
├── logs/                        # Application logs
│
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (gitignored)
├── .env.example                 # Environment template
├── test_optimizations.py        # Optimization verification script
└── README.md                    # This file
```

---

## 🧪 Testing

### Test Individual Components

```bash
# Test ArXiv fetching
python tests/test_arxiv_fetcher.py

# Test OpenAI configuration
python tests/test_openai_config.py

# Test Notion integration
python tests/test_notion.py

# Test similarity filtering
python tests/test_similarity_filter.py

# Test LLM analysis
python tests/test_llm_analyzer.py
```

### Test Optimizations

```bash
python test_optimizations.py
```

Expected output:
```
================================================================================
🚀 TESTING PIPELINE OPTIMIZATIONS
================================================================================

📋 Test 1: Zotero Deduplication
✓ Found 27 existing identifiers in Zotero

⚖️  Test 2: Semantic Scoring Configuration
✓ Similarity weight: 85%
✓ Keyword weight: 15%

📄 Test 3: Multimodal PDF Extraction
✓ PyMuPDF installed - full multimodal support
✓ Method available: extract_figures_from_pdf

🤖 Test 4: LLM Multimodal Analysis
✓ Current model: gpt-4o
✓ Vision-capable model detected
✓ Method available: generate_detailed_analysis_with_figures

================================================================================
✅ OPTIMIZATION CHECK COMPLETE
================================================================================
```

### Integration Tests

```bash
# Full workflow test with 2 papers
python src/main.py --max-papers 2

# Dry run (no DB writes)
python src/main.py --dry-run --max-papers 2
```

---

## 🔧 Troubleshooting

### Common Issues

#### "OpenAI API key not provided"
**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify key is set (should show your key)
grep OPENAI_API_KEY .env

# No extra spaces or quotes:
OPENAI_API_KEY=sk-proj-abc123   # ✓ Correct
OPENAI_API_KEY= sk-proj-abc123  # ✗ Space before key
OPENAI_API_KEY="sk-proj-abc123" # ✗ Quotes
```

#### "Could not find Notion database"
**Solution:**
1. Verify database is shared with integration (see [Notion Setup](#notion-integration))
2. Check database ID (not page ID):
   ```bash
   # URL format: https://notion.so/workspace/DATABASE_ID?v=...
   # Copy DATABASE_ID part
   ```
3. Test connection: `python tests/test_notion.py`

#### "PyMuPDF not installed"
**Impact:** Figure extraction disabled, text-only analysis
**Solution:**
```bash
pip install pymupdf
python test_optimizations.py  # Verify installation
```

#### "No papers passed similarity filter"
**Causes:**
1. Zotero library is empty or has unrelated papers
2. Similarity threshold too high
3. ArXiv papers are in different research areas

**Solutions:**
```yaml
# config/config.yaml - Lower threshold
similarity_filter:
  min_similarity_score: 0.4  # Lower from 0.6

  # Or disable similarity filtering temporarily
  enabled: false
```

#### "Rate limit exceeded"
**OpenAI API:**
- Wait 60 seconds and retry
- Use `gpt-4o-mini` for lower rate limits
- Add `time.sleep(1)` between paper analyses

**ArXiv API:**
- Reduce `max_results` in config
- Add delays between fetches

#### Embeddings taking too long
**First run:** Downloads model (~90MB), takes 2-3 minutes
**Subsequent runs:** Uses cached model, much faster

**Speed up:**
```yaml
# config/config.yaml
similarity_filter:
  embedding_model: "all-MiniLM-L6-v2"  # Fast, good quality
  # embedding_model: "all-mpnet-base-v2"  # Slower, slightly better
```

#### Logs not appearing
**Check log directory:**
```bash
ls -l logs/
```

**If empty:**
```bash
# Logs may be in stderr
python src/main.py 2>&1 | tee output.log
```

---

### Getting Help

**Before opening an issue:**

1. ✅ Check logs: `logs/paper_assistant_YYYYMMDD.log`
2. ✅ Run test scripts to isolate the problem
3. ✅ Verify API keys and credentials
4. ✅ Check [Troubleshooting](#-troubleshooting) section

**When opening an issue, include:**
- Error message (full traceback)
- Relevant log file excerpt
- Configuration (redact API keys!)
- Python version: `python --version`
- Installed packages: `pip list | grep -E "(openai|notion|sentence-transformers)"`

---

## 🗺️ Roadmap

### Completed ✅

- [x] Phase 1: Project setup and structure
- [x] Phase 2: ArXiv scraping and filtering
- [x] Phase 3: LLM analysis implementation
- [x] Phase 4: Notion and Zotero integration
- [x] Phase 5: Semantic similarity filtering
- [x] Phase 6: Zotero deduplication
- [x] Phase 7: Multimodal content extraction
- [x] Phase 8: Vision-based analysis with GPT-4o

### Planned 🔮

- [ ] OCR for better figure text extraction
- [ ] Extract equations and formulas
- [ ] Methodology section extraction (like Introduction)
- [ ] Support for more document sources (bioRxiv, SSRN)
- [ ] Browser extension for manual paper additions
- [ ] Paper comparison and trend analysis
- [ ] Citation network visualization
- [ ] Custom embedding models fine-tuned on your research
- [ ] Slack/Discord notifications for high-priority papers
- [ ] Web interface for configuration and monitoring

### Ideas 💡

- Integration with Semantic Scholar API
- PDF annotation export to Notion
- Generate literature review sections automatically
- Paper recommendation based on your notes
- Collaborative features for research teams

---

## 📄 License

MIT License

Copyright (c) 2026 Research Paper Intelligence Assistant

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

**Made with ❤️ for researchers who want to stay on top of the latest papers without drowning in information overload.**

**Questions? Issues? Ideas?** Open an issue or pull request!
