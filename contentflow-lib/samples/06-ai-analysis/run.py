#!/usr/bin/env python
"""
AI Agent Test Runner

Run individual AI executor tests organized in sub-folders.

Usage:
    python run.py                    # Show interactive menu
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def print_menu():
    """Display the test selection menu"""
    print("\n" + "=" * 70)
    print("AI AGENT EXECUTOR TEST SUITE")
    print("=" * 70)
    print("\nAvailable Tests:")
    print("  1. agent      - AI Agent Executor (general purpose AI agent)")
    print("  2. summarize  - Summarization Executor (content summarization)")
    print("  3. entities   - Entity Extraction Executor (extract named entities)")
    print("  4. sentiment  - Sentiment Analysis Executor (analyze sentiment)")
    print("  5. classify   - Content Classifier Executor (categorize content)")
    print("  6. pii        - PII Detector Executor (detect and redact PII)")
    print("  7. keywords   - Keyword Extractor Executor (extract keywords)")
    print("  8. language   - Language Detector Executor (detect text language)")
    print("  9. translate  - Translation Executor (translate text)")
    print("\n  0. exit       - Exit")
    print("=" * 70)


def get_test_choice():
    """Get user's test choice interactively"""
    while True:
        choice = input("\nSelect test to run (1-10, or 0 to exit): ").strip()
        
        test_map = {
            '1': 'agent',
            '2': 'summarize',
            '3': 'entities',
            '4': 'sentiment',
            '5': 'classify',
            '6': 'pii',
            '7': 'keywords',
            '8': 'language',
            '9': 'translate',
            '0': 'exit'
        }
        
        if choice in test_map:
            return test_map[choice]
        else:
            print("Invalid choice. Please enter a number from 0-10.")
            
async def run_test(test_name: str):
    """Run the specified test by importing and executing its run function"""
    test_modules = {
        'agent': ('01-ai-agent', 'AI Agent'),
        'summarize': ('02-summarization', 'Summarization'),
        'entities': ('03-entity-extraction', 'Entity Extraction'),
        'sentiment': ('04-sentiment-analysis', 'Sentiment Analysis'),
        'classify': ('05-content-classifier', 'Content Classifier'),
        'pii': ('06-pii-detector', 'PII Detector'),
        'keywords': ('07-keyword-extractor', 'Keyword Extractor'),
        'language': ('08-language-detector', 'Language Detector'),
        'translate': ('09-translation', 'Translation'),
    }
    if test_name not in test_modules:
        print(f"Unknown test: {test_name}")
        print("Available tests: agent, summarize, entities, sentiment, classify, pii, keywords, language, translate")
        return False
    
    folder_name, test_title = test_modules[test_name]
    
    try:
        # Import the module from the sub-folder
        current_dir = Path(__file__).parent
        test_dir = current_dir / folder_name
        
        # Add test directory to path temporarily
        sys.path.insert(0, str(test_dir))
        
        try:
            import run
            await run.run_pipeline()
            return True
        finally:
            # Remove from path
            sys.path.remove(str(test_dir))
        
    except Exception as e:
        print(f"\n✗ Failed to run {test_title} test")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_usage():
    """Print usage information"""
    print(__doc__)


if __name__ == "__main__":
    
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)
    
    # Check if test specified via command line
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type in ["agent", "ai-agent"]:
            asyncio.run(run_test("agent"))
        elif test_type in ["summarize", "summary", "summarization"]:
            asyncio.run(run_test("summarize"))
        elif test_type in ["entities", "entity", "entity-extraction"]:
            asyncio.run(run_test("entities"))
        elif test_type in ["sentiment", "sentiment-analysis"]:
            asyncio.run(run_test("sentiment"))
        elif test_type in ["classify", "classifier", "classification"]:
            asyncio.run(run_test("classify"))
        elif test_type in ["keywords", "keyword", "keyword-extractor"]:
            asyncio.run(run_test("keywords"))
        elif test_type in ["language", "lang", "language-detector", "detect"]:
            asyncio.run(run_test("language"))
        elif test_type in ["translate", "translation", "translator"]:
            asyncio.run(run_test("translate"))
            
        else:
            print(f"Unknown test type: {test_type}")
            print_usage()
            sys.exit(1)
    
    else:
        # Interactive menu mode
        print_menu()
        choice = get_test_choice()
        
        if choice == 'exit':
            print("\nExiting...")
            sys.exit(0)        
        else:
            print(f"\n{'=' * 70}")
            print(f"Starting {choice.upper()} run...")
            print(f"{'=' * 70}\n")
            
            success = asyncio.run(run_test(choice))
            
            if success:
                print("\nRun completed successfully.")
            else:
                print("\nRun failed.")
                
