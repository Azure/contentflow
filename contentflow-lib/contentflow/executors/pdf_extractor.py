"""PDF extraction executor using PyMuPDF for text, pages, and images."""

import base64
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import pymupdf  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF is required for PDF extraction. "
        "Install it with: pip install pymupdf"
    )

from . import ParallelExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.pdf_extractor")


class PDFExtractorExecutor(ParallelExecutor):
    """
    Extract content from PDF documents using PyMuPDF.
    
    This executor analyzes PDF documents to extract text, page-level chunks,
    and embedded images using the PyMuPDF library.
    
    Configuration (settings dict):
        - extract_text (bool): Extract text content from PDF
          Default: True
        - extract_pages (bool): Create page-level text chunks
          Default: True
        - extract_images (bool): Extract embedded images from PDF
          Default: False
        - content_field (str): Field containing PDF bytes
          Default: "content"
        - temp_file_path_field (str): Field containing temp file path
          Default: "temp_file_path"
        - output_field (str): Field name for extracted data
          Default: "pdf_output"
        - image_format (str): Format for extracted images
          Default: "png"
          Options: "png", "jpeg", "jpg"
        - image_output_mode (str): How to store extracted images
          Default: "base64"
          Options: "base64", "bytes"
        - min_image_size (int): Minimum image size in pixels (width or height)
          Default: 100
        - page_separator (str): Separator between pages in full text
          Default: "\n\n---\n\n"

        Also setting from ParallelExecutor and BaseExecutor apply.
        
    Example:
        ```python
        executor = PDFExtractorExecutor(
            id="pdf_extractor",
            settings={
                "extract_text": True,
                "extract_pages": True,
                "extract_images": True,
                "image_format": "png",
                "min_image_size": 100,
            }
        )
        ```
    
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - data['content']: PDF document bytes, OR
        - data['temp_file_path']: Path to PDF file
        
    Output:
        Document or List[Document] with added fields:
        - data['pdf_output']['text']: Full extracted text
        - data['pdf_output']['pages']: List of page chunks with text and metadata
        - data['pdf_output']['images']: List of extracted images (if enabled)
        - summary_data['pages_processed']: Number of pages processed
        - summary_data['images_extracted']: Number of images extracted
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
        
        # Extract configuration
        self.extract_text = self.get_setting("extract_text", default=True)
        self.extract_pages = self.get_setting("extract_pages", default=True)
        self.extract_images = self.get_setting("extract_images", default=False)
        self.content_field = self.get_setting("content_field", default=None)
        self.temp_file_field = self.get_setting("temp_file_path_field", default="temp_file_path")
        self.output_field = self.get_setting("output_field", default="pdf_output")
        self.image_format = self.get_setting("image_format", default="png")
        self.image_output_mode = self.get_setting("image_output_mode", default="base64")
        self.min_image_size = self.get_setting("min_image_size", default=100)
        self.page_separator = self.get_setting("page_separator", default="\n\n---\n\n")
        
        # Validate image format
        if self.image_format.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Invalid image_format: {self.image_format}. Must be 'png', 'jpeg', or 'jpg'")
        
        # Validate image output mode
        if self.image_output_mode not in ["base64", "bytes"]:
            raise ValueError(f"Invalid image_output_mode: {self.image_output_mode}. Must be 'base64' or 'bytes'")
        
        if self.debug_mode:
            logger.debug(
                f"PDFExtractorExecutor with id {self.id} initialized: "
                f"text={self.extract_text}, pages={self.extract_pages}, "
                f"images={self.extract_images}, format={self.image_format}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single PDF document using PyMuPDF.
           Implements the abstract method from ParallelExecutor.
        """
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Get PDF content
            pdf_bytes = None
            pdf_path = None
            
            # Try to get from content field
            if self.content_field in content.data:
                pdf_bytes = content.data[self.content_field]
            
            # Try to get from temp file
            elif self.temp_file_field in content.data:
                pdf_path = content.data[self.temp_file_field]
            
            if not pdf_bytes and not pdf_path:
                raise ValueError(
                    f"PDF missing required content. "
                    f"Needs either '{self.content_field}' or '{self.temp_file_field}'"
                )
            
            if self.debug_mode:
                source = f"file: {pdf_path}" if pdf_path else f"bytes: {len(pdf_bytes)} bytes"
                logger.debug(f"Processing PDF {content.id} from {source}")
            
            # Open PDF document
            if pdf_bytes:
                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            else:
                doc = pymupdf.open(filename=pdf_path)
            
            try:
                extracted_data = {}
                page_count = len(doc)
                
                # Extract text
                all_text = []
                pages_data = []
                
                for page_num in range(page_count):
                    page = doc[page_num]
                    page_text = page.get_text()
                    
                    if self.extract_text:
                        all_text.append(page_text)
                    
                    if self.extract_pages:
                        page_info = {
                            "page_number": page_num + 1,
                            "width": page.rect.width,
                            "height": page.rect.height,
                            "text": page_text,
                            "char_count": len(page_text)
                        }
                        pages_data.append(page_info)
                
                if self.extract_text:
                    extracted_data['text'] = self.page_separator.join(all_text)
                    if self.debug_mode:
                        logger.debug(f"Extracted {len(extracted_data['text'])} characters of text")
                
                if self.extract_pages:
                    extracted_data['pages'] = pages_data
                    if self.debug_mode:
                        logger.debug(f"Created {len(pages_data)} page chunks")
                
                # Extract images
                if self.extract_images:
                    images = self._extract_images_from_pdf(doc)
                    extracted_data['images'] = images
                    if self.debug_mode:
                        logger.debug(f"Extracted {len(images)} images")
                else:
                    images = []
                
                # Store extracted data
                content.data[self.output_field] = extracted_data
                
                # Update summary
                content.summary_data['pages_processed'] = page_count
                content.summary_data['images_extracted'] = len(images) if self.extract_images else 0
                content.summary_data['extraction_status'] = "success"
                
            finally:
                doc.close()
                            
        except Exception as e:
            logger.error(
                f"PDFExtractorExecutor {self.id} failed processing PDF {content.id}",
                exc_info=True
            )
            
            # Raise the exception to be handled upstream if needed
            raise
        
        return content
    
    def _extract_images_from_pdf(self, doc: pymupdf.Document) -> List[Dict[str, Any]]:
        """Extract images from PDF document.
        
        Args:
            doc: Opened PyMuPDF document
            
        Returns:
            List of image dictionaries with metadata and image data
        """
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    
                    # Extract image
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Get image dimensions
                    pix = pymupdf.Pixmap(doc, xref)
                    width = pix.width
                    height = pix.height
                    
                    # Filter by minimum size
                    if width < self.min_image_size and height < self.min_image_size:
                        if self.debug_mode:
                            logger.debug(
                                f"Skipping small image on page {page_num + 1}: "
                                f"{width}x{height} (min: {self.min_image_size})"
                            )
                        continue
                    
                    # Convert to desired format if needed
                    if self.image_format.lower() in ["png", "jpeg", "jpg"]:
                        target_format = "png" if self.image_format.lower() == "png" else "jpeg"
                        
                        if image_ext != target_format:
                            # Convert image format
                            pix = pymupdf.Pixmap(pymupdf.Pixmap(doc, xref), 0)  # Remove alpha if present
                            if target_format == "png":
                                image_bytes = pix.tobytes("png")
                            else:
                                image_bytes = pix.tobytes("jpeg")
                        
                        pix = None  # Clean up
                    
                    # Prepare image data based on output mode
                    if self.image_output_mode == "base64":
                        image_data = base64.b64encode(image_bytes).decode('utf-8')
                    else:
                        image_data = image_bytes
                    
                    image_info = {
                        "page_number": page_num + 1,
                        "image_index": img_index,
                        "width": width,
                        "height": height,
                        "format": self.image_format,
                        "data": image_data,
                        "encoding": self.image_output_mode
                    }
                    
                    images.append(image_info)
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} from page {page_num + 1}: {e}"
                    )
                    continue
        
        return images
