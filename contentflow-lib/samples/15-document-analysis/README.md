# Article Summarization Pipeline

Automatically summarize long-form articles, research papers, and blog posts using advanced AI models with key point extraction, entity recognition, and sentiment analysis.

## Overview

This sample demonstrates automated content analysis and summarization suitable for news aggregation, content curation, research workflows, and content management systems. It uses Azure OpenAI to generate concise summaries, extract key entities, and analyze sentiment from text content.

## Pipeline Flow

```
Content Loading → Text Preprocessing → AI Summarization → 
Entity Extraction → Sentiment Analysis → Output
```

### Pipeline Steps

1. **Content Loader** - Loads article content from files or storage
   - Support for local files and Azure Blob Storage
   - Parallel content retrieval
   - Temporary file management

2. **Text Preprocessor** - Cleans and normalizes text
   - Field mapping and restructuring
   - Metadata preservation
   - Format standardization

3. **AI Summarizer** - Generates concise summaries
   - Configurable summary length (brief, short, medium, detailed)
   - Multiple styles (bullet points, paragraph, abstract)
   - Key facts preservation
   - Focus area specification

4. **Entity Extractor** - Extracts named entities
   - People, organizations, locations
   - Dates, money, products, events
   - Custom entity types
   - Structured output with context

5. **Sentiment Analyzer** - Analyzes tone and sentiment
   - Document-level or sentence-level analysis
   - Positive/negative/neutral classification
   - Confidence scores
   - Emotion detection (joy, anger, sadness, etc.)

6. **Pass Through** - Final output consolidation

## Features

- **Multi-Level Summarization**: Choose from brief, short, medium, or detailed summaries
- **Smart Entity Recognition**: Automatically identify key people, places, organizations, and more
- **Sentiment Analysis**: Understand the tone and emotional content
- **Configurable Styles**: Paragraph, bullet points, or abstract format
- **Batch Processing**: Process multiple articles efficiently
- **Metadata Rich**: Preserve source information and context

## Prerequisites

- Azure subscription with:
  - Azure OpenAI resource with GPT-4 or GPT-3.5 deployment
- Python 3.8+
- Contentflow library installed

## Configuration

### Environment Variables

Create or update `samples/.env` with the following:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Pipeline Configuration

The pipeline is configured in `pipeline-config.yaml`. Key settings:

**Summarization:**
- `summary_length`: "medium" (brief, short, medium, detailed)
- `summary_style`: "paragraph" (paragraph, bullet_points, abstract)
- `preserve_key_facts`: true (ensure important facts are retained)
- `max_tokens`: 500 (adjust for longer/shorter summaries)

**Entity Extraction:**
- `entity_types`: List of entity types to extract
- `output_format`: "structured" (structured, list, text)
- `include_context`: false (include surrounding text)

**Sentiment Analysis:**
- `granularity`: "document" (document, sentence, aspect)
- `include_confidence`: true (include confidence scores)
- `include_emotions`: true (detect specific emotions)
- `scale`: "3-point" (3-point or 5-point scale)

## Usage

### Basic Execution

```bash
cd samples/15-article-summarization
python run.py
```

### Processing Custom Articles

Modify `run.py` to load your own articles:

```python
# From file
document = Content(
    id=ContentIdentifier(
        canonical_id="my_article",
        unique_id="my_article",
        source_id="articles",
        source_name="My Article",
        source_type="file",
        path="/path/to/article.txt",
    )
)

# From text
document = Content(
    id=ContentIdentifier(
        canonical_id="article_001",
        unique_id="article_001",
        source_id="articles",
        source_name="Article Title",
        source_type="text",
        path="article.txt",
    ),
    data={"text": "Your article text here..."}
)
```

### Expected Output

```
================================================================================
Article Summarization Pipeline
================================================================================

✓ Initialized article summarization pipeline
  - AI Model: gpt-4
  - Summary Style: Paragraph format (medium length)
  - Entity Types: Person, Organization, Location, Date, Product, Event

✓ Created 2 sample articles for processing

🔄 Starting article analysis...
  Processing steps:
    1. Load article content
    2. Preprocess text
    3. Generate AI summary
    4. Extract key entities
    5. Analyze sentiment

✓ Wrote detailed results to output/summarization_result.json

================================================================================
✓ Article Summarization Completed
================================================================================
  Total articles processed: 2
  Successfully analyzed: 2
  Failed: 0
  Total duration: 8.45s
  Avg per article: 4.23s

================================================================================
📄 Article Analysis Results
================================================================================

────────────────────────────────────────────────────────────────────────────────
Article 1: Climate Article
────────────────────────────────────────────────────────────────────────────────

📖 Original Text (1234 characters):
  Climate Change Summit Reaches Historic Agreement
  
  World leaders at the Global Climate Summit...

✨ AI-Generated Summary:
  World leaders at the Global Climate Summit in Geneva signed a landmark agreement 
  to reduce carbon emissions by 50% by 2030, with 195 countries committing $500 
  billion to renewable energy. The accord includes phasing out coal by 2035, 
  investing in carbon capture, and creating a Global Climate Fund for developing 
  nations.

🏷️  Extracted Entities:
  PERSON: António Guterres, Dr. Sarah Chen
  ORGANIZATION: United Nations, Greenpeace, World Wildlife Fund, MIT
  LOCATION: Geneva
  DATE: November 15-20, 2024, 2030, 2035
  MONEY: $500 billion
  EVENT: Global Climate Summit

💭 Sentiment Analysis:
  Sentiment: Positive
  Confidence: 87.50%
  Emotions: Hope, Determination

🎉 Article summarization and analysis complete!
```

