# Figure Extraction Feature

## Overview

The Daily Reading Paper system now automatically extracts figures (images, diagrams, charts) from academic papers and embeds them with their captions in both:
- **Notion documents** - Figures appear in a dedicated section with full captions
- **Markdown reports** - Figures are embedded as images with captions

## How It Works

### 1. Extraction Methods

The system uses two extraction methods with automatic fallback:

#### HTML Extraction (Preferred)
- Extracts figures from ArXiv HTML version when available
- Preserves original figure numbering (e.g., "Figure 2.1", "Figure 3")
- Downloads high-quality images directly from ArXiv servers
- Extracts captions from `<figcaption>` tags
- More reliable caption extraction

#### PDF Extraction (Fallback)
- Extracts figures from PDF when HTML is not available
- Uses PyMuPDF (fitz) to extract embedded images
- Attempts to locate captions by searching nearby text
- Sequential figure numbering (1, 2, 3...)

### 2. Figure Data Structure

Each extracted figure contains:

```python
{
    'figure_number': str,          # Original or sequential number (e.g., "2.1" or "3")
    'caption': str,                # Figure caption text
    'image_url': str,              # Direct URL to image (HTML extraction)
    'image_data': str,             # Base64 encoded image data
    'image_format': str,           # Image format (png, jpg, etc.)
    'page_num': int,               # Page number (PDF extraction)
    'sequential_index': int        # Extraction order
}
```

### 3. Output Locations

#### Notion Documents
Figures appear in a dedicated **"🖼️ Figures"** section after the metadata, containing:
- Full-size image (external URL from ArXiv)
- Caption in quote block format: "Figure X: [caption text]"

Example:
```
🖼️ Figures
──────────
[Image]
Figure 2.1: Architecture diagram showing the transformer-based model...

[Image]
Figure 3: Comparison of results across different benchmarks...
```

#### Markdown Reports
Figures are embedded between the Abstract and Summary sections:

```markdown
### Figures

![Figure 2.1](https://arxiv.org/html/2402.08954/figure1.png)

**Figure 2.1:** Architecture diagram showing the transformer-based model...

![Figure 3](https://arxiv.org/html/2402.08954/figure2.png)

**Figure 3:** Comparison of results across different benchmarks...
```

#### JSON Output
The full figure data (including base64 images) is saved in the JSON output file for programmatic access.

## Configuration

### Maximum Figures

Control the maximum number of figures extracted per paper:

```yaml
# config/config.yaml

html_extraction:
  enabled: true
  prefer_html: true
  max_figures: 3          # Maximum figures to extract (default: 3)
  download_images: true   # Download images as base64 (default: true)
```

### Timeout Settings

Configure timeouts for image downloads:

```yaml
html_extraction:
  timeouts:
    get_image: 25         # Timeout for downloading images (seconds)
    get_html: 30          # Timeout for downloading HTML
    head_request: 20      # Timeout for availability check
    connect: 10           # Connection timeout
```

## Usage

### Standard Workflow

Figures are automatically extracted during the normal workflow:

```bash
python src/main.py
```

The system will:
1. Extract figures from HTML (if available) or PDF
2. Include figures in LLM analysis (for vision models)
3. Embed figures in Notion documents
4. Save figures in markdown reports

### Deep Dive Mode

When using deep dive mode, figures are also considered in the web-enriched analysis:

```bash
python src/main.py --deep-dive
```

### Testing Figure Extraction

Test the figure extraction independently:

```bash
# Test HTML extraction
python tests/test_figure_extraction.py --html

# Test PDF extraction
python tests/test_figure_extraction.py --pdf

# Test both with validation
python tests/test_figure_extraction.py --all
```

## Examples

### Example 1: HTML Extraction

For a paper like `2402.08954` with HTML version available:

**Extracted Figures:**
```
Figure 1: Overview of the proposed robotic learning framework
Figure 2.1: Architecture diagram of the vision-language model
Figure 3: Qualitative results on manipulation tasks
```

**In Notion:**
- All 3 figures appear with full images and captions
- Images loaded from ArXiv HTML URLs
- Captions preserve original numbering

**In Markdown:**
- Images embedded as `![Figure X](url)`
- Captions formatted as bold text below images

### Example 2: PDF Extraction

For a paper without HTML version:

**Extracted Figures:**
```
Figure 1: System architecture (Page 3)
Figure 2: Experimental results (Page 5)
Figure 3: Ablation study (Page 7)
```

**In Notion:**
- Figures appear with sequential numbering
- Page numbers indicated in captions

## Technical Details

### Image Storage

- **HTML Extraction**: Images are downloaded and stored as base64 data URIs
- **PDF Extraction**: Images are extracted from PDF and converted to base64
- **Size Filtering**: Small images (<10KB) are filtered out to avoid icons/logos

