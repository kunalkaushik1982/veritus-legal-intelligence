"""
Test script for PDF processing functionality
File: backend/test_pdf_processing.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.batch_processor import BatchProcessor
from app.services.pdf_processor import PDFProcessor


async def test_single_pdf():
    """Test processing a single PDF file"""
    print("Testing single PDF processing...")
    
    pdf_processor = PDFProcessor()
    
    # Test with one of the sample PDFs
    pdf_path = "../pdfs/1146.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    try:
        result = await pdf_processor.process_judgment_pdf(pdf_path, 1)
        
        if result.get("success"):
            print("✅ PDF processing successful!")
            print(f"Text length: {result.get('text_length', 0)} characters")
            print(f"Page count: {result.get('page_count', 0)}")
            
            extracted_data = result.get("extracted_data", {})
            print(f"Case number: {extracted_data.get('case_number', 'N/A')}")
            print(f"Case title: {extracted_data.get('case_title', 'N/A')}")
            print(f"Judges: {extracted_data.get('judges', [])}")
            print(f"Statutes cited: {extracted_data.get('statutes_cited', [])}")
            print(f"Key phrases: {extracted_data.get('key_phrases', [])[:3]}...")  # Show first 3
            
        else:
            print(f"❌ PDF processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing PDF processing: {str(e)}")


async def test_batch_processing():
    """Test batch processing with a small number of PDFs"""
    print("\nTesting batch processing...")
    
    batch_processor = BatchProcessor(max_workers=2)
    
    # Test with the pdfs directory
    pdf_directory = "../pdfs"
    
    if not os.path.exists(pdf_directory):
        print(f"PDF directory not found: {pdf_directory}")
        return
    
    try:
        # Process only 3 PDFs for testing
        result = await batch_processor.process_pdf_directory(
            pdf_directory=pdf_directory,
            batch_size=2,
            start_from=0,
            limit=3
        )
        
        if result.get("success"):
            print("✅ Batch processing successful!")
            print(f"Processed: {result.get('processed', 0)}")
            print(f"Failed: {result.get('failed', 0)}")
            print(f"Total: {result.get('total', 0)}")
            
            # Show some results
            results = result.get("results", [])
            for i, res in enumerate(results[:2]):  # Show first 2 results
                if res.get("success"):
                    print(f"  {i+1}. {res.get('case_number', 'N/A')}: {res.get('case_title', 'N/A')}")
                else:
                    print(f"  {i+1}. Failed: {res.get('error', 'Unknown error')}")
                    
        else:
            print(f"❌ Batch processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing batch processing: {str(e)}")


async def main():
    """Main test function"""
    print("🚀 Starting PDF processing tests...\n")
    
    # Test single PDF processing
    await test_single_pdf()
    
    # Test batch processing
    await test_batch_processing()
    
    print("\n✅ Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
