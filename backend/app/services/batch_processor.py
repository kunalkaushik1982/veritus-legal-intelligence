"""
Batch PDF processing service for handling large volumes of judgments
File: backend/app/services/batch_processor.py
"""

import asyncio
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import aiofiles

from app.services.pdf_processor import PDFProcessor
# from app.models.judgment import Judgment
# from app.database import get_db
# from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Service for batch processing large volumes of PDF judgments"""
    
    def __init__(self, max_workers: int = 4):
        self.pdf_processor = PDFProcessor()
        self.max_workers = max_workers
        self.processed_count = 0
        self.failed_count = 0
        self.total_count = 0
        
    async def process_pdf_directory(
        self, 
        pdf_directory: str,
        batch_size: int = 100,
        start_from: int = 0,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process all PDFs in a directory in batches
        
        Args:
            pdf_directory: Path to directory containing PDF files
            batch_size: Number of PDFs to process in each batch
            start_from: Index to start processing from
            limit: Maximum number of PDFs to process (None for all)
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Get list of PDF files
            pdf_files = self._get_pdf_files(pdf_directory)
            
            if not pdf_files:
                return {
                    "success": False,
                    "error": f"No PDF files found in {pdf_directory}",
                    "processed": 0,
                    "failed": 0,
                    "total": 0
                }
            
            # Apply limits
            if start_from > 0:
                pdf_files = pdf_files[start_from:]
            
            if limit:
                pdf_files = pdf_files[:limit]
            
            self.total_count = len(pdf_files)
            logger.info(f"Starting batch processing of {self.total_count} PDF files")
            
            # Process in batches
            results = []
            for i in range(0, len(pdf_files), batch_size):
                batch = pdf_files[i:i + batch_size]
                batch_results = await self._process_batch(batch, i)
                results.extend(batch_results)
                
                # Log progress
                self._log_progress(i + len(batch))
            
            return {
                "success": True,
                "processed": self.processed_count,
                "failed": self.failed_count,
                "total": self.total_count,
                "results": results,
                "processing_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed": self.processed_count,
                "failed": self.failed_count,
                "total": self.total_count
            }
    
    def _get_pdf_files(self, directory: str) -> List[str]:
        """Get list of PDF files in directory"""
        try:
            pdf_dir = Path(directory)
            if not pdf_dir.exists():
                logger.error(f"Directory {directory} does not exist")
                return []
            
            pdf_files = []
            for file_path in pdf_dir.glob("*.pdf"):
                if file_path.is_file():
                    pdf_files.append(str(file_path))
            
            # Sort files for consistent processing order
            pdf_files.sort()
            logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error getting PDF files from {directory}: {str(e)}")
            return []
    
    async def _process_batch(self, pdf_files: List[str], batch_index: int) -> List[Dict[str, Any]]:
        """Process a batch of PDF files concurrently"""
        try:
            logger.info(f"Processing batch {batch_index // 100 + 1}: {len(pdf_files)} files")
            
            # Create tasks for concurrent processing
            tasks = []
            for pdf_file in pdf_files:
                task = self._process_single_pdf(pdf_file)
                tasks.append(task)
            
            # Process batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {pdf_files[i]}: {str(result)}")
                    self.failed_count += 1
                    processed_results.append({
                        "file": pdf_files[i],
                        "success": False,
                        "error": str(result)
                    })
                else:
                    if result.get("success", False):
                        self.processed_count += 1
                    else:
                        self.failed_count += 1
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return []
    
    async def _process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF file"""
        try:
            # Extract filename without extension for case number
            filename = Path(pdf_path).stem
            
            # Process PDF without database for now
            result = await self.pdf_processor.process_judgment_pdf(
                pdf_path, 
                1  # Dummy ID for now
            )
            
            if result.get("success", False):
                extracted_data = result.get("extracted_data", {})
                
                return {
                    "file": pdf_path,
                    "success": True,
                    "case_number": filename,
                    "case_title": extracted_data.get("case_title", f"Case {filename}"),
                    "text_length": result.get("text_length", 0),
                    "page_count": extracted_data.get("page_count", 0),
                    "judges": extracted_data.get("judges", []),
                    "statutes_cited": extracted_data.get("statutes_cited", [])
                }
            else:
                return {
                    "file": pdf_path,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return {
                "file": pdf_path,
                "success": False,
                "error": str(e)
            }
    
    def _log_progress(self, processed: int):
        """Log processing progress"""
        percentage = (processed / self.total_count) * 100 if self.total_count > 0 else 0
        logger.info(
            f"Progress: {processed}/{self.total_count} ({percentage:.1f}%) - "
            f"Processed: {self.processed_count}, Failed: {self.failed_count}"
        )
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        try:
            # Simplified status for now
            return {
                "total_judgments": 0,
                "processed_judgments": 0,
                "failed_judgments": 0,
                "pending_judgments": 0,
                "processing_percentage": 0
            }
                
        except Exception as e:
            logger.error(f"Error getting processing status: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def resume_processing(
        self, 
        pdf_directory: str,
        batch_size: int = 100,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Resume processing from where it left off"""
        try:
            # Get current status
            status = await self.get_processing_status()
            start_from = status.get("processed_judgments", 0)
            
            logger.info(f"Resuming processing from judgment {start_from}")
            
            return await self.process_pdf_directory(
                pdf_directory=pdf_directory,
                batch_size=batch_size,
                start_from=start_from,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error resuming processing: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
