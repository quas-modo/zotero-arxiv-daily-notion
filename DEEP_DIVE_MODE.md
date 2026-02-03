# Deep Dive Mode with Web Search - Feature Documentation

## Overview

The Deep Dive Mode enhances paper analysis by using OpenAI's native tool-calling feature with web search. This allows the LLM to automatically search for additional context, official documentation, and related resources while analyzing papers.

---

## 🌟 Key Features

### 1. **Integrated Web Search**
- Uses GPT-4o (or later) with `tools: [{"type": "web_search"}]`
- Automatic search for specialized terms and frameworks
- No manual text extraction required

### 2. **Context Enrichment**
When analyzing a paper, the model can search for:
- 🔍 Official documentation for frameworks (e.g., RT-1, RT-2, PaLM-E)
- 💻 GitHub repositories for implementations
- 📝 Related blog posts and technical articles
- 📊 Comparison articles and benchmarks
- 🎓 Related academic work

### 3. **Structured Citations**
- Captures all web sources used during analysis
- Formats citations as clickable links in Notion
- Includes snippets for context
- Distinguished by source type (web_search, inline_citation)

### 4. **Fallback Mechanism**
- Primary: Standard PDF-based analysis (fast, reliable)
- Deep Dive: Web search enrichment (slower, richer context)
- Automatic fallback if web search fails

---

## 🚀 Usage

### Command Line

```bash
# Standard mode (default)
python src/main.py --max-papers 3

# Deep dive mode with web search
python src/main.py --max-papers 3 --deep-dive

# Deep dive with dry run
python src/main.py --max-papers 2 --deep-dive --dry-run
```

### Configuration File

Enable deep dive mode by default in `config/config.yaml`:

```yaml
llm:
  provider: "openai"
  deep_dive_mode: true  # Enable by default
```

**Priority:** CLI flag `--deep-dive` > config file > default (false)

---

## 🔧 How It Works

### Analysis Flow

```
┌─────────────────────────────────────────────┐
│ 1. Extract PDF Content                     │
│    - Full text, introduction, figures      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 2. Generate Summary (Standard)             │
│    - No web search, fast                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. Deep Dive Analysis with Web Search     │
│    - LLM identifies specialized terms      │
│    - Automatically searches the web        │
│    - Enriches analysis with context        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. Extract & Structure Citations          │
│    - Parse tool call results               │
│    - Extract inline citations              │
│    - Format as structured sources          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 5. Save to Notion with Web Sources        │
│    - New "Web Search Sources" section      │
│    - Clickable links with descriptions     │
└─────────────────────────────────────────────┘
```

### Web Search Triggers

The LLM is instructed to search when it encounters:

1. **Robotics Frameworks**
   - RT-1, RT-2, PaLM-E, OpenVLA
   - World model implementations
   - Action prediction models

2. **Novel Architectures**
   - Specific model names
   - Framework implementations
   - Architecture designs

3. **Datasets & Benchmarks**
   - Dataset names (DROID, Bridge, etc.)
   - Benchmark comparisons
   - Evaluation metrics

4. **Technical Concepts**
   - Specialized terminology
   - Novel methods
   - Implementation details

---

## 📊 Output Structure

### Standard Mode Output

```json
{
  "summary": "...",
  "detailed_analysis": "...",
  "summary_zh": "...",
  "detailed_analysis_zh": "...",
  "analysis_model": "gpt-4o-mini",
  "num_figures_analyzed": 3
}
```

### Deep Dive Mode Output

```json
{
  "summary": "...",
  "detailed_analysis": "... [Source: RT-1 Documentation](https://robotics.google.com) ...",
  "summary_zh": "...",
  "detailed_analysis_zh": "...",
  "analysis_model": "gpt-4o",
  "num_figures_analyzed": 3,
  "web_sources": [
    {
      "title": "RT-1: Robotics Transformer for Real-World Control",
      "url": "https://robotics.google.com/rt-1",
      "snippet": "RT-1 is a multi-task model that tokenizes robot inputs...",
      "source_type": "web_search"
    },
    {
      "title": "RT-1 GitHub Repository",
      "url": "https://github.com/google-research/robotics_transformer",
      "snippet": "",
      "source_type": "inline_citation"
    }
  ],
  "analysis_mode": "deep_dive_with_web_search"
}
```

---

## 📝 Notion Display

### Standard Mode
- Title, authors, metadata
- Summary (Chinese + English)
- Detailed analysis
- Links & Resources (PDF, ArXiv, GitHub)

### Deep Dive Mode (Additional Section)
```
🌐 Web Search Sources (Deep Dive Mode)
───────────────────────────────────────
ℹ️ Found 5 web sources to provide additional context

1. RT-1: Robotics Transformer for Real-World Control
   https://robotics.google.com/rt-1
   RT-1 is a multi-task model that tokenizes robot inputs...

2. OpenVLA: An Open-Source Vision-Language-Action Model
   https://openvla.github.io
   OpenVLA combines pre-trained vision and language...

3. GitHub: google-research/robotics_transformer
   https://github.com/google-research/robotics_transformer
```

---

## ⚡ Performance Comparison

| Metric | Standard Mode | Deep Dive Mode |
|--------|--------------|----------------|
| **Time per paper** | ~30-45s | ~60-90s |
| **Tokens used** | ~3,000 | ~5,000-8,000 |
| **Cost (gpt-4o)** | ~$0.015 | ~$0.025-0.04 |
| **Context depth** | Good | Excellent |
| **Citations** | 0 | 3-10 |
| **Accuracy** | High | Very High |

**Recommendation:**
- **Standard mode:** Daily automated runs, quick analysis
- **Deep dive mode:** Important papers, unfamiliar topics, research reviews

---

## 🔒 Requirements

### Model Requirements
- **Required:** GPT-4o or later (web search tool support)
- **Not supported:** GPT-4o-mini, GPT-4, GPT-3.5 (lacks web search)

```bash
# .env
OPENAI_MODEL=gpt-4o  # Required for web search
```

### API Access
- OpenAI API key with access to tool-calling
- Web search tool availability (check OpenAI dashboard)

---

## 🧪 Testing

### Test Deep Dive Mode

```bash
# Test with 1 paper
python src/main.py --max-papers 1 --deep-dive

# Expected output:
# 🤖 STEP 4: Analyzing papers with LLM
# 🌐 Deep Dive Mode ENABLED - Using web search
#   [1/1] Paper title...
#      ✓ Complete (with 5 web sources)
```

### Verify in Notion

1. Check the created Notion entry
2. Look for "🌐 Web Search Sources" section
3. Verify clickable links to sources
4. Confirm context is enriched

### Test Fallback

```bash
# Use non-web-search model (should fallback gracefully)
OPENAI_MODEL=gpt-4o-mini python src/main.py --max-papers 1 --deep-dive
```

Expected: Warning + fallback to standard mode

---

## 🐛 Troubleshooting

### Issue: "Web search tool not available"

**Cause:** Using a model without web search support

**Solution:**
```bash
# Use gpt-4o or later
export OPENAI_MODEL=gpt-4o
python src/main.py --deep-dive
```

### Issue: No web sources captured

**Possible causes:**
1. LLM didn't find terms worth searching
2. Model didn't use web search tool
3. Parsing failed

**Debug:**
```bash
# Check logs for tool calls
tail -f logs/paper_assistant_*.log | grep "web_search"
```

### Issue: Deep dive too slow

**Solution 1:** Use standard mode for most papers
```bash
# Standard for daily runs
python src/main.py

# Deep dive for specific papers
python src/main.py --max-papers 3 --deep-dive
```

**Solution 2:** Reduce paper count
```bash
# Fewer papers in deep dive
python src/main.py --max-papers 2 --deep-dive
```

### Issue: Higher costs

**Expected:** Deep dive uses 1.5-2x more tokens

**Mitigation:**
- Use selectively (important papers only)
- Set `deep_dive_mode: false` in config (use CLI flag when needed)
- Monitor usage in OpenAI dashboard

---

## 💡 Best Practices

### When to Use Deep Dive Mode

✅ **Good use cases:**
- Papers about unfamiliar frameworks
- Novel architectures you haven't seen
- Papers with many specialized terms
- Research reviews and surveys
- Papers you plan to cite in your work

❌ **Not needed for:**
- Papers in your core area (you know the terms)
- Incremental improvements
- Daily automated runs (too slow/expensive)
- Papers with clear abstracts

### Optimization Tips

1. **Hybrid approach:**
   ```bash
   # Daily: Standard mode for 10 papers
   python src/main.py

   # Weekly: Deep dive for top 3 most interesting
   python src/main.py --max-papers 3 --deep-dive
   ```

2. **Configure selectively:**
   ```yaml
   # config.yaml
   llm:
     deep_dive_mode: false  # Keep off by default
   ```

   Use CLI flag when needed:
   ```bash
   python src/main.py --deep-dive  # Explicit opt-in
   ```

3. **Monitor costs:**
   - Check OpenAI usage dashboard
   - Set budget alerts
   - Review monthly spending

---

## 🎯 Example Output

### Paper: "OpenVLA: Open-Source Vision-Language-Action Model"

**Standard Mode Analysis:**
```markdown
## Core Methodology
The paper introduces OpenVLA, a vision-language-action model...
```

**Deep Dive Mode Analysis:**
```markdown
## Core Methodology
The paper introduces OpenVLA, a vision-language-action model that builds
on the Prismatic-7B architecture [Source: Prismatic VLM](https://github.com/...)
and extends it for robotics applications. Unlike previous approaches like
RT-2 [Source: RT-2 Documentation](https://robotics.google.com/rt-2), OpenVLA
is fully open-source and demonstrates competitive performance on...

## Implementation Details
The code is available on GitHub [Source: OpenVLA Repository](https://github.com/openvla)
and includes pre-trained checkpoints. The model uses the Bridge dataset
[Source: Bridge Data](https://rail.eecs.berkeley.edu/datasets/bridge_release/)
for training and evaluation...
```

**Web Sources Captured:**
1. Prismatic VLM Repository
2. RT-2 Official Documentation
3. OpenVLA GitHub Repository
4. Bridge Dataset Documentation
5. Related blog post on embodied AI

---

## 📚 Related Documentation

- [Main README](README.md) - Full system documentation
- [PIPELINE_OPTIMIZATIONS.md](PIPELINE_OPTIMIZATIONS.md) - Recent improvements
- [OpenAI Tool Calling Docs](https://platform.openai.com/docs/guides/function-calling) - API reference

---

## 🔄 Future Enhancements

Potential improvements:

- [ ] **Custom search domains:** Limit to specific sites (GitHub, arXiv, official docs)
- [ ] **Citation formatting:** APA, BibTeX export
- [ ] **Search query optimization:** Better query generation
- [ ] **Cost tracking:** Per-paper cost estimation
- [ ] **Selective enrichment:** Only search for unknown terms
- [ ] **Cache search results:** Reuse for similar papers

---

**Status:** ✅ Fully implemented and tested

**Last Updated:** February 2026

**Questions?** Check the troubleshooting section or open an issue!
