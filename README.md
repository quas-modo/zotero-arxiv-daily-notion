# Research Paper Intelligence Assistant

An automated tool that discovers, analyzes, and archives academic papers from ArXiv daily.

## Features

- 📚 **Automated Paper Discovery**: Fetches latest papers from ArXiv (AI/ML/Robotics categories)
- 🎯 **Smart Filtering**:
  - **Similarity-based**: Compares papers to your Zotero library using semantic embeddings
  - **Keyword matching**: Boosts papers matching your research interests
  - **Hybrid scoring**: Combines both methods for personalized recommendations
- 🤖 **Dual-Layer Analysis**:
  - Summary: Concise TL;DR of core contributions
  - Detailed: Deep-dive analysis with methodology and findings
- 📝 **Notion Integration**: Automatically creates organized entries in your Notion database
- 📖 **Zotero Sync**: Optional integration with Zotero for reference management
- ⏰ **Daily Automation**: Runs automatically every day

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
  - **Custom Endpoint Support**: If you need to use a proxy or custom endpoint, set `OPENAI_BASE_URL` in `.env`
  - See [OPENAI_CONFIG.md](OPENAI_CONFIG.md) for detailed configuration guide
- **Notion Integration Token**: Create integration at https://www.notion.so/my-integrations
- **Notion Database ID**: Create a database and share it with your integration

Optional:
- **Zotero API Key**: Get from https://www.zotero.org/settings/keys

### 3. Create Notion Database

1. Go to Notion and create a new database
2. Add the following properties:
   - Title (Title)
   - Authors (Text)
   - Published Date (Date)
   - Categories (Multi-select)
   - Keywords (Multi-select)
   - ArXiv ID (Text)
   - PDF Link (URL)
   - GitHub (URL)
   - Summary (Text)
   - Detailed Analysis (Text)
3. Share the database with your integration
4. Copy the database ID from the URL and add to `.env`

### 4. Customize Research Interests

Edit `config/config.yaml` to add your specific research keywords and preferences.

**NEW**: For personalized similarity-based filtering, see [SIMILARITY_FILTER_GUIDE.md](SIMILARITY_FILTER_GUIDE.md) to:
- Configure Zotero integration for semantic paper matching
- Import scholar-inbox.com recommendations
- Fine-tune similarity thresholds and scoring weights

## Usage

### Quick Start

```bash
# Run the full workflow (fetch, filter, analyze, sync to Notion)
./run.sh src/main.py

# Limit to 3 papers (recommended for testing)
./run.sh src/main.py --max-papers 3

# Dry run (don't create Notion entries)
./run.sh src/main.py --dry-run
```

### Manual Run

```bash
# Using the helper script
./run.sh src/main.py

# Or using full Python path
/mnt/shared-storage-user/chenxinyi1/env/miniconda3/envs/daily_reading_paper/bin/python src/main.py
```

### Automated Daily Run

The script includes a scheduler that runs daily at 9 AM UTC. To start the scheduler:

```bash
./run.sh src/main.py --schedule
```

### Run as Background Service (Linux/Mac)

Using cron:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/Daily_Reading_Paper && /path/to/conda/envs/daily_reading_paper/bin/python src/main.py

# Or use the helper script
0 9 * * * cd /path/to/Daily_Reading_Paper && ./run.sh src/main.py
```

## Project Structure

```
Daily_Reading_Paper/
├── config/
│   └── config.yaml           # Configuration settings
├── src/
│   ├── main.py              # Main orchestration script
│   ├── fetchers/
│   │   └── arxiv_fetcher.py # ArXiv API integration
│   ├── filters/
│   │   ├── relevance_filter.py # Keyword-based filtering
│   │   └── similarity_filter.py # Similarity-based filtering
│   ├── analyzers/
│   │   └── llm_analyzer.py  # LLM-based analysis
│   ├── integrations/
│   │   ├── notion_client.py # Notion API integration
│   │   └── zotero_client.py # Zotero API integration
│   └── utils/
│       ├── logger.py        # Logging utilities
│       └── scholar_inbox_reader.py # Scholar-inbox import
├── data/
│   ├── embeddings/          # Cached embeddings for similarity
│   ├── cache/               # Cached paper metadata
│   └── outputs/             # Generated reports
└── logs/                    # Application logs
```

## Roadmap

- [x] Phase 1: Project setup and structure
- [x] Phase 2: ArXiv scraping and filtering
- [x] Phase 3: LLM analysis implementation
- [x] Phase 4: Notion and Zotero integration
- [ ] Phase 5: Daily automation and deployment (ready to use!)

## Documentation

- [SIMILARITY_FILTER_GUIDE.md](SIMILARITY_FILTER_GUIDE.md) - **NEW!** Similarity-based filtering guide
- [NOTION_SETUP.md](NOTION_SETUP.md) - Complete Notion integration guide
- [OPENAI_CONFIG.md](OPENAI_CONFIG.md) - OpenAI API configuration (including proxies)
- [TEST_RESULTS.md](TEST_RESULTS.md) - Testing results and validation

## License

MIT License