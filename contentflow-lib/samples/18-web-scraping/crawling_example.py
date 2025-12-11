"""
Crawling web scraping example using the WebScrapingExecutor.

This example demonstrates:
- Basic web page scraping
- Data extraction using CSS selectors
- Screenshot capture and saving to file
"""

import asyncio
import sys
import os
import yaml
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.executors import WebScrapingExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

logger = logging.getLogger(__name__)

setup_logging()


async def main():
    """Run the web scraping example."""
    
    # Load configuration
    config_path = Path(__file__).parent / "crawling_example.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    executor_config = config['executors'][0]
    
    # Create executor
    logger.info("Creating WebScrapingExecutor...")
    executor = WebScrapingExecutor(
        id=executor_config['id'],
        settings=executor_config['settings']
    )

    # Execute scraping
    logger.info("Starting web scraping...")
    results = await executor.process_input(input=None, ctx=None)
    
    # Display results
    logger.info(f"Scraped {len(results)} page(s)")
    
    # write results to output folder
    output_folder = Path(__file__).parent / "output"
    output_folder.mkdir(exist_ok=True)
    output_file = output_folder / "crawling_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
            f.write("[\n")
            for result in results:
                f.write(result.model_dump_json(indent=2))
                if result != results[-1]:
                    f.write(",\n")
            f.write("]\n")
    print(f"  Wrote output to {output_file}")
    
    for i, content in enumerate(results):
        output = content.data.get('web_scraping_output', {})
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Page {i+1}: {output.get('url')}")
        logger.info(f"Title: {output.get('title')}")
        logger.info(f"Timestamp: {output.get('timestamp')}")
        
        # Show extracted fields
        extracted = output.get('extracted_fields', {})
        logger.info(f"\nExtracted Fields:")
        for field, value in extracted.items():
            if value:
                preview = value[:100] + '...' if len(value) > 100 else value
                logger.info(f"  {field}: {preview}")
        
        # Show screenshot info
        if output.get('screenshot_path'):
            logger.info(f"\nScreenshot saved to: {output.get('screenshot_path')}")
        elif output.get('screenshot_base64'):
            logger.info(f"\nScreenshot captured (base64, {len(output.get('screenshot_base64'))} chars)")
        
        # Summary data
        logger.info(f"\nSummary:")
        logger.info(f"  Status: {content.summary_data.get('extraction_status')}")
        logger.info(f"  Pages Scraped: {content.summary_data.get('pages_scraped')}")
    
    logger.info(f"\n{'='*60}")
    logger.info("Web scraping completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
