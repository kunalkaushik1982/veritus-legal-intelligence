"""
Entity extraction service for legal document analysis
File: backend/app/services/entity_extractor.py
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.entity import Entity, Timeline, EntityType
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Service for extracting entities and timelines from legal documents"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Entity extraction patterns
        self.entity_patterns = {
            EntityType.PARTY: [
                r"(?:petitioner|appellant|plaintiff)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:respondent|defendant)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ],
            EntityType.JUDGE: [
                r"(?:Hon'ble|Honourable)\s+(?:Mr\.?\s*Justice|Ms\.?\s*Justice|Justice)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ],
            EntityType.STATUTE: [
                r"(?:Section|Sec\.?)\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^,\n]*?)(?:Act|Code|Rules?)",
                r"Article\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^,\n]*?)",
                r"(\d+[A-Z]\s+[A-Z][^,\n]*?)\s+(?:Act|Code)"
            ],
            EntityType.CASE_LAW: [
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\s+SCC\)"
            ],
            EntityType.DATE: [
                r"(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})",
                r"(\d{4})",
                r"(?:on|dated?)\s+(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})"
            ],
            EntityType.COURT: [
                r"(?:Supreme Court|High Court|District Court|Sessions Court)",
                r"(?:Court of|Appellate Court)",
                r"(?:Tribunal|Commission)"
            ]
        }
        
        # Timeline event patterns
        self.timeline_patterns = [
            r"(?:filed|filing)\s+(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})",
            r"(?:heard|hearing)\s+(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})",
            r"(?:judgment|decided)\s+(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})",
            r"(?:appeal|appealed)\s+(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})",
            r"(?:order|ordered)\s+(?:on|dated?)\s+(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})"
        ]
    
    async def extract_timeline_and_entities(
        self, 
        judgment_id: int, 
        text: str
    ) -> Dict[str, Any]:
        """
        Extract timeline events and entities from judgment text
        
        Args:
            judgment_id: ID of the judgment
            text: Full text of the judgment
            
        Returns:
            Dictionary containing extracted timeline and entities
        """
        try:
            start_time = datetime.now()
            
            # Extract entities
            entities = await self._extract_entities(judgment_id, text)
            
            # Extract timeline events
            timeline_events = await self._extract_timeline_events(judgment_id, text)
            
            # Save to database
            await self._save_entities_to_db(entities)
            await self._save_timeline_to_db(timeline_events)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "timeline_events": timeline_events,
                "extracted_entities": entities,
                "processing_time_ms": int(processing_time),
                "total_entities": len(entities),
                "total_events": len(timeline_events)
            }
            
        except Exception as e:
            logger.error(f"Error extracting timeline and entities: {str(e)}")
            return {
                "timeline_events": [],
                "extracted_entities": [],
                "processing_time_ms": 0,
                "error": str(e)
            }
    
    async def _extract_entities(self, judgment_id: int, text: str) -> List[Dict[str, Any]]:
        """Extract entities from judgment text"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    
                    # Skip if entity is too short or too long
                    if len(entity_text.strip()) < 3 or len(entity_text.strip()) > 200:
                        continue
                    
                    entity = {
                        "judgment_id": judgment_id,
                        "entity_type": entity_type.value,
                        "entity_text": entity_text.strip(),
                        "normalized_text": self._normalize_entity_text(entity_text.strip(), entity_type),
                        "start_position": match.start(),
                        "end_position": match.end(),
                        "confidence_score": self._calculate_entity_confidence(entity_text, entity_type),
                        "is_primary": self._is_primary_entity(entity_text, entity_type),
                        "context": self._get_entity_context(text, match.start(), match.end()),
                        "extraction_method": "regex"
                    }
                    
                    entities.append(entity)
        
        # Remove duplicates and sort by confidence
        unique_entities = self._remove_duplicate_entities(entities)
        unique_entities.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return unique_entities[:50]  # Return top 50 entities
    
    async def _extract_timeline_events(self, judgment_id: int, text: str) -> List[Dict[str, Any]]:
        """Extract timeline events from judgment text"""
        events = []
        
        for pattern in self.timeline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                event_date_str = match.group(1)
                event_description = self._extract_event_description(text, match.start(), match.end())
                
                event = {
                    "judgment_id": judgment_id,
                    "event_date": self._parse_date(event_date_str),
                    "event_description": event_description,
                    "event_type": self._classify_event_type(event_description),
                    "parties_involved": self._extract_parties_from_event(event_description),
                    "court_involved": self._extract_court_from_event(event_description),
                    "legal_significance": self._assess_legal_significance(event_description),
                    "confidence_score": self._calculate_event_confidence(event_description),
                    "extraction_method": "regex"
                }
                
                events.append(event)
        
        # Sort by date
        events.sort(key=lambda x: x["event_date"] or datetime.min)
        
        return events[:20]  # Return top 20 events
    
    def _normalize_entity_text(self, text: str, entity_type: EntityType) -> str:
        """Normalize entity text based on type"""
        if entity_type == EntityType.STATUTE:
            # Normalize statute references
            return text.replace("Sec.", "Section").replace("sec.", "Section")
        elif entity_type == EntityType.JUDGE:
            # Normalize judge names
            return text.replace("Hon'ble", "").replace("Honourable", "").replace("Justice", "").strip()
        elif entity_type == EntityType.DATE:
            # Normalize date formats
            return self._normalize_date(text)
        
        return text
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to standard format"""
        try:
            # Try to parse common date formats
            from datetime import datetime
            
            formats = [
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d %B %Y",
                "%B %d, %Y"
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            return date_str
        except:
            return date_str
    
    def _calculate_entity_confidence(self, text: str, entity_type: EntityType) -> int:
        """Calculate confidence score for entity extraction"""
        confidence = 50  # Base confidence
        
        # Length-based confidence
        if 5 <= len(text) <= 50:
            confidence += 20
        elif len(text) > 50:
            confidence += 10
        
        # Type-specific confidence adjustments
        if entity_type == EntityType.JUDGE:
            if "Justice" in text or "Hon'ble" in text:
                confidence += 20
        elif entity_type == EntityType.STATUTE:
            if "Section" in text or "Article" in text:
                confidence += 20
        elif entity_type == EntityType.CASE_LAW:
            if "v." in text or "vs." in text:
                confidence += 20
        
        return min(max(confidence, 0), 100)
    
    def _is_primary_entity(self, text: str, entity_type: EntityType) -> bool:
        """Determine if entity is primary (most important)"""
        if entity_type == EntityType.PARTY:
            return "petitioner" in text.lower() or "appellant" in text.lower()
        elif entity_type == EntityType.JUDGE:
            return "Chief Justice" in text or "Justice" in text
        elif entity_type == EntityType.STATUTE:
            return "Section" in text or "Article" in text
        
        return False
    
    def _get_entity_context(self, text: str, start: int, end: int) -> str:
        """Get context around entity"""
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)
        return text[context_start:context_end]
    
    def _remove_duplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on text similarity"""
        unique_entities = []
        seen_texts = set()
        
        for entity in entities:
            normalized_text = entity["normalized_text"].lower()
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _extract_event_description(self, text: str, start: int, end: int) -> str:
        """Extract event description from context"""
        # Get surrounding context
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end]
        
        # Extract sentence containing the event
        sentences = re.split(r'[.!?]', context)
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["filed", "heard", "judgment", "appeal", "order"]):
                return sentence.strip()
        
        return context.strip()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        try:
            from datetime import datetime
            
            formats = [
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d %B %Y",
                "%B %d, %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except:
            return None
    
    def _classify_event_type(self, description: str) -> str:
        """Classify the type of event"""
        description_lower = description.lower()
        
        if "filed" in description_lower or "filing" in description_lower:
            return "filing"
        elif "heard" in description_lower or "hearing" in description_lower:
            return "hearing"
        elif "judgment" in description_lower or "decided" in description_lower:
            return "judgment"
        elif "appeal" in description_lower:
            return "appeal"
        elif "order" in description_lower:
            return "order"
        else:
            return "other"
    
    def _extract_parties_from_event(self, description: str) -> List[str]:
        """Extract parties involved in the event"""
        parties = []
        
        # Look for party patterns
        party_patterns = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:petitioner|appellant|plaintiff)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:respondent|defendant)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if isinstance(match, tuple):
                    parties.extend(match)
                else:
                    parties.append(match)
        
        return list(set(parties))  # Remove duplicates
    
    def _extract_court_from_event(self, description: str) -> Optional[str]:
        """Extract court involved in the event"""
        court_patterns = [
            r"(Supreme Court|High Court|District Court|Sessions Court)",
            r"(Court of [A-Z][a-z]+)",
            r"([A-Z][a-z]+ Tribunal)"
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
        
        return None
    
    def _assess_legal_significance(self, description: str) -> str:
        """Assess the legal significance of the event"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["landmark", "precedent", "binding", "authoritative"]):
            return "high"
        elif any(word in description_lower for word in ["important", "significant", "notable"]):
            return "medium"
        else:
            return "low"
    
    def _calculate_event_confidence(self, description: str) -> int:
        """Calculate confidence score for event extraction"""
        confidence = 50  # Base confidence
        
        # Length-based confidence
        if len(description) > 50:
            confidence += 20
        elif len(description) > 20:
            confidence += 10
        
        # Legal terminology presence
        legal_terms = ["court", "judgment", "filed", "heard", "appeal", "order"]
        term_count = sum(1 for term in legal_terms if term in description.lower())
        confidence += term_count * 5
        
        return min(max(confidence, 0), 100)
    
    async def _save_entities_to_db(self, entities: List[Dict[str, Any]]):
        """Save extracted entities to database"""
        try:
            for entity_data in entities:
                entity = Entity(**entity_data)
                self.db.add(entity)
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error saving entities to database: {str(e)}")
            self.db.rollback()
    
    async def _save_timeline_to_db(self, events: List[Dict[str, Any]]):
        """Save timeline events to database"""
        try:
            for event_data in events:
                event = Timeline(**event_data)
                self.db.add(event)
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error saving timeline to database: {str(e)}")
            self.db.rollback()
