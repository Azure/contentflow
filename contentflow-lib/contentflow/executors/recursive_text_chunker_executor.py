"""Recursive text chunker executor for creating chunks using recursive splitting strategy."""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from . import ParallelExecutor
from ..models import Content

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_index: int
    char_count: int
    word_count: int
    split_level: int  # Which separator level was used for this chunk
    separator_used: Optional[str]
    page_numbers: Optional[List[int]] = None


class RecursiveTextChunkerExecutor(ParallelExecutor):
    """
    Create chunks using recursive text splitting strategy.
    
    This executor recursively splits text using a hierarchy of separators,
    starting with larger separators (paragraphs) and working down to smaller
    ones (sentences, words) if chunks are still too large. This approach is
    inspired by LangChain's RecursiveCharacterTextSplitter and works with
    output from any extractor (PDF, Word, PowerPoint, etc.).
    
    The recursive strategy ensures:
    - Natural semantic boundaries are preserved when possible
    - Large chunks are progressively split using finer separators
    - Optimal chunk sizes for RAG and embedding models
    - Configurable overlap between chunks for context continuity
    
    Configuration (settings dict):
        - input_field (str): Field containing extracted text
          Default: "text" (works with most extractors)
          For PDFExtractor output: "pdf_output.text"
          For WordExtractor output: "word_output.text"
          For PowerPointExtractor output: "ppt_output.text"
        - output_field (str): Field name for chunk output
          Default: "chunks"
        - chunk_size (int): Target maximum chunk size in characters
          Default: 1000
        - chunk_overlap (int): Overlap between chunks in characters
          Default: 200
        - separators (List[str]): Hierarchy of separators to try (in order)
          Default: ["\n\n", "\n", ". ", " ", ""]
          Common alternatives:
            - ["\n\n\n", "\n\n", "\n", ". ", " ", ""] for more paragraph focus
            - ["\n\n", "\n", "。", ".", " ", ""] for multilingual (Chinese/Japanese)
        - length_function (str): How to measure text length
          Default: "characters"
          Options: "characters", "words", "tokens" (approximate)
        - keep_separator (bool): Whether to keep separators in the chunks
          Default: True
        - strip_whitespace (bool): Strip leading/trailing whitespace from chunks
          Default: True
        - min_chunk_size (int): Minimum viable chunk size (merge if smaller)
          Default: 100
        - add_metadata (bool): Include detailed chunk metadata
          Default: True
        - include_page_numbers (bool): Track page numbers for chunks (when available)
          Default: True
          Note: Requires input from extractors that provide page data (PDF, Word, PowerPoint)

        Also setting from ParallelExecutor and BaseExecutor apply.
    
    Example:
        ```python
        # Basic recursive chunking with default separators
        executor = RecursiveTextChunkerExecutor(
            id="chunker",
            settings={
                "chunk_size": 1000,
                "chunk_overlap": 200,
            }
        )
        
        # Custom separators for code or structured text
        executor = RecursiveTextChunkerExecutor(
            id="chunker",
            settings={
                "separators": ["\n\n", "\n", ";", " ", ""],
                "chunk_size": 500,
                "chunk_overlap": 50,
            }
        )
        
        # Working with PDF extractor output
        executor = RecursiveTextChunkerExecutor(
            id="chunker",
            settings={
                "input_field": "pdf_output.text",
                "chunk_size": 1500,
                "chunk_overlap": 300,
            }
        )
        
        # Word-based chunking instead of character-based
        executor = RecursiveTextChunkerExecutor(
            id="chunker",
            settings={
                "length_function": "words",
                "chunk_size": 200,  # 200 words
                "chunk_overlap": 40,  # 40 words overlap
            }
        )
        ```
    
    Input:
        Document or List[Document] with extracted text in specified input_field
        
    Output:
        Document or List[Document] with added fields:
        - data['chunks']: List of chunk dictionaries containing:
          - 'text': Chunk text content
          - 'metadata': ChunkMetadata with tracking info (if add_metadata=True)
        - summary_data['chunks_created']: Number of chunks created
        - summary_data['avg_chunk_size']: Average chunk size
        - summary_data['chunking_method']: "recursive"
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        # Field configuration
        self.input_field = self.get_setting("input_field", default="text")
        self.output_field = self.get_setting("output_field", default="chunks")
        
        # Chunking parameters
        self.chunk_size = self.get_setting("chunk_size", default=1000)
        self.chunk_overlap = self.get_setting("chunk_overlap", default=200)
        self.min_chunk_size = self.get_setting("min_chunk_size", default=100)
        
        # Separator hierarchy
        default_separators = ["\n\n", "\n", ". ", " ", ""]
        self.separators = self.get_setting("separators", default=default_separators)
        
        # Length measurement
        self.length_function = self.get_setting("length_function", default="characters")
        valid_length_functions = ["characters", "words", "tokens"]
        if self.length_function not in valid_length_functions:
            raise ValueError(
                f"Invalid length_function: {self.length_function}. "
                f"Must be one of {valid_length_functions}"
            )
        
        # Processing options
        self.keep_separator = self.get_setting("keep_separator", default=True)
        self.strip_whitespace = self.get_setting("strip_whitespace", default=True)
        self.add_metadata = self.get_setting("add_metadata", default=True)
        self.include_page_numbers = self.get_setting("include_page_numbers", default=True)
        
        # Validation
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("min_chunk_size cannot exceed chunk_size")
        
        if not self.separators:
            raise ValueError("separators list cannot be empty")
        
        if self.debug_mode:
            logger.debug(
                f"RecursiveTextChunkerExecutor {self.id} initialized: "
                f"chunk_size={self.chunk_size}, overlap={self.chunk_overlap}, "
                f"separators={self.separators}, length_function={self.length_function}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process a single document to create chunks.
           Implements the abstract method from ParallelExecutor.
        """
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Extract text from input field (supports nested fields like "pdf_output.text")
            text = self._get_nested_field(content.data, self.input_field)
            
            if not text:
                raise ValueError(f"No text found in field: {self.input_field}")
            
            if not isinstance(text, str):
                raise ValueError(f"Field {self.input_field} must contain string text, got {type(text)}")
            
            if self.debug_mode:
                logger.debug(
                    f"Processing document {content.id}: "
                    f"{len(text)} chars, using recursive chunking"
                )
            
            # Extract page data if available (from PDF, Word, PowerPoint extractors)
            pages_data = self._extract_pages_data(content.data, self.input_field)
            
            # Create chunks using recursive splitting
            chunks = self._split_text_recursive(text)
            
            # Add page numbers to chunks if available
            if self.include_page_numbers and pages_data:
                chunks = self._add_page_numbers_to_chunks(chunks, text, pages_data)
            
            # Apply overlap between chunks
            if self.chunk_overlap > 0:
                chunks = self._apply_overlap(chunks, text)
            
            # Merge chunks that are too small
            chunks = self._merge_small_chunks(chunks)
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk_data in enumerate(chunks):
                chunk_obj = {'text': chunk_data['text']}
                
                if self.add_metadata:
                    chunk_obj['metadata'] = {
                        'chunk_index': i,
                        'char_count': len(chunk_data['text']),
                        'word_count': len(chunk_data['text'].split()),
                        'split_level': chunk_data.get('split_level', 0),
                        'separator_used': chunk_data.get('separator_used'),
                        'page_numbers': chunk_data.get('page_numbers'),
                    }
                
                chunk_objects.append(chunk_obj)
            
            # Store chunks
            content.data[self.output_field] = chunk_objects
            
            # Update summary
            if chunk_objects:
                avg_size = sum(len(c['text']) for c in chunk_objects) / len(chunk_objects)
                content.summary_data['chunks_created'] = len(chunk_objects)
                content.summary_data['avg_chunk_size'] = int(avg_size)
                content.summary_data['chunking_method'] = "recursive"
            else:
                content.summary_data['chunks_created'] = 0
                content.summary_data['avg_chunk_size'] = 0
                content.summary_data['chunking_method'] = "recursive"
            
            if self.debug_mode:
                logger.debug(f"Created {len(chunk_objects)} chunks for document {content.id}")
            
        except Exception as e:
            logger.error(
                f"RecursiveTextChunkerExecutor {self.id} failed processing {content.id}",
                exc_info=True
            )
            raise
        
        return content
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get a value from a nested field path like 'pdf_output.text'."""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None
        
        return value
    
    def _measure_length(self, text: str) -> int:
        """Measure text length according to configured length_function."""
        if self.length_function == "words":
            return len(text.split())
        elif self.length_function == "tokens":
            # Approximate token count (rough estimate: ~4 chars per token)
            return len(text) // 4
        else:  # characters
            return len(text)
    
    def _split_text_recursive(
        self,
        text: str,
        separators: Optional[List[str]] = None,
        split_level: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recursively split text using hierarchy of separators.
        
        Args:
            text: Text to split
            separators: List of separators to try (uses self.separators if None)
            split_level: Current recursion level (for metadata)
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if separators is None:
            separators = self.separators
        
        # Base case: no more separators or text is small enough
        text_length = self._measure_length(text)
        
        if not separators or text_length <= self.chunk_size:
            if self.strip_whitespace:
                text = text.strip()
            
            if text:
                return [{
                    'text': text,
                    'split_level': split_level,
                    'separator_used': None,
                }]
            else:
                return []
        
        # Try current separator
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # Split by current separator
        if separator == "":
            # Character-level split (last resort)
            splits = list(text)
        else:
            splits = self._split_text_with_separator(text, separator)
        
        # Group splits into chunks
        chunks = []
        current_chunk_parts = []
        current_chunk_length = 0
        
        for split in splits:
            split_length = self._measure_length(split)
            
            # If single split is too large, recursively split it further
            if split_length > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk_parts:
                    chunk_text = self._join_parts(current_chunk_parts, separator)
                    if self.strip_whitespace:
                        chunk_text = chunk_text.strip()
                    
                    if chunk_text:
                        chunks.append({
                            'text': chunk_text,
                            'split_level': split_level,
                            'separator_used': separator,
                        })
                    
                    current_chunk_parts = []
                    current_chunk_length = 0
                
                # Recursively split the large piece
                sub_chunks = self._split_text_recursive(
                    split,
                    remaining_separators,
                    split_level + 1
                )
                chunks.extend(sub_chunks)
            
            # Check if adding this split would exceed chunk_size
            elif current_chunk_length + split_length > self.chunk_size and current_chunk_parts:
                # Save current chunk
                chunk_text = self._join_parts(current_chunk_parts, separator)
                if self.strip_whitespace:
                    chunk_text = chunk_text.strip()
                
                if chunk_text:
                    chunks.append({
                        'text': chunk_text,
                        'split_level': split_level,
                        'separator_used': separator,
                    })
                
                # Start new chunk with current split
                current_chunk_parts = [split]
                current_chunk_length = split_length
            
            else:
                # Add to current chunk
                current_chunk_parts.append(split)
                current_chunk_length += split_length
        
        # Add final chunk
        if current_chunk_parts:
            chunk_text = self._join_parts(current_chunk_parts, separator)
            if self.strip_whitespace:
                chunk_text = chunk_text.strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'split_level': split_level,
                    'separator_used': separator,
                })
        
        return chunks
    
    def _split_text_with_separator(self, text: str, separator: str) -> List[str]:
        """Split text by separator, optionally keeping the separator."""
        if separator == "":
            return list(text)
        
        if self.keep_separator:
            # Split while keeping separator with the preceding text
            splits = []
            parts = text.split(separator)
            
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    # Add separator back to all parts except the last
                    splits.append(part + separator)
                else:
                    # Last part doesn't get separator
                    if part:  # Only add if not empty
                        splits.append(part)
            
            return splits
        else:
            # Simple split without keeping separator
            return text.split(separator)
    
    def _join_parts(self, parts: List[str], separator: str) -> str:
        """Join parts back together."""
        if self.keep_separator:
            # Parts already have separators attached
            return "".join(parts)
        else:
            # Need to add separator between parts
            return separator.join(parts)
    
    def _apply_overlap(
        self,
        chunks: List[Dict[str, Any]],
        original_text: str
    ) -> List[Dict[str, Any]]:
        """Apply overlap between consecutive chunks."""
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk['text']
            
            # Add overlap from previous chunk
            if i > 0:
                prev_chunk_text = chunks[i - 1]['text']
                
                # Take last N units from previous chunk
                overlap_text = self._get_overlap_text(prev_chunk_text, self.chunk_overlap)
                
                if overlap_text:
                    chunk_text = overlap_text + chunk_text
            
            overlapped_chunk = {
                'text': chunk_text,
                'split_level': chunk.get('split_level', 0),
                'separator_used': chunk.get('separator_used'),
            }
            
            # Preserve or merge page numbers when adding overlap
            if i > 0 and 'page_numbers' in chunk:
                current_pages = chunk.get('page_numbers', [])
                prev_pages = chunks[i - 1].get('page_numbers', [])
                
                if current_pages and prev_pages:
                    # Merge page numbers from both chunks
                    all_pages = sorted(set(current_pages + prev_pages))
                    overlapped_chunk['page_numbers'] = all_pages
                elif current_pages:
                    overlapped_chunk['page_numbers'] = current_pages
                elif prev_pages:
                    overlapped_chunk['page_numbers'] = prev_pages
            elif 'page_numbers' in chunk:
                overlapped_chunk['page_numbers'] = chunk.get('page_numbers')
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from end of previous chunk."""
        text_length = self._measure_length(text)
        
        if text_length <= overlap_size:
            return text
        
        if self.length_function == "words":
            # Word-based overlap
            words = text.split()
            overlap_words = words[-overlap_size:]
            return " ".join(overlap_words) + " "
        
        elif self.length_function == "tokens":
            # Approximate token-based overlap (chars * 4)
            char_overlap = overlap_size * 4
            overlap_text = text[-char_overlap:]
            
            # Try to start at word boundary
            space_pos = overlap_text.find(' ')
            if space_pos > 0:
                overlap_text = overlap_text[space_pos + 1:]
            
            return overlap_text + " "
        
        else:  # characters
            # Character-based overlap
            overlap_text = text[-overlap_size:]
            
            # Try to start at word boundary
            space_pos = overlap_text.find(' ')
            if space_pos > 0:
                overlap_text = overlap_text[space_pos + 1:]
            
            return overlap_text + " "
    
    def _merge_small_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge chunks that are below minimum size."""
        if not chunks or self.min_chunk_size <= 0:
            return chunks
        
        merged_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            current_text = current_chunk['text']
            current_length = self._measure_length(current_text)
            
            # Check if chunk is too small and not the last chunk
            if current_length < self.min_chunk_size and i < len(chunks) - 1:
                # Merge with next chunk
                next_chunk = chunks[i + 1]
                merged_text = current_text + next_chunk['text']
                
                merged_chunk = {
                    'text': merged_text,
                    'split_level': min(
                        current_chunk.get('split_level', 0),
                        next_chunk.get('split_level', 0)
                    ),
                    'separator_used': current_chunk.get('separator_used'),
                }
                
                # Merge page numbers if present
                if 'page_numbers' in current_chunk or 'page_numbers' in next_chunk:
                    current_pages = current_chunk.get('page_numbers', [])
                    next_pages = next_chunk.get('page_numbers', [])
                    if current_pages or next_pages:
                        merged_chunk['page_numbers'] = sorted(set(current_pages + next_pages))
                
                merged_chunks.append(merged_chunk)
                i += 2  # Skip next chunk as it's merged
            else:
                merged_chunks.append(current_chunk)
                i += 1
        
        return merged_chunks
    
    def _extract_pages_data(self, data: Dict[str, Any], input_field: str) -> Optional[List[Dict[str, Any]]]:
        """Extract page data from extractor output if available."""
        # Try to get pages data from various extractor formats
        field_parts = input_field.split('.')
        
        if len(field_parts) > 1:
            # Nested field like "pdf_output.text"
            base_field = field_parts[0]
            base_data = data.get(base_field)
            
            if isinstance(base_data, dict):
                # Check for pages array in extractor output
                pages = base_data.get('pages')
                if isinstance(pages, list) and pages:
                    return pages
        
        # Also check top-level pages field
        pages = data.get('pages')
        if isinstance(pages, list) and pages:
            return pages
        
        return None
    
    def _add_page_numbers_to_chunks(
        self,
        chunks: List[Dict[str, Any]],
        full_text: str,
        pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add page numbers to chunks based on their position in the full text."""
        if not chunks or not pages_data:
            return chunks
        
        # Build a map of character positions to page numbers
        char_to_page = self._build_char_to_page_map(full_text, pages_data)
        
        for chunk in chunks:
            chunk_text = chunk.get('text', '')
            if not chunk_text:
                continue
            
            # Find chunk position in full text
            page_nums = self._get_page_numbers_for_text(chunk_text, full_text, char_to_page, pages_data)
            
            if page_nums:
                chunk['page_numbers'] = page_nums
        
        return chunks
    
    def _build_char_to_page_map(
        self,
        full_text: str,
        pages_data: List[Dict[str, Any]]
    ) -> Dict[int, int]:
        """Build a mapping of character positions to page numbers."""
        char_to_page = {}
        current_pos = 0
        
        for page in pages_data:
            page_text = page.get('text', '')
            page_num = page.get('page_number', 0)
            
            if not page_text or not page_num:
                continue
            
            # Find page text in full text
            page_start = full_text.find(page_text, current_pos)
            
            if page_start != -1:
                page_end = page_start + len(page_text)
                
                # Map each character position in this page to the page number
                for pos in range(page_start, page_end):
                    char_to_page[pos] = page_num
                
                current_pos = page_end
            else:
                # If exact match fails, try fuzzy matching with first 100 chars
                if len(page_text) > 100:
                    fingerprint = page_text[:100]
                    page_start = full_text.find(fingerprint, current_pos)
                    
                    if page_start != -1:
                        page_end = page_start + len(page_text)
                        for pos in range(page_start, page_end):
                            char_to_page[pos] = page_num
                        current_pos = page_end
        
        return char_to_page
    
    def _get_page_numbers_for_text(
        self,
        chunk_text: str,
        full_text: str,
        char_to_page: Dict[int, int],
        pages_data: List[Dict[str, Any]]
    ) -> List[int]:
        """Determine which pages a chunk appears on."""
        page_numbers = set()
        
        if not chunk_text:
            return []
        
        # Clean chunk text for better matching
        chunk_text_clean = chunk_text.strip()
        if not chunk_text_clean:
            return []
        
        # Try to find chunk in full text
        chunk_start = full_text.find(chunk_text_clean)
        
        # If exact match fails, try with first 200 chars as a fingerprint
        if chunk_start == -1 and len(chunk_text_clean) > 200:
            fingerprint = chunk_text_clean[:200]
            chunk_start = full_text.find(fingerprint)
        
        if chunk_start != -1:
            chunk_end = chunk_start + len(chunk_text_clean)
            
            # Get page numbers from character positions
            for pos in range(chunk_start, min(chunk_end, len(full_text))):
                if pos in char_to_page:
                    page_numbers.add(char_to_page[pos])
            
            if page_numbers:
                return sorted(page_numbers)
        
        # Fallback: check which pages contain parts of the chunk text
        if not page_numbers:
            # Extract first and last few words as markers
            words = chunk_text_clean.split()
            if len(words) >= 5:
                first_words = ' '.join(words[:5])
                last_words = ' '.join(words[-5:])
                
                for page in pages_data:
                    page_text = page.get('text', '')
                    page_num = page.get('page_number', 0)
                    
                    # Check if any significant portion appears in this page
                    if first_words in page_text or last_words in page_text:
                        if page_num:
                            page_numbers.add(page_num)
        
        # Last resort: assign to first page if available
        if not page_numbers and pages_data:
            first_page_num = pages_data[0].get('page_number', 1)
            if first_page_num:
                page_numbers.add(first_page_num)
        
        return sorted(page_numbers)
