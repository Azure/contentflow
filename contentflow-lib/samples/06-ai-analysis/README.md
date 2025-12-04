# AI Agent Tests - Organized Structure

This directory contains various AI executor tests, each organized in its own sub-folder for better maintainability.

## Directory Structure

```
06-ai-agent/
├── 01-ai-agent/              # General AI Agent executor test
│   ├── run.py
│   └── pipeline_config.yaml
├── 02-summarization/         # Summarization executor test
│   ├── run.py
│   └── summarization_config.yaml
├── 03-entity-extraction/     # Entity extraction executor test
│   ├── run.py
│   └── entity_extraction_config.yaml
├── 04-sentiment-analysis/    # Sentiment analysis executor test
│   ├── run.py
│   └── sentiment_analysis_config.yaml
├── 05-content-classifier/    # Content classifier executor test
│   ├── run.py
│   └── content_classifier_config.yaml
├── run.py                    # Main test runner with menu
└── test_all.py              # Run all tests sequentially
```

## Running Tests

### Option 1: Interactive Menu

Run the main `run.py` without arguments to get an interactive menu:

```bash
python run.py
```

This will display:
```
======================================================================
AI AGENT EXECUTOR TEST SUITE
======================================================================

Available Tests:
  1. agent      - AI Agent Executor (general purpose AI agent)
  2. summarize  - Summarization Executor (content summarization)
  3. entities   - Entity Extraction Executor (extract named entities)
  4. sentiment  - Sentiment Analysis Executor (analyze sentiment)
  5. classify   - Content Classifier Executor (categorize content)
  6. all        - Run all tests sequentially

  0. exit       - Exit
======================================================================
```

### Option 2: Command Line Arguments

Run specific tests directly from the command line:

```bash
# Run AI Agent test
python run.py agent

# Run Summarization test
python run.py summarize

# Run Entity Extraction test
python run.py entities

# Run Sentiment Analysis test
python run.py sentiment

# Run Content Classifier test
python run.py classify
```

### Option 3: Run All Tests

To run all tests sequentially:

```bash
python test_all.py
```

Or run specific test via test_all.py:

```bash
python test_all.py agent
python test_all.py summarize
python test_all.py entities
python test_all.py sentiment
python test_all.py classify
```

## Test Descriptions

### 1. AI Agent Executor (`01-ai-agent`)
Tests the general-purpose Azure OpenAI agent executor for processing content with custom instructions.

**Features:**
- Configurable AI agent instructions
- Support for conversation history
- Flexible input/output field mapping

### 2. Summarization Executor (`02-summarization`)
Tests content summarization with different styles and formats.

**Features:**
- Brief, detailed, or bullet-point summaries
- Configurable summary length
- Support for various content types

### 3. Entity Extraction Executor (`03-entity-extraction`)
Tests extraction of named entities from text.

**Features:**
- Extract organizations, people, locations, dates
- Monetary values and contact information
- Context extraction for each entity

### 4. Sentiment Analysis Executor (`04-sentiment-analysis`)
Tests sentiment analysis capabilities.

**Features:**
- Positive/Negative/Neutral classification
- Confidence scores
- Emotion detection
- Explanations for sentiment decisions

### 5. Content Classifier Executor (`05-content-classifier`)
Tests content categorization into predefined categories.

**Features:**
- Multi-category support (Technology, Business, Science, etc.)
- Confidence scores
- Category distribution analysis
- Explanations for classifications

## Output

Each test creates its own output folder within its sub-directory:
- `01-ai-agent/output/pipeline_result.json`
- `02-summarization/output/summarization_result.json`
- `03-entity-extraction/output/entity_extraction_result.json`
- `04-sentiment-analysis/output/sentiment_analysis_result.json`
- `05-content-classifier/output/content_classifier_result.json`

## Running Individual Tests Directly

You can also run each test directly from its sub-folder:

```bash
cd 01-ai-agent
python run.py

cd ../02-summarization
python run.py

# etc...
```

## Configuration

Each test has its own configuration file in YAML format. Modify these files to:
- Change AI model settings
- Adjust executor parameters
- Modify input/output field mappings
- Configure processing behavior

## Environment Variables

Make sure to set up your `.env` file in the `samples/` directory with:
```
AZURE_OPENAI_ENDPOINT=your_endpoint_here
# Add other required environment variables
```