## Output

Results are saved to `output/summarization_result.json` containing:
- Original article text
- AI-generated summaries
- Extracted entities with types
- Sentiment analysis results
- Processing metadata

## Use Cases

- **News Aggregation**: Automatically summarize news articles for newsletters
- **Content Curation**: Generate summaries for content recommendation systems
- **Research Workflows**: Quickly extract key points from research papers
- **Executive Summaries**: Create concise summaries of long-form reports
- **Social Media Snippets**: Generate shareable summaries for social platforms
- **Content Moderation**: Analyze sentiment and content before publication

## Customization

### Adjust Summary Length

```yaml
summary_length: detailed  # More comprehensive summary
max_tokens: 1000         # Allow longer output
```

### Change Summary Style

```yaml
summary_style: bullet_points  # Bullet point format
# or
summary_style: abstract      # Academic abstract style
```

### Focus on Specific Aspects

```yaml
focus_areas: "main arguments, key findings, methodology"
```

### Extract Custom Entities

```yaml
custom_entities: ["technology", "regulation", "metric"]
```

### Aspect-Based Sentiment

```yaml
granularity: aspect
aspects: ["product quality", "customer service", "pricing"]
```

## Advanced Features

### Batch Processing from Files

Process multiple article files:

```python
article_files = [
    "articles/article1.txt",
    "articles/article2.txt",
    "articles/article3.txt",
]

documents = []
for idx, file_path in enumerate(article_files):
    document = Content(
        id=ContentIdentifier(
            canonical_id=f"article_{idx:03d}",
            unique_id=f"article_{idx:03d}",
            source_id="file_batch",
            source_name=Path(file_path).name,
            source_type="file",
            path=file_path,
        )
    )
    documents.append(document)
```

### Load from URLs

Use web scraping to load article content:

```python
import requests
from bs4 import BeautifulSoup

url = "https://example.com/article"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
article_text = soup.get_text()

document = Content(
    id=ContentIdentifier(
        canonical_id="web_article",
        unique_id="web_article",
        source_id="web",
        source_name=url,
        source_type="url",
        path=url,
    ),
    data={"text": article_text, "source_url": url}
)
```

## Troubleshooting

**Summaries too short/long:**
- Adjust `summary_length` and `max_tokens` settings
- Try different `summary_style` options

**Missing entities:**
- Add to `entity_types` list
- Use `custom_entities` for domain-specific terms
- Lower `temperature` for more consistent extraction

**Sentiment seems incorrect:**
- Check `granularity` setting (document vs. sentence)
- Review `scale` (3-point vs. 5-point)
- Enable `include_emotions` for more detail

**API rate limiting:**
- Reduce `max_concurrent` setting
- Add delays between requests
- Check Azure OpenAI quota limits

## Performance Optimization

- **Parallel Processing**: Set `max_concurrent: 5` for faster batch processing
- **Token Optimization**: Reduce `max_tokens` for faster responses
- **Caching**: Cache summaries for repeated articles
- **Batch Size**: Process 10-20 articles per batch for optimal performance

## Next Steps

After summarization, you can:
- **Store Summaries**: Save to database or search index
- **Generate Reports**: Create automated content digests
- **Content Recommendation**: Use entities for similarity matching
- **Trend Analysis**: Aggregate sentiment across articles over time

## Related Samples

- `06-ai-analysis`: AI-powered content analysis
- `14-gpt-rag-ingestion`: Full RAG ingestion pipeline
- `12-field-transformation`: Advanced field mapping

## Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [GPT-4 Best Practices](https://platform.openai.com/docs/guides/gpt-best-practices)
- [Summarization Techniques](https://learn.microsoft.com/azure/ai-services/openai/how-to/summarization)
- [Named Entity Recognition](https://learn.microsoft.com/azure/ai-services/language-service/named-entity-recognition/overview)