### Caption Extraction

**HTML:** Extracts from `<figcaption>` tags with pattern matching:
```python
# Matches: "Figure 2.1:", "Fig 3:", "FIGURE 4."
pattern = r'^Figure\s+([\d\.]+)[:.]\s*'
```

**PDF:** Searches page text for patterns:
```python
# Matches various formats
patterns = [
    r'Figure\s*{num}[:\.]?\s*([^\n]+)',
    r'Fig\.\s*{num}[:\.]?\s*([^\n]+)',
]
```

### Notion Image Blocks

Figures use Notion's external image block type:

```python
{
    "type": "image",
    "image": {
        "type": "external",
        "external": {
            "url": "https://arxiv.org/html/2402.08954/figure1.png"
        }
    }
}
```

### Markdown Image Embedding

Markdown uses standard image syntax with base64 or URLs:

```markdown
![Alt text](https://url.com/image.png)
# or
![Alt text](data:image/png;base64,iVBORw0KG...)
```

## Troubleshooting

### No Figures Extracted

**Possible causes:**
1. Paper has no figures in the first 10 pages (PDF)
2. HTML version not available and PDF extraction failed
3. Images are too small (<10KB) and filtered out
4. Network timeout during image download

**Solutions:**
- Check paper has visual content
- Increase `max_figures` in config
- Increase timeout values
- Check logs for specific errors

### Figures Not Appearing in Notion

**Possible causes:**
1. Image URLs are invalid or expired
2. Notion API permission issues
3. Images too large for Notion

**Solutions:**
- Verify image URLs are accessible
- Check Notion integration permissions
- Review Notion API error messages in logs

### Figures Missing Captions

**Possible causes:**
1. Paper uses non-standard caption format
2. Caption text on different page (PDF)
3. HTML structure doesn't match expected format

**Solutions:**
- Check original paper for caption format
- Adjust caption extraction patterns in `html_extractor.py` or `pdf_extractor.py`
- Report issue with paper ID for pattern updates

## Performance Considerations

### Network Bandwidth

- Each figure download adds ~50-500KB of data transfer
- 3 figures per paper = ~150KB-1.5MB additional bandwidth
- Parallel requests use connection pooling for efficiency

### Processing Time

- HTML extraction: +2-5 seconds per paper
- PDF extraction: +3-10 seconds per paper
- Image downloads: ~0.5-2 seconds per figure
- Total impact: ~3-15 seconds per paper

### Storage

- Base64 encoded images increase JSON file size
- 3 figures per paper ≈ 200KB-2MB additional storage
- Consider external image hosting for large-scale deployments

## Future Enhancements

Potential improvements for figure extraction:

1. **OCR Integration**: Extract text from figures for better analysis
2. **Figure Type Classification**: Identify diagrams, charts, photos, etc.
3. **Table Extraction**: Extract and format tables alongside figures
4. **Interactive Figures**: Preserve interactive elements (if available)
5. **Higher Resolution**: Download high-res versions when available
6. **Caption Enhancement**: Use LLM to improve/standardize captions
7. **Cross-Reference Extraction**: Link figures to text references

## API Reference

### HTMLExtractor.extract_figures()

```python
def extract_figures(
    html_content: str,
    arxiv_id: str = None,
    download_images: bool = True
) -> List[Dict]:
    """
    Extract figures with captions from HTML.

    Args:
        html_content: Raw HTML string
        arxiv_id: ArXiv paper ID for constructing image URLs
        download_images: Whether to download images as base64

    Returns:
        List of figure dicts with:
            - image_data: Base64 encoded image
            - image_url: Direct URL to image
            - caption: Figure caption text
            - figure_number: Original figure number
            - sequential_index: Extraction order
    """
```

### PDFTextExtractor.extract_figures_from_pdf()

```python
def extract_figures_from_pdf(
    pdf_content: bytes,
    max_figures: int = 5
) -> List[Dict]:
    """
    Extract figures/images from PDF with captions.

    Args:
        pdf_content: PDF file bytes
        max_figures: Maximum number of figures to extract

    Returns:
        List of dicts with:
            - image_data: Base64 encoded image
            - image_format: File extension (png, jpg, etc.)
            - caption: Extracted caption
            - page_num: Page number
            - figure_number: Sequential figure number
            - size_bytes: Image size in bytes
    """
```

## License

This feature is part of the Daily Reading Paper system and follows the same license terms.

## Contributing

To improve figure extraction:

1. Test with various paper formats
2. Report extraction failures with paper IDs
3. Suggest caption pattern improvements
4. Contribute alternative extraction methods

For questions or issues, please open a GitHub issue with:
- Paper ArXiv ID
- Extraction method used (HTML/PDF)
- Expected vs. actual results
- Relevant log output
