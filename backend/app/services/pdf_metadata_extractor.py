"""
PDF Metadata Extraction Service
Extracts structured information from legal PDFs including parties, dates, case numbers, and summaries
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFMetadataExtractor:
    """Service for extracting metadata from legal PDF documents"""
    
    def __init__(self):
        # Common legal patterns
        self.party_patterns = [
            r'(?:petitioner|appellant|plaintiff)\s*:?\s*([^,\n]+)',
            r'(?:respondent|defendant)\s*:?\s*([^,\n]+)',
            r'vs\.?\s*([^,\n]+)',
            r'v\.?\s*([^,\n]+)',
        ]
        
        self.date_patterns = [
            r'(?:dated|date)\s*:?\s*(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})',
            r'(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})',
            r'(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})',
        ]
        
        self.case_number_patterns = [
            r'(?:case\s+no\.?|civil\s+appeal\s+no\.?|criminal\s+appeal\s+no\.?|writ\s+petition\s+no\.?)\s*:?\s*([^\s,]+)',
            r'(?:no\.?|number)\s*:?\s*([^\s,]+)',
        ]
        
        self.court_patterns = [
            r'(supreme\s+court\s+of\s+india)',
            r'(high\s+court\s+of\s+[^,\n]+)',
            r'(district\s+court\s+of\s+[^,\n]+)',
        ]
        
        # Keywords for summary extraction
        self.summary_keywords = [
            'facts', 'background', 'case', 'issue', 'question', 'matter',
            'dispute', 'controversy', 'subject', 'topic'
        ]

    def extract_metadata(self, pdf_text: str, filename: str) -> Dict:
        """Extract comprehensive metadata from PDF text"""
        try:
            metadata = {
                'filename': filename,
                'petitioner': self._extract_petitioner(pdf_text),
                'respondent': self._extract_respondent(pdf_text),
                'judgment_date': self._extract_date(pdf_text),
                'case_number': self._extract_case_number(pdf_text),
                'court': self._extract_court(pdf_text),
                'case_title': self._extract_case_title(pdf_text),
                'summary': self._extract_summary(pdf_text),
                'judges': self._extract_judges(pdf_text),
                'extraction_date': datetime.now().isoformat(),
                'extraction_status': 'success'
            }
            
            # Generate a proper case title if not found
            if not metadata['case_title'] and metadata['petitioner'] and metadata['respondent']:
                metadata['case_title'] = f"{metadata['petitioner']} vs {metadata['respondent']}"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {
                'filename': filename,
                'petitioner': 'Unknown Petitioner',
                'respondent': 'Unknown Respondent',
                'judgment_date': None,
                'case_number': filename.replace('.pdf', ''),
                'court': 'Supreme Court',
                'case_title': filename.replace('.pdf', '').replace('_', ' ').replace('-', ' '),
                'summary': 'PDF uploaded and processed',
                'judges': [],
                'extraction_date': datetime.now().isoformat(),
                'extraction_status': 'error',
                'error': str(e)
            }

    def _extract_petitioner(self, text: str) -> Optional[str]:
        """Extract petitioner/appellant name"""
        text_lower = text.lower()
        
        # Look for petitioner/appellant patterns
        patterns = [
            r'(?:petitioner|appellant|plaintiff)\s*:?\s*([^,\n]{10,100})',
            r'([^,\n]+)\s+vs\.?\s+',
            r'([^,\n]+)\s+v\.?\s+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Clean up the extracted name
                name = matches[0].strip()
                # Remove common legal terms
                name = re.sub(r'\b(?:petitioner|appellant|plaintiff|and|others?)\b', '', name, flags=re.IGNORECASE)
                name = name.strip()
                if len(name) > 5:  # Ensure it's a meaningful name
                    return name.title()
        
        return None

    def _extract_respondent(self, text: str) -> Optional[str]:
        """Extract respondent/defendant name"""
        text_lower = text.lower()
        
        # Look for respondent/defendant patterns
        patterns = [
            r'(?:respondent|defendant)\s*:?\s*([^,\n]{10,100})',
            r'vs\.?\s+([^,\n]{10,100})',
            r'v\.?\s+([^,\n]{10,100})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Clean up the extracted name
                name = matches[0].strip()
                # Remove common legal terms
                name = re.sub(r'\b(?:respondent|defendant|and|others?)\b', '', name, flags=re.IGNORECASE)
                name = name.strip()
                if len(name) > 5:  # Ensure it's a meaningful name
                    return name.title()
        
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract judgment date"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    date_str = matches[0].strip()
                    # Try to parse and format the date
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        return parsed_date.isoformat()
                except:
                    continue
        
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y',
            '%d %B %Y', '%d %b %Y', '%B %d, %Y', '%b %d, %Y',
            '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None

    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number"""
        for pattern in self.case_number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                case_no = matches[0].strip()
                if len(case_no) > 3:  # Ensure it's a meaningful case number
                    return case_no
        
        return None

    def _extract_court(self, text: str) -> Optional[str]:
        """Extract court name"""
        for pattern in self.court_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].title()
        
        return None

    def _extract_case_title(self, text: str) -> Optional[str]:
        """Extract case title from the beginning of the document"""
        lines = text.split('\n')[:20]  # Check first 20 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 200:  # Reasonable title length
                # Check if it contains legal keywords
                if any(keyword in line.lower() for keyword in ['vs', 'v.', 'petitioner', 'respondent', 'appeal', 'case']):
                    return line
        
        return None

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract a brief summary from the document"""
        # Look for sections that might contain facts or background
        sections = text.split('\n\n')
        
        for section in sections[:10]:  # Check first 10 sections
            section = section.strip()
            if len(section) > 100 and len(section) < 500:  # Reasonable summary length
                # Check if it contains summary keywords
                if any(keyword in section.lower() for keyword in self.summary_keywords):
                    # Clean up the summary
                    summary = re.sub(r'\s+', ' ', section)  # Remove extra whitespace
                    return summary[:300] + '...' if len(summary) > 300 else summary
        
        return None

    def _extract_judges(self, text: str) -> List[str]:
        """Extract judge names"""
        judges = []
        
        # Look for judge patterns
        patterns = [
            r'(?:hon\'?ble\s+)?(?:mr\.?\s+)?justice\s+([^,\n]+)',
            r'(?:hon\'?ble\s+)?(?:chief\s+justice)\s+([^,\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                judge_name = match.strip().title()
                if len(judge_name) > 5 and judge_name not in judges:
                    judges.append(judge_name)
        
        return judges[:5]  # Limit to 5 judges

    def save_metadata(self, metadata: Dict, file_path: str) -> bool:
        """Save extracted metadata to a JSON file"""
        try:
            metadata_file = Path(file_path).with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            return False

    def load_metadata(self, file_path: str) -> Optional[Dict]:
        """Load metadata from JSON file"""
        try:
            metadata_file = Path(file_path).with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
        
        return None
