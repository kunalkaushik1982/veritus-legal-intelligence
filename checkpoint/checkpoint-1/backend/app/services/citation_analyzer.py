"""
Citation analysis service for legal precedent strength analysis
File: backend/app/services/citation_analyzer.py
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from collections import defaultdict, Counter
import networkx as nx

from app.models.citation import Citation, CitationType, CitationNetwork
from app.models.judgment import Judgment
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class CitationAnalyzer:
    """Service for analyzing citation relationships and strength"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Citation strength keywords for different relationship types
        self.citation_keywords = {
            CitationType.RELIED_UPON: [
                "relied upon", "followed", "applied", "adopted", "accepted",
                "approved", "endorsed", "supported", "upheld", "confirmed"
            ],
            CitationType.DISTINGUISHED: [
                "distinguished", "different", "not applicable", "inapplicable",
                "not followed", "rejected", "declined to follow"
            ],
            CitationType.OVERRULED: [
                "overruled", "overruling", "set aside", "reversed", "quashed",
                "annulled", "invalidated", "superseded"
            ],
            CitationType.REFERRED: [
                "referred to", "mentioned", "cited", "noted", "observed",
                "discussed", "considered", "examined"
            ],
            CitationType.FOLLOWED: [
                "followed", "adopted", "applied", "implemented", "enforced"
            ]
        }
    
    async def analyze_citation_strength(
        self, 
        source_judgment_id: int, 
        target_judgment_id: int,
        context_text: str
    ) -> Dict[str, Any]:
        """
        Analyze the strength of a citation relationship
        
        Args:
            source_judgment_id: ID of the judgment making the citation
            target_judgment_id: ID of the judgment being cited
            context_text: Text containing the citation
            
        Returns:
            Dictionary with citation analysis results
        """
        try:
            # Extract citation type and context
            citation_type = self._detect_citation_type(context_text)
            strength_score = self._calculate_strength_score(context_text, citation_type)
            confidence_score = self._calculate_confidence_score(context_text)
            
            # Extract legal principles and statutes
            legal_principle = self._extract_legal_principle(context_text)
            statute_reference = self._extract_statute_reference(context_text)
            issue_category = self._categorize_legal_issue(context_text)
            
            # Determine if citation is positive or negative
            is_positive = self._is_positive_citation(citation_type, context_text)
            
            return {
                "citation_type": citation_type.value,
                "strength_score": strength_score,
                "confidence_score": confidence_score,
                "legal_principle": legal_principle,
                "statute_reference": statute_reference,
                "issue_category": issue_category,
                "is_positive": is_positive,
                "context": context_text,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing citation strength: {str(e)}")
            return {
                "citation_type": "cited",
                "strength_score": 50,
                "confidence_score": 30,
                "error": str(e)
            }
    
    def _detect_citation_type(self, context_text: str) -> CitationType:
        """Detect the type of citation relationship"""
        context_lower = context_text.lower()
        
        # Check for each citation type
        for citation_type, keywords in self.citation_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    return citation_type
        
        # Default to general citation
        return CitationType.CITED
    
    def _calculate_strength_score(self, context_text: str, citation_type: CitationType) -> int:
        """Calculate citation strength score (0-100)"""
        base_scores = {
            CitationType.RELIED_UPON: 90,
            CitationType.FOLLOWED: 85,
            CitationType.REFERRED: 60,
            CitationType.DISTINGUISHED: 30,
            CitationType.OVERRULED: 10,
            CitationType.CITED: 50
        }
        
        base_score = base_scores.get(citation_type, 50)
        
        # Adjust based on context indicators
        context_lower = context_text.lower()
        
        # High significance indicators
        high_indicators = ["landmark", "precedent", "binding", "authoritative", "settled law"]
        for indicator in high_indicators:
            if indicator in context_lower:
                base_score = min(base_score + 10, 100)
        
        # Negative indicators
        negative_indicators = ["not binding", "not applicable", "distinguished", "overruled"]
        for indicator in negative_indicators:
            if indicator in context_lower:
                base_score = max(base_score - 20, 0)
        
        return base_score
    
    def _calculate_confidence_score(self, context_text: str) -> int:
        """Calculate confidence in citation analysis (0-100)"""
        confidence = 50  # Base confidence
        
        # Increase confidence for clear indicators
        context_lower = context_text.lower()
        
        # Strong positive indicators
        strong_indicators = ["clearly", "explicitly", "specifically", "directly"]
        for indicator in strong_indicators:
            if indicator in context_lower:
                confidence += 10
        
        # Legal terminology presence
        legal_terms = ["court", "judgment", "precedent", "principle", "law", "statute"]
        term_count = sum(1 for term in legal_terms if term in context_lower)
        confidence += term_count * 5
        
        # Context length (more context = higher confidence)
        if len(context_text) > 200:
            confidence += 10
        elif len(context_text) < 50:
            confidence -= 20
        
        return min(max(confidence, 0), 100)
    
    def _extract_legal_principle(self, context_text: str) -> Optional[str]:
        """Extract the legal principle being cited"""
        # Look for principle indicators
        principle_patterns = [
            r"principle\s+(?:of|that|is)\s+([^.]+)",
            r"rule\s+(?:of|that|is)\s+([^.]+)",
            r"doctrine\s+(?:of|that|is)\s+([^.]+)",
            r"established\s+(?:that|is)\s+([^.]+)",
            r"held\s+(?:that|is)\s+([^.]+)"
        ]
        
        for pattern in principle_patterns:
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_statute_reference(self, context_text: str) -> Optional[str]:
        """Extract statute references from citation context"""
        # Common statute patterns
        statute_patterns = [
            r"section\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^.]*)",
            r"article\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^.]*)",
            r"(\d+[A-Z]\s+[A-Z][^.]*)\s+act",
            r"(\d+[A-Z]\s+[A-Z][^.]*)\s+code"
        ]
        
        for pattern in statute_patterns:
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _categorize_legal_issue(self, context_text: str) -> Optional[str]:
        """Categorize the legal issue being discussed"""
        issue_categories = {
            "constitutional": ["constitution", "fundamental right", "article", "amendment"],
            "criminal": ["criminal", "offence", "penalty", "punishment", "bail", "arrest"],
            "civil": ["civil", "contract", "tort", "damages", "injunction", "specific performance"],
            "family": ["marriage", "divorce", "maintenance", "custody", "adoption"],
            "property": ["property", "land", "possession", "title", "ownership"],
            "commercial": ["company", "partnership", "bankruptcy", "insolvency", "merger"],
            "administrative": ["government", "public", "administrative", "bureaucracy"],
            "labor": ["employment", "labor", "wages", "industrial", "trade union"]
        }
        
        context_lower = context_text.lower()
        
        for category, keywords in issue_categories.items():
            for keyword in keywords:
                if keyword in context_lower:
                    return category
        
        return "general"
    
    def _is_positive_citation(self, citation_type: CitationType, context_text: str) -> bool:
        """Determine if citation is positive (supporting) or negative (opposing)"""
        if citation_type in [CitationType.RELIED_UPON, CitationType.FOLLOWED]:
            return True
        elif citation_type in [CitationType.OVERRULED, CitationType.DISTINGUISHED]:
            return False
        
        # Check context for positive/negative indicators
        context_lower = context_text.lower()
        
        positive_indicators = ["support", "agree", "correct", "valid", "sound"]
        negative_indicators = ["disagree", "incorrect", "invalid", "unsound", "reject"]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in context_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in context_lower)
        
        return positive_count > negative_count
    
    async def build_citation_network(self, judgment_id: int) -> Dict[str, Any]:
        """
        Build citation network for a specific judgment
        
        Args:
            judgment_id: ID of the judgment to analyze
            
        Returns:
            Dictionary containing network analysis results
        """
        try:
            # Get all citations involving this judgment
            citations = self.db.query(Citation).filter(
                or_(
                    Citation.source_judgment_id == judgment_id,
                    Citation.target_judgment_id == judgment_id
                )
            ).all()
            
            if not citations:
                return {
                    "judgment_id": judgment_id,
                    "network": {"nodes": [], "edges": []},
                    "metrics": {},
                    "message": "No citations found for this judgment"
                }
            
            # Build network graph
            G = nx.DiGraph()
            
            # Add nodes and edges
            for citation in citations:
                source_id = citation.source_judgment_id
                target_id = citation.target_judgment_id
                
                # Add nodes
                G.add_node(source_id, type="source")
                G.add_node(target_id, type="target")
                
                # Add edge with weight based on strength
                weight = citation.strength_score or 50
                G.add_edge(source_id, target_id, 
                          weight=weight,
                          citation_type=citation.citation_type.value,
                          strength_score=citation.strength_score)
            
            # Calculate network metrics
            metrics = self._calculate_network_metrics(G, judgment_id)
            
            # Format network data for frontend
            network_data = self._format_network_data(G, judgment_id)
            
            return {
                "judgment_id": judgment_id,
                "network": network_data,
                "metrics": metrics,
                "total_citations": len(citations),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error building citation network: {str(e)}")
            return {
                "judgment_id": judgment_id,
                "error": str(e),
                "network": {"nodes": [], "edges": []},
                "metrics": {}
            }
    
    def _calculate_network_metrics(self, G: nx.DiGraph, judgment_id: int) -> Dict[str, Any]:
        """Calculate network analysis metrics"""
        try:
            metrics = {}
            
            # Basic metrics
            metrics["total_nodes"] = G.number_of_nodes()
            metrics["total_edges"] = G.number_of_edges()
            
            # Centrality measures
            if G.has_node(judgment_id):
                metrics["in_degree"] = G.in_degree(judgment_id)
                metrics["out_degree"] = G.out_degree(judgment_id)
                metrics["total_degree"] = metrics["in_degree"] + metrics["out_degree"]
                
                # PageRank centrality
                try:
                    pagerank = nx.pagerank(G)
                    metrics["pagerank"] = pagerank.get(judgment_id, 0)
                except:
                    metrics["pagerank"] = 0
                
                # Betweenness centrality
                try:
                    betweenness = nx.betweenness_centrality(G)
                    metrics["betweenness_centrality"] = betweenness.get(judgment_id, 0)
                except:
                    metrics["betweenness_centrality"] = 0
            
            # Network-level metrics
            try:
                metrics["density"] = nx.density(G)
                metrics["is_connected"] = nx.is_weakly_connected(G)
            except:
                metrics["density"] = 0
                metrics["is_connected"] = False
            
            # Citation strength metrics
            edge_strengths = [data.get("strength_score", 50) for _, _, data in G.edges(data=True)]
            if edge_strengths:
                metrics["avg_citation_strength"] = sum(edge_strengths) / len(edge_strengths)
                metrics["max_citation_strength"] = max(edge_strengths)
                metrics["min_citation_strength"] = min(edge_strengths)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating network metrics: {str(e)}")
            return {}
    
    def _format_network_data(self, G: nx.DiGraph, judgment_id: int) -> Dict[str, Any]:
        """Format network data for frontend visualization"""
        try:
            nodes = []
            edges = []
            
            # Get judgment details for nodes
            judgment_ids = list(G.nodes())
            judgments = self.db.query(Judgment).filter(Judgment.id.in_(judgment_ids)).all()
            judgment_dict = {j.id: j for j in judgments}
            
            # Format nodes
            for node_id in G.nodes():
                judgment = judgment_dict.get(node_id)
                if judgment:
                    node = {
                        "id": node_id,
                        "label": judgment.case_title[:50] + "..." if len(judgment.case_title) > 50 else judgment.case_title,
                        "case_number": judgment.case_number,
                        "judgment_date": judgment.judgment_date.isoformat() if judgment.judgment_date else None,
                        "type": "source" if node_id == judgment_id else "target",
                        "size": G.degree(node_id) * 10 + 20  # Size based on degree
                    }
                    nodes.append(node)
            
            # Format edges
            for source, target, data in G.edges(data=True):
                edge = {
                    "source": source,
                    "target": target,
                    "weight": data.get("weight", 50),
                    "citation_type": data.get("citation_type", "cited"),
                    "strength_score": data.get("strength_score", 50),
                    "color": self._get_edge_color(data.get("citation_type", "cited"))
                }
                edges.append(edge)
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
        except Exception as e:
            logger.error(f"Error formatting network data: {str(e)}")
            return {"nodes": [], "edges": []}
    
    def _get_edge_color(self, citation_type: str) -> str:
        """Get color for citation type in visualization"""
        color_map = {
            "relied_upon": "#2E8B57",  # Sea Green
            "followed": "#32CD32",      # Lime Green
            "referred": "#4169E1",      # Royal Blue
            "distinguished": "#FF8C00", # Dark Orange
            "overruled": "#DC143C",     # Crimson
            "cited": "#708090"          # Slate Gray
        }
        return color_map.get(citation_type, "#708090")
    
    async def get_citation_statistics(self, judgment_id: int) -> Dict[str, Any]:
        """Get comprehensive citation statistics for a judgment"""
        try:
            # Get citations where this judgment is the source
            outgoing_citations = self.db.query(Citation).filter(
                Citation.source_judgment_id == judgment_id
            ).all()
            
            # Get citations where this judgment is the target
            incoming_citations = self.db.query(Citation).filter(
                Citation.target_judgment_id == judgment_id
            ).all()
            
            # Calculate statistics
            stats = {
                "judgment_id": judgment_id,
                "outgoing_citations": len(outgoing_citations),
                "incoming_citations": len(incoming_citations),
                "total_citations": len(outgoing_citations) + len(incoming_citations),
                "citation_types": {},
                "strength_distribution": {},
                "temporal_analysis": {}
            }
            
            # Citation type distribution
            all_citations = outgoing_citations + incoming_citations
            citation_types = Counter(c.citation_type.value for c in all_citations)
            stats["citation_types"] = dict(citation_types)
            
            # Strength score distribution
            strength_scores = [c.strength_score for c in all_citations if c.strength_score]
            if strength_scores:
                stats["strength_distribution"] = {
                    "average": sum(strength_scores) / len(strength_scores),
                    "maximum": max(strength_scores),
                    "minimum": min(strength_scores),
                    "count": len(strength_scores)
                }
            
            # Temporal analysis
            judgment = self.db.query(Judgment).filter(Judgment.id == judgment_id).first()
            if judgment and judgment.judgment_date:
                judgment_year = judgment.judgment_date.year
                
                # Citations by year
                year_citations = defaultdict(int)
                for citation in all_citations:
                    source_judgment = self.db.query(Judgment).filter(
                        Judgment.id == citation.source_judgment_id
                    ).first()
                    if source_judgment and source_judgment.judgment_date:
                        year_citations[source_judgment.judgment_date.year] += 1
                
                stats["temporal_analysis"] = {
                    "judgment_year": judgment_year,
                    "citations_by_year": dict(year_citations),
                    "years_since_judgment": datetime.now().year - judgment_year
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting citation statistics: {str(e)}")
            return {
                "judgment_id": judgment_id,
                "error": str(e)
            }
