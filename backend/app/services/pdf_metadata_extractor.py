"""
PDF Metadata Extractor Service
Extracts legal metadata from judgment text
"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFMetadataExtractor:
    """Service for extracting metadata from legal judgment text"""
    
    def __init__(self):
        # Regex patterns for extracting legal metadata
        self.patterns = {
            'case_number': [
                r'(?:Civil Appeal|Criminal Appeal|Writ Petition|Special Leave Petition|Review Petition)[\s\(]*(?:No\.?)?[\s\(]*(\d+(?:[-/]\d+)*)',
                r'(?:C\.A\.|Cr\.A\.|W\.P\.|S\.L\.P\.|R\.P\.)[\s\(]*(?:No\.?)?[\s\(]*(\d+(?:[-/]\d+)*)',
                r'(?:Case|Appeal|Petition)[\s]*(?:No\.?)?[\s]*:?[\s]*(\d+(?:[-/]\d+)*)',
                r'(\d{4}/\w{2,}/\d+)',  # Year/Court/Number format
            ],
            'petitioner': [
                r'(?:Petitioner|Appellant)[\s]*:[\s]*([^\n\r]+?)(?:\s*Vs?\.|versus|v\.|against)',
                r'^([^\n\r]+?)(?:\s*Vs?\.|versus|v\.|against)',
                r'In the matter of[\s]*:?[\s]*([^\n\r]+?)(?:\s*Vs?\.|versus|v\.|against)',
            ],
            'respondent': [
                r'(?:Vs?\.|versus|v\.|against)[\s]*([^\n\r]+?)(?:\n|\r|$|\.\.\.)',
                r'(?:Respondent|Appellee)[\s]*:[\s]*([^\n\r]+?)(?:\n|\r|$)',
            ],
            'judges': [
                r'(?:Before|Coram)[\s]*:?[\s]*([^\n\r]+?)(?:\n|\r)',
                r'(?:Hon\'ble|Justice|J\.)[\s]+([A-Z][a-zA-Z\s\.]+?)(?:,|and|\n|\r)',
                r'Justice[\s]+([A-Z][a-zA-Z\s\.]+?)(?:,|and|\n|\r)',
            ],
            'judgment_date': [
                r'(?:Judgment|Decided|Date)[\s]*:?[\s]*([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})',
                r'(?:Delivered|Pronounced)[\s]*(?:on)?[\s]*:?[\s]*([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})',
                r'([0-9]{1,2}(?:st|nd|rd|th)?[\s]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[\s]+[0-9]{4})',
            ],
            'court': [
                r'(Supreme Court of India)',
                r'(High Court of [A-Za-z\s]+)',
                r'(District Court of [A-Za-z\s]+)',
                r'(?:In the|Before the)[\s]+([A-Za-z\s]+Court[A-Za-z\s]*)',
            ]
        }
    
    def extract_metadata(self, text: str, filename: str = "") -> Dict:
        """Extract comprehensive metadata from judgment text"""
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for metadata extraction")
                return self._default_metadata(filename)
            
            # Clean text for better extraction
            clean_text = self._clean_text(text)
            
            # Extract each type of metadata
            metadata = {
                'case_number': self._extract_case_number(clean_text),
                'case_title': self._extract_case_title(clean_text),
                'petitioner': self._extract_petitioner(clean_text),
                'respondent': self._extract_respondent(clean_text),
                'judges': self._extract_judges(clean_text),
                'judgment_date': self._extract_judgment_date(clean_text),
                'court': self._extract_court(clean_text),
                'summary': self._extract_summary(clean_text),
                'keywords': self._extract_keywords(clean_text),
                'statutes_cited': self._extract_statutes(clean_text),
                'cases_cited': self._extract_cited_cases(clean_text),
                'file_name': filename,
                'extraction_timestamp': datetime.now().isoformat(),
                'text_length': len(text),
                'confidence_score': 0.8  # Default confidence
            }
            
            # Generate case title if not found
            if not metadata['case_title']:
                metadata['case_title'] = self._generate_case_title(
                    metadata['petitioner'], 
                    metadata['respondent']
                )
            
            # Calculate confidence score based on extracted data
            metadata['confidence_score'] = self._calculate_confidence(metadata)
            
            logger.info(f"Metadata extracted successfully for {filename}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return self._default_metadata(filename)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better extraction"""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove page numbers and headers/footers
            text = re.sub(r'Page \d+ of \d+', '', text)
            text = re.sub(r'\d+\s*$', '', text, flags=re.MULTILINE)
            
            # Normalize common legal abbreviations
            text = re.sub(r'\bVs?\b\.?', 'v.', text)
            text = re.sub(r'\bversus\b', 'v.', text, flags=re.IGNORECASE)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def _extract_case_number(self, text: str) -> str:
        """Extract case number using multiple patterns"""
        for pattern in self.patterns['case_number']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_case_title(self, text: str) -> str:
        """Extract case title from the beginning of the document"""
        try:
            # Look for title in first few lines
            lines = text.split('\n')[:10]
            
            for line in lines:
                if 'v.' in line.lower() or 'vs.' in line.lower():
                    # Clean up the title
                    title = re.sub(r'\s+', ' ', line).strip()
                    title = re.sub(r'^[^a-zA-Z]*', '', title)  # Remove leading non-letters
                    if len(title) > 10 and len(title) < 200:
                        return title
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting case title: {e}")
            return ""
    
    def _extract_petitioner(self, text: str) -> str:
        """Extract petitioner name"""
        for pattern in self.patterns['petitioner']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                petitioner = match.group(1).strip()
                # Clean up common artifacts
                petitioner = re.sub(r'\s+', ' ', petitioner)
                petitioner = re.sub(r'[^\w\s\.,&()-]', '', petitioner)
                if len(petitioner) > 2:
                    return petitioner
        return ""
    
    def _extract_respondent(self, text: str) -> str:
        """Extract respondent name"""
        for pattern in self.patterns['respondent']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                respondent = match.group(1).strip()
                # Clean up common artifacts
                respondent = re.sub(r'\s+', ' ', respondent)
                respondent = re.sub(r'[^\w\s\.,&()-]', '', respondent)
                if len(respondent) > 2:
                    return respondent
        return ""
    
    def _extract_judges(self, text: str) -> List[str]:
        """Extract judge names"""
        judges = []
        
        for pattern in self.patterns['judges']:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                judge_text = match.group(1).strip()
                
                # Split multiple judges
                judge_names = re.split(r',|and|\n', judge_text)
                
                for judge in judge_names:
                    judge = judge.strip()
                    # Clean up judge name
                    judge = re.sub(r'(?:Hon\'ble|Justice|J\.)', '', judge, flags=re.IGNORECASE)
                    judge = re.sub(r'\s+', ' ', judge).strip()
                    
                    if len(judge) > 3 and judge not in judges:
                        judges.append(judge)
        
        return judges[:5]  # Limit to 5 judges
    
    def _extract_judgment_date(self, text: str) -> str:
        """Extract judgment date"""
        for pattern in self.patterns['judgment_date']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                date_str = match.group(1).strip()
                # Try to normalize date format
                try:
                    # Handle different date formats
                    if re.match(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}', date_str):
                        return date_str
                    elif re.match(r'\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4}', date_str):
                        return date_str
                except:
                    pass
                return date_str
        return ""
    
    def _extract_court(self, text: str) -> str:
        """Extract court name"""
        for pattern in self.patterns['court']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                court = match.group(1).strip()
                return court
        return ""
    
    def _extract_summary(self, text: str, max_length: int = 500) -> str:
        """Extract a summary from the judgment"""
        try:
            # Look for summary sections
            summary_patterns = [
                r'(?:Summary|Abstract|Brief)[\s]*:[\s]*([^\n\r]+(?:\n[^\n\r]+)*)',
                r'(?:Held|Decided|Conclusion)[\s]*:[\s]*([^\n\r]+(?:\n[^\n\r]+)*)',
            ]
            
            for pattern in summary_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    summary = match.group(1).strip()
                    if len(summary) > 50:
                        return summary[:max_length] + "..." if len(summary) > max_length else summary
            
            # Fallback: use first paragraph
            paragraphs = text.split('\n\n')
            for para in paragraphs[1:6]:  # Skip first paragraph (usually title)
                para = para.strip()
                if len(para) > 100:
                    return para[:max_length] + "..." if len(para) > max_length else para
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting summary: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant legal keywords"""
        try:
            # Common legal terms to look for
            legal_terms = [
                'constitutional', 'fundamental rights', 'due process', 'natural justice',
                'criminal law', 'civil law', 'contract', 'tort', 'property',
                'evidence', 'procedure', 'appeal', 'revision', 'writ',
                'mandamus', 'certiorari', 'prohibition', 'quo warranto',
                'habeas corpus', 'injunction', 'damages', 'compensation'
            ]
            
            keywords = []
            text_lower = text.lower()
            
            for term in legal_terms:
                if term in text_lower:
                    keywords.append(term)
            
            return keywords[:10]  # Limit to 10 keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _extract_statutes(self, text: str) -> List[str]:
        """Extract cited statutes and acts"""
        try:
            statute_patterns = [
                r'([A-Z][a-zA-Z\s]+ Act,? \d{4})',
                r'(Section \d+(?:\([a-z]\))? of [A-Z][a-zA-Z\s]+ Act,? \d{4})',
                r'(Article \d+(?:\([a-z]\))? of [a-zA-Z\s]+ Constitution)',
                r'([A-Z][a-zA-Z\s]+ Code,? \d{4})',
            ]
            
            statutes = []
            
            for pattern in statute_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    statute = match.group(1).strip()
                    if statute not in statutes and len(statute) > 5:
                        statutes.append(statute)
            
            return statutes[:15]  # Limit to 15 statutes
            
        except Exception as e:
            logger.error(f"Error extracting statutes: {e}")
            return []
    
    def _extract_cited_cases(self, text: str) -> List[str]:
        """Extract cited case names"""
        try:
            # Pattern for case citations
            case_patterns = [
                r'([A-Z][a-zA-Z\s&]+ v\.? [A-Z][a-zA-Z\s&]+(?:\s*\(\d{4}\))?)',
                r'(In re [A-Z][a-zA-Z\s&]+(?:\s*\(\d{4}\))?)',
            ]
            
            cases = []
            
            for pattern in case_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    case = match.group(1).strip()
                    if case not in cases and len(case) > 10:
                        cases.append(case)
            
            return cases[:20]  # Limit to 20 cases
            
        except Exception as e:
            logger.error(f"Error extracting cited cases: {e}")
            return []
    
    def _generate_case_title(self, petitioner: str, respondent: str) -> str:
        """Generate case title from petitioner and respondent"""
        try:
            if petitioner and respondent:
                return f"{petitioner} v. {respondent}"
            elif petitioner:
                return f"{petitioner} v. Unknown"
            elif respondent:
                return f"Unknown v. {respondent}"
            else:
                return "Unknown Case"
        except Exception as e:
            logger.error(f"Error generating case title: {e}")
            return "Unknown Case"
    
    def _calculate_confidence(self, metadata: Dict) -> float:
        """Calculate confidence score based on extracted metadata"""
        try:
            score = 0.0
            total_fields = 8
            
            # Weight different fields
            weights = {
                'case_number': 0.2,
                'petitioner': 0.15,
                'respondent': 0.15,
                'judges': 0.1,
                'judgment_date': 0.1,
                'court': 0.1,
                'case_title': 0.1,
                'summary': 0.1
            }
            
            for field, weight in weights.items():
                if metadata.get(field):
                    if isinstance(metadata[field], list):
                        if len(metadata[field]) > 0:
                            score += weight
                    elif len(str(metadata[field]).strip()) > 0:
                        score += weight
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _default_metadata(self, filename: str = "") -> Dict:
        """Return default metadata structure"""
        return {
            'case_number': '',
            'case_title': 'Unknown Case',
            'petitioner': '',
            'respondent': '',
            'judges': [],
            'judgment_date': '',
            'court': '',
            'summary': '',
            'keywords': [],
            'statutes_cited': [],
            'cases_cited': [],
            'file_name': filename,
            'extraction_timestamp': datetime.now().isoformat(),
            'text_length': 0,
            'confidence_score': 0.0
        }