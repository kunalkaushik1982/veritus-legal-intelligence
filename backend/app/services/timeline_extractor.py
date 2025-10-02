"""
Timeline extraction service for legal documents
File: backend/app/services/timeline_extractor.py
"""

import re
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimelineExtractor:
    """Service for extracting timeline events from legal documents"""
    
    def __init__(self):
        # Date patterns for legal documents
        self.date_patterns = [
            r'(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
            r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})',  # 1st January 2024
            r'(\d{4})',  # Just year
            r'(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})',  # on DD-MM-YYYY
        ]
        
        # Event type patterns
        self.event_patterns = {
            'filing': [r'filed', r'petition.*filed', r'application.*filed', r'complaint.*filed'],
            'hearing': [r'heard', r'hearing', r'argued', r'submissions', r'oral arguments'],
            'judgment': [r'judgment', r'decided', r'ruled', r'held', r'concluded'],
            'appeal': [r'appeal', r'appealed', r'challenged', r'petition.*appeal'],
            'order': [r'order', r'directed', r'instructed', r'commanded'],
            'notice': [r'notice', r'notified', r'served', r'issued.*notice'],
            'interim': [r'interim', r'temporary', r'stay', r'injunction']
        }
    
    async def extract_timeline_events(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """Extract timeline events from judgment text"""
        try:
            events = []
            
            # Split text into sentences for better analysis
            sentences = re.split(r'[.!?]+', text)
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                    
                # Look for dates in the sentence
                dates_found = []
                for pattern in self.date_patterns:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    dates_found.extend(matches)
                
                if dates_found:
                    # Determine event type
                    event_type = 'general'
                    for event_name, patterns in self.event_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, sentence, re.IGNORECASE):
                                event_type = event_name
                                break
                        if event_type != 'general':
                            break
                    
                    # Extract parties/court information
                    parties = []
                    if 'petitioner' in sentence.lower():
                        parties.append('Petitioner')
                    if 'respondent' in sentence.lower():
                        parties.append('Respondent')
                    if 'appellant' in sentence.lower():
                        parties.append('Appellant')
                    if 'defendant' in sentence.lower():
                        parties.append('Defendant')
                    
                    # Extract court information
                    court = None
                    court_patterns = [r'supreme court', r'high court', r'district court', r'sessions court']
                    for pattern in court_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            court = re.search(pattern, sentence, re.IGNORECASE).group()
                            break
                    
                    # Create timeline event
                    event = {
                        "event_id": len(events) + 1,
                        "event_date": dates_found[0] if dates_found else None,
                        "event_description": sentence[:200] + "..." if len(sentence) > 200 else sentence,
                        "event_type": event_type,
                        "parties_involved": parties if parties else None,
                        "court_involved": court,
                        "legal_significance": "High" if event_type in ['judgment', 'appeal'] else "Medium",
                        "confidence_score": 85 if event_type != 'general' else 60,
                        "page_reference": f"Page {i//10 + 1}",  # Estimate page number
                        "context": sentence
                    }
                    
                    events.append(event)
            
            # Sort events by date if possible
            try:
                events.sort(key=lambda x: x.get('event_date', ''), reverse=False)
            except:
                pass  # Keep original order if sorting fails
            
            return events[:20]  # Limit to 20 most relevant events
            
        except Exception as e:
            logger.error(f"Error extracting timeline events: {str(e)}")
            return []
