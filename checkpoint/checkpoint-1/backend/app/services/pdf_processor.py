"""
PDF processing service for judgment text extraction
File: backend/app/services/pdf_processor.py
"""

import PyPDF2
import re
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF judgments and extracting structured data"""
    
    def __init__(self):
        # Common patterns for legal document structure
        self.case_number_pattern = r"(?:Civil|Criminal|Writ|Special Leave|Appeal)\s+(?:Appeal|Petition|Application)?\s*(?:No\.?\s*)?(\d+[A-Z]?/\d{4})"
        self.date_pattern = r"(\d{1,2}[-\/]\d{1,2}[-\/]\d{4}|\d{4})"
        self.judge_pattern = r"(?:Hon'ble|Honourable)\s+(?:Mr\.?\s*Justice|Ms\.?\s*Justice|Justice)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        self.statute_pattern = r"(?:Section|Sec\.?)\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^,\n]*?)(?:Act|Code|Rules?)"
        
    async def process_judgment_pdf(
        self, 
        pdf_path: str, 
        judgment_id: int
    ) -> Dict[str, Any]:
        """
        Process a PDF judgment and extract structured data
        
        Args:
            pdf_path: Path to the PDF file
            judgment_id: ID of the judgment in database
            
        Returns:
            Dictionary containing extracted data
        """
        try:
            # Extract text from PDF
            full_text = await self._extract_text_from_pdf(pdf_path)
            
            if not full_text:
                return {
                    "success": False,
                    "error": "Could not extract text from PDF",
                    "judgment_id": judgment_id
                }
            
            # Extract structured information
            extracted_data = await self._extract_structured_data(full_text)
            
            # Split text into chunks for vector storage
            text_chunks = await self._split_text_into_chunks(full_text)
            
            return {
                "success": True,
                "judgment_id": judgment_id,
                "full_text": full_text,
                "text_length": len(full_text),
                "page_count": extracted_data.get("page_count", 0),
                "extracted_data": extracted_data,
                "text_chunks": text_chunks,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "judgment_id": judgment_id
            }
    
    async def _extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(page_text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                        continue
                
                full_text = "\n".join(text_content)
                return full_text if full_text.strip() else None
                
        except Exception as e:
            logger.error(f"Error reading PDF file {pdf_path}: {str(e)}")
            return None
    
    async def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from judgment text"""
        try:
            extracted_data = {
                "case_number": None,
                "case_title": None,
                "petitioner": None,
                "respondent": None,
                "judges": [],
                "judgment_date": None,
                "statutes_cited": [],
                "page_count": 0,
                "key_phrases": []
            }
            
            # Extract case number
            case_number_match = re.search(self.case_number_pattern, text, re.IGNORECASE)
            if case_number_match:
                extracted_data["case_number"] = case_number_match.group(1)
            
            # Extract case title (usually in first few lines)
            lines = text.split('\n')[:10]
            for line in lines:
                line = line.strip()
                if len(line) > 20 and len(line) < 200 and not line.isdigit():
                    if not extracted_data["case_title"]:
                        extracted_data["case_title"] = line
                    break
            
            # Extract judges
            judge_matches = re.findall(self.judge_pattern, text, re.IGNORECASE)
            extracted_data["judges"] = list(set(judge_matches))
            
            # Extract dates
            date_matches = re.findall(self.date_pattern, text)
            if date_matches:
                # Try to identify judgment date (usually the most recent)
                extracted_data["judgment_date"] = date_matches[-1]
            
            # Extract statutes
            statute_matches = re.findall(self.statute_pattern, text, re.IGNORECASE)
            for match in statute_matches:
                statute_text = f"Section {match[0]} of {match[1]}"
                if statute_text not in extracted_data["statutes_cited"]:
                    extracted_data["statutes_cited"].append(statute_text)
            
            # Extract key legal phrases
            key_phrases = self._extract_key_phrases(text)
            extracted_data["key_phrases"] = key_phrases
            
            # Estimate page count (rough approximation)
            extracted_data["page_count"] = max(1, len(text) // 2000)  # ~2000 chars per page
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {}
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key legal phrases from text"""
        key_phrases = []
        
        # Common legal phrase patterns
        phrase_patterns = [
            r"ratio decidendi[:\s]*([^.]+)",
            r"held that[:\s]*([^.]+)",
            r"it is settled law[:\s]*([^.]+)",
            r"the principle[:\s]*([^.]+)",
            r"this court[:\s]*([^.]+)",
            r"we are of the view[:\s]*([^.]+)"
        ]
        
        for pattern in phrase_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                phrase = match.strip()
                if len(phrase) > 20 and len(phrase) < 200:
                    key_phrases.append(phrase)
        
        return key_phrases[:10]  # Return top 10 phrases
    
    async def _split_text_into_chunks(
        self, 
        text: str, 
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks for vector storage"""
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                # Try to break at sentence boundary
                if end < len(text):
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    break_point = max(last_period, last_newline)
                    
                    if break_point > chunk_size * 0.7:  # If we can break reasonably
                        chunk_text = text[start:start + break_point + 1]
                        end = start + break_point + 1
                
                chunks.append({
                    "text": chunk_text.strip(),
                    "start_position": start,
                    "end_position": end,
                    "length": len(chunk_text)
                })
                
                start = end - overlap  # Overlap for context
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting text into chunks: {str(e)}")
            return []
    
    async def extract_citations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract citation references from judgment text"""
        try:
            citations = []
            
            # Pattern for case citations
            case_citation_pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)"
            
            matches = re.finditer(case_citation_pattern, text)
            for match in matches:
                citation = {
                    "petitioner": match.group(1),
                    "respondent": match.group(2),
                    "year": int(match.group(3)),
                    "full_citation": match.group(0),
                    "start_position": match.start(),
                    "end_position": match.end(),
                    "context": text[max(0, match.start()-100):match.end()+100]
                }
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Error extracting citations from text: {str(e)}")
            return []
