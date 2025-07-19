import os
import uuid
import aiofiles
from typing import List, Dict, Any
import fitz  # PyMuPDF
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image
import io
import base64
import logging

from config import settings
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
        self.vector_store = VectorStore()

    async def save_uploaded_file(self, file: UploadFile) -> tuple[str, str]:
        """Save uploaded PDF file to disk and return both file path and original filename"""
        try:
            # Ensure uploads directory exists
            os.makedirs(settings.upload_dir, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_dir, unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Verify file was saved
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"Successfully saved uploaded file: {file_path} (size: {file_size} bytes)")
            else:
                logger.error(f"File was not saved: {file_path}")
                raise Exception(f"Failed to save file to {file_path}")
            
            return file_path, file.filename  # Return both paths
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise

    def extract_text_and_images_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text and images from PDF with page numbers"""
        try:
            doc = fitz.open(file_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                text = page.get_text()
                
                # Extract images
                images = []
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Convert to PIL Image
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                            # Convert to base64 for storage
                            buffered = io.BytesIO()
                            pil_image.save(buffered, format="PNG")
                            img_base64 = base64.b64encode(buffered.getvalue()).decode()
                            
                            images.append({
                                "index": img_index,
                                "data": img_base64,
                                "format": "png"
                            })
                        
                        pix = None  # Release memory
                        
                    except Exception as img_error:
                        logger.warning(f"Could not extract image {img_index} from page {page_num}: {img_error}")
                        continue
                
                # Extract table data if any (basic implementation)
                tables = self.extract_tables_from_page(page)
                
                pages_data.append({
                    "page_number": page_num + 1,  # 1-indexed
                    "text": text,
                    "images": images,
                    "tables": tables,
                    "has_content": bool(text.strip() or images or tables)
                })
            
            doc.close()
            logger.info(f"Extracted data from {len(pages_data)} pages")
            return pages_data
            
        except Exception as e:
            logger.error(f"Failed to extract data from PDF: {e}")
            raise

    def extract_tables_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract table data from a page (basic implementation)"""
        try:
            tables = page.find_tables()
            table_data = []
            
            for table_index, table in enumerate(tables):
                try:
                    # Extract table as pandas DataFrame if possible
                    df = table.to_pandas()
                    
                    # Convert to dict format
                    table_dict = {
                        "index": table_index,
                        "data": df.to_dict('records') if not df.empty else [],
                        "headers": df.columns.tolist() if not df.empty else [],
                        "rows": len(df) if not df.empty else 0,
                        "cols": len(df.columns) if not df.empty else 0
                    }
                    
                    table_data.append(table_dict)
                    
                except Exception as table_error:
                    logger.warning(f"Could not extract table {table_index}: {table_error}")
                    continue
            
            return table_data
            
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
            return []

    def create_chunks_from_pages(self, pages_data: List[Dict[str, Any]], filename: str, original_filename: str) -> List[Dict[str, Any]]:
        """Create chunks from page data with metadata"""
        try:
            chunks = []
            
            for page_data in pages_data:
                page_num = page_data["page_number"]
                text = page_data["text"]
                images = page_data["images"]
                tables = page_data["tables"]
                
                if not page_data["has_content"]:
                    continue
                
                # Create text chunks
                if text.strip():
                    text_chunks = self.text_splitter.split_text(text)
                    
                    for chunk_index, chunk_text in enumerate(text_chunks):
                        # Try to extract section title from chunk
                        section_title = self.extract_section_title(chunk_text)
                        
                        chunk = {
                            "content": chunk_text,
                            "page_number": page_num,
                            "chunk_type": "text",
                            "chunk_index": chunk_index,
                            "section_title": section_title,
                            "filename": filename,  # UUID filename for storage
                            "original_filename": original_filename,  # Original filename for display
                            "has_images": len(images) > 0,
                            "has_tables": len(tables) > 0,
                            "image_count": len(images),
                            "table_count": len(tables)
                        }
                        chunks.append(chunk)
                
                # Create image-based chunks (if images contain important data)
                for img_index, image in enumerate(images):
                    # Create a descriptive chunk for the image
                    image_content = f"Image {img_index + 1} on page {page_num}"
                    
                    # If there's surrounding text, include it for context
                    context_text = text[:200] if text else ""
                    if context_text:
                        image_content += f"\nContext: {context_text}"
                    
                    chunk = {
                        "content": image_content,
                        "page_number": page_num,
                        "chunk_type": "image",
                        "chunk_index": img_index,
                        "section_title": "",
                        "filename": filename,
                        "original_filename": original_filename,
                        "image_data": image["data"],
                        "has_images": True,
                        "has_tables": len(tables) > 0,
                        "image_count": 1,
                        "table_count": len(tables)
                    }
                    chunks.append(chunk)
                
                # Create table-based chunks
                for table_index, table in enumerate(tables):
                    if table["data"]:
                        # Create a text representation of the table
                        table_content = f"Table {table_index + 1} on page {page_num}\n"
                        table_content += f"Headers: {', '.join(table['headers'])}\n"
                        
                        # Add first few rows as sample
                        for i, row in enumerate(table["data"][:3]):  # First 3 rows
                            row_text = ", ".join([f"{k}: {v}" for k, v in row.items()])
                            table_content += f"Row {i+1}: {row_text}\n"
                        
                        if len(table["data"]) > 3:
                            table_content += f"... and {len(table['data']) - 3} more rows"
                        
                        chunk = {
                            "content": table_content,
                            "page_number": page_num,
                            "chunk_type": "table",
                            "chunk_index": table_index,
                            "section_title": "",
                            "filename": filename,
                            "original_filename": original_filename,
                            "table_data": table["data"],
                            "has_images": len(images) > 0,
                            "has_tables": True,
                            "image_count": len(images),
                            "table_count": 1
                        }
                        chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {len(pages_data)} pages")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}")
            raise

    def extract_section_title(self, text: str) -> str:
        """Extract section title from chunk text (simple heuristic)"""
        try:
            lines = text.split('\n')
            for line in lines[:3]:  # Check first 3 lines
                line = line.strip()
                # Simple heuristics for section titles
                if (len(line) < 100 and 
                    (line.isupper() or 
                     line.istitle() or 
                     any(line.startswith(prefix) for prefix in ['Chapter', 'Section', '##', '#']))):
                    return line
            return ""
        except:
            return ""

    async def process_pdf(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Process PDF file: extract text, images, and tables, then store in vector database"""
        try:
            # Extract filename
            filename = os.path.basename(file_path)
            document_id = str(uuid.uuid4())
            
            # Extract text and images from PDF
            pages_data = self.extract_text_and_images_from_pdf(file_path)
            
            # Create chunks with both filenames
            chunks = self.create_chunks_from_pages(pages_data, filename, original_filename)
            
            if not chunks:
                raise ValueError("No content could be extracted from the PDF")
            
            # Store in vector database with the UUID filename for file retrieval
            await self.vector_store.store_document_chunks(
                chunks=chunks,
                document_id=document_id,
                filename=filename  # Use UUID filename for storage path
            )
            
            # Keep the original file for viewing
            # os.remove(file_path)
            
            return {
                "document_id": document_id,
                "filename": original_filename,  # Return original filename to user
                "pages_processed": len(pages_data),
                "chunks_created": len(chunks),
                "text_chunks": len([c for c in chunks if c["chunk_type"] == "text"]),
                "image_chunks": len([c for c in chunks if c["chunk_type"] == "image"]),
                "table_chunks": len([c for c in chunks if c["chunk_type"] == "table"])
            }
            
        except Exception as e:
            # Clean up file on error, but not on success
            if os.path.exists(file_path):
                logger.warning(f"Process failed for {file_path}. File will be removed.")
                # os.remove(file_path) 
            logger.error(f"Failed to process PDF: {e}")
            raise

    async def generate_page_image(self, file_path: str, page_number: int) -> bytes:
        """Generate a JPG image of a specific page from a PDF"""
        try:
            doc = fitz.open(file_path)
            
            # Convert to 0-based indexing
            page_index = page_number - 1
            
            if page_index < 0 or page_index >= len(doc):
                logger.error(f"Page {page_number} does not exist in document (total pages: {len(doc)})")
                doc.close()
                return None
            
            # Load the page
            page = doc.load_page(page_index)
            
            # Create a transformation matrix for high-quality rendering
            # Scale factor for better quality (2.0 means 2x resolution)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if necessary (remove alpha channel)
            if pil_image.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', pil_image.size, (255, 255, 255))
                background.paste(pil_image, mask=pil_image.split()[-1])  # Use alpha channel as mask
                pil_image = background
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Save as JPEG
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_bytes = img_buffer.getvalue()
            
            # Clean up
            pix = None
            doc.close()
            
            logger.info(f"Generated page image for page {page_number}: {len(img_bytes)} bytes")
            return img_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate page image for page {page_number}: {e}")
            return None

    def health_check(self) -> bool:
        """Check if the PDF processor is healthy"""
        try:
            # Test if PyMuPDF is working
            test_doc = fitz.open()
            test_doc.close()
            return True
        except:
            return False 