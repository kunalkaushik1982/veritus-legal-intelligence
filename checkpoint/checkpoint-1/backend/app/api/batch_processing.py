"""
API endpoints for batch PDF processing
File: backend/app/api/batch_processing.py
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime

from app.services.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/batch", tags=["batch-processing"])

# Global batch processor instance
batch_processor = BatchProcessor(max_workers=4)


class BatchProcessingRequest(BaseModel):
    pdf_directory: str
    batch_size: int = 100
    start_from: int = 0
    limit: Optional[int] = None


class BatchProcessingResponse(BaseModel):
    success: bool
    message: str
    processed: int
    failed: int
    total: int
    processing_time: Optional[str] = None
    error: Optional[str] = None


@router.post("/start", response_model=BatchProcessingResponse)
async def start_batch_processing(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch processing of PDF judgments
    
    Args:
        request: Batch processing configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Processing status and results
    """
    try:
        logger.info(f"Starting batch processing for directory: {request.pdf_directory}")
        
        # Start processing in background
        background_tasks.add_task(
            _process_pdfs_background,
            request.pdf_directory,
            request.batch_size,
            request.start_from,
            request.limit
        )
        
        return BatchProcessingResponse(
            success=True,
            message="Batch processing started successfully",
            processed=0,
            failed=0,
            total=0
        )
        
    except Exception as e:
        logger.error(f"Error starting batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def get_processing_status():
    """
    Get current batch processing status
    
    Returns:
        Current processing statistics
    """
    try:
        status = await batch_processor.get_processing_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=BatchProcessingResponse)
async def resume_processing(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Resume batch processing from where it left off
    
    Args:
        request: Batch processing configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Processing status and results
    """
    try:
        logger.info(f"Resuming batch processing for directory: {request.pdf_directory}")
        
        # Start processing in background
        background_tasks.add_task(
            _resume_processing_background,
            request.pdf_directory,
            request.batch_size,
            request.limit
        )
        
        return BatchProcessingResponse(
            success=True,
            message="Batch processing resumed successfully",
            processed=0,
            failed=0,
            total=0
        )
        
    except Exception as e:
        logger.error(f"Error resuming batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=Dict[str, Any])
async def test_processing(request: BatchProcessingRequest):
    """
    Test processing with a small number of PDFs
    
    Args:
        request: Batch processing configuration
        
    Returns:
        Test processing results
    """
    try:
        logger.info(f"Testing processing with {request.limit} PDFs from {request.pdf_directory}")
        
        result = await batch_processor.process_pdf_directory(
            pdf_directory=request.pdf_directory,
            batch_size=5,
            start_from=0,
            limit=request.limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in test processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-existing", response_model=Dict[str, Any])
async def process_existing_pdfs():
    """
    Process all existing PDFs in the pdfs directory
    
    Returns:
        Processing results with counts and details
    """
    try:
        logger.info("Starting to process existing PDFs in pdfs directory")
        
        # Use the existing PDFs directory
        pdf_directory = "pdfs"
        
        # Check if directory exists
        from pathlib import Path
        pdfs_path = Path(pdf_directory)
        if not pdfs_path.exists():
            return {
                "success": False,
                "error": f"Directory '{pdf_directory}' not found",
                "total": 0,
                "processed": 0,
                "failed": 0,
                "results": []
            }
        
        # Get list of PDF files
        pdf_files = list(pdfs_path.glob("*.pdf"))
        total_pdfs = len(pdf_files)
        
        if total_pdfs == 0:
            return {
                "success": True,
                "message": "No PDF files found in pdfs directory",
                "total": 0,
                "processed": 0,
                "failed": 0,
                "results": []
            }
        
        logger.info(f"Found {total_pdfs} PDF files to process")
        
        # Process each PDF
        processed_count = 0
        failed_count = 0
        results = []
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                logger.info(f"Processing {pdf_file.name} ({i+1}/{total_pdfs})")
                
                # Use the existing PDF processor
                from app.services.pdf_processor import PDFProcessor
                from app.services.pdf_metadata_extractor import PDFMetadataExtractor
                from app.services.judgment_storage import JudgmentMetadataStorage
                
                pdf_processor = PDFProcessor()
                metadata_extractor = PDFMetadataExtractor()
                judgment_storage = JudgmentMetadataStorage()
                
                # Process the PDF
                processing_result = await pdf_processor.process_judgment_pdf(str(pdf_file), i + 1)
                
                if processing_result.get("success"):
                    # Extract metadata
                    full_text = processing_result.get("full_text", "")
                    extracted_metadata = metadata_extractor.extract_metadata(full_text, pdf_file.name)
                    
                    # Store the judgment
                    judgment_data = {
                        "id": i + 1,
                        "filename": pdf_file.name,
                        "file_path": str(pdf_file),
                        "file_size": pdf_file.stat().st_size,
                        "processed_date": datetime.now().isoformat(),
                        "is_processed": True,
                        "extraction_status": "success",
                        **extracted_metadata
                    }
                    
                    # Store in judgment storage
                    judgment_storage.save_judgment_metadata(i + 1, judgment_data)
                    
                    results.append(judgment_data)
                    processed_count += 1
                    logger.info(f"Successfully processed {pdf_file.name}")
                    
                else:
                    error_msg = processing_result.get("error", "Unknown error")
                    results.append({
                        "id": i + 1,
                        "filename": pdf_file.name,
                        "file_path": str(pdf_file),
                        "is_processed": False,
                        "extraction_status": "failed",
                        "error": error_msg
                    })
                    failed_count += 1
                    logger.error(f"Failed to process {pdf_file.name}: {error_msg}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {str(e)}")
                results.append({
                    "id": i + 1,
                    "filename": pdf_file.name,
                    "file_path": str(pdf_file),
                    "is_processed": False,
                    "extraction_status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        # Save results to JSON file for persistence
        output_data = {
            "total_processed": processed_count,
            "total_found": total_pdfs,
            "processing_date": datetime.now().isoformat(),
            "judgments": results
        }
        
        # Create judgment_metadata directory if it doesn't exist
        judgment_metadata_dir = Path("judgment_metadata")
        judgment_metadata_dir.mkdir(exist_ok=True)
        
        # Save to both files for compatibility
        with open("processed_judgments.json", 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Also save to judgment_metadata/judgments.json for the storage service
        judgment_metadata_file = judgment_metadata_dir / "judgments.json"
        metadata_storage_data = {
            "judgments": results,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        with open(judgment_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_storage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing completed: {processed_count} processed, {failed_count} failed")
        
        return {
            "success": True,
            "message": f"Processed {processed_count} of {total_pdfs} PDFs successfully",
            "total": total_pdfs,
            "processed": processed_count,
            "failed": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing existing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_pdfs_background(
    pdf_directory: str,
    batch_size: int,
    start_from: int,
    limit: Optional[int]
):
    """Background task for processing PDFs"""
    try:
        result = await batch_processor.process_pdf_directory(
            pdf_directory=pdf_directory,
            batch_size=batch_size,
            start_from=start_from,
            limit=limit
        )
        
        logger.info(f"Background processing completed: {result}")
        
    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")


async def _resume_processing_background(
    pdf_directory: str,
    batch_size: int,
    limit: Optional[int]
):
    """Background task for resuming processing"""
    try:
        result = await batch_processor.resume_processing(
            pdf_directory=pdf_directory,
            batch_size=batch_size,
            limit=limit
        )
        
        logger.info(f"Background resume processing completed: {result}")
        
    except Exception as e:
        logger.error(f"Error in background resume processing: {str(e)}")
