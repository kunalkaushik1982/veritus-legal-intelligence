"""
RAG (Retrieval Augmented Generation) service for chatbot
File: backend/app/services/rag_service.py
"""

import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json
import asyncio
from pathlib import Path

from app.services.vector_service import VectorService
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based chatbot responses using judgment data"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.vector_service = VectorService()
        self.pdf_processor = PDFProcessor()
        
        # In-memory storage for demo (replace with database in production)
        self.judgment_chunks = []
        self.judgment_metadata = {}
        
    async def add_judgment_to_knowledge_base(self, pdf_path: str) -> Dict[str, Any]:
        """
        Add a judgment PDF to the knowledge base
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Process PDF
            result = await self.pdf_processor.process_judgment_pdf(pdf_path, 1)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to process PDF")
                }
            
            # Create embeddings
            embedding_result = await self.vector_service.create_judgment_embeddings(result)
            
            if not embedding_result.get("success", False):
                return {
                    "success": False,
                    "error": embedding_result.get("error", "Failed to create embeddings")
                }
            
            # Store in knowledge base
            case_number = embedding_result["case_number"]
            if not case_number:
                # Use filename as case number if extraction failed
                case_number = Path(pdf_path).stem
            
            self.judgment_chunks.extend(embedding_result["chunks"])
            self.judgment_metadata[case_number] = {
                "case_title": result.get("extracted_data", {}).get("case_title") or f"Case {case_number}",
                "judges": result.get("extracted_data", {}).get("judges", []),
                "statutes_cited": result.get("extracted_data", {}).get("statutes_cited", []),
                "text_length": result.get("text_length", 0),
                "page_count": result.get("extracted_data", {}).get("page_count", 0)
            }
            
            # Update chunk metadata with correct case number
            for chunk in embedding_result["chunks"]:
                chunk["metadata"]["case_number"] = case_number
            
            return {
                "success": True,
                "case_number": case_number,
                "chunks_added": len(embedding_result["chunks"]),
                "total_chunks": len(self.judgment_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error adding judgment to knowledge base: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_with_rag(self, user_query: str) -> Dict[str, Any]:
        """
        Answer a query using RAG (Retrieval Augmented Generation)
        
        Args:
            user_query: User's question
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # If no judgments in knowledge base, return general response
            if not self.judgment_chunks:
                return await self._get_general_response(user_query)
            
            # Get relevant context from judgments
            context_result = await self.vector_service.get_relevant_context(
                user_query,
                self.judgment_chunks,
                max_context_length=3000
            )
            
            # Create RAG prompt
            rag_prompt = self._create_rag_prompt(user_query, context_result)
            
            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are Veritus, an expert legal research assistant specializing in Indian Supreme Court judgments. Always base your answers on the provided legal context and cite specific cases when relevant."
                    },
                    {"role": "user", "content": rag_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract citations from relevant chunks
            citations = self._extract_citations(context_result["relevant_chunks"])
            
            # Calculate overall confidence score
            overall_confidence = self._calculate_overall_confidence(
                context_result["top_similarity"],
                citations,
                len(context_result["relevant_chunks"])
            )
            
            return {
                "response": ai_response,
                "citations": citations,
                "relevant_judgments": [chunk["case_number"] for chunk in context_result["relevant_chunks"] if chunk["case_number"]],
                "confidence_score": overall_confidence,
                "response_time_ms": 0,  # Will be calculated by caller
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "query_intent": "legal_research",
                "context_used": len(context_result["relevant_chunks"]) > 0,
                "total_judgments_searched": len(self.judgment_chunks),
                "top_similarity": context_result["top_similarity"],
                "citation_analysis": {
                    "total_citations_found": len(citations),
                    "high_relevance_citations": len([c for c in citations if c["relevance"] in ["Very High", "High"]]),
                    "average_relevance_score": sum(c["relevance_score"] for c in citations) / len(citations) if citations else 0,
                    "statutes_referenced": list(set([statute for c in citations for statute in c.get("statutes_cited", [])])),
                    "judges_mentioned": list(set([judge for c in citations for judge in c.get("judges", [])]))
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            return {
                "response": f"Error processing query: {str(e)}",
                "citations": [],
                "relevant_judgments": [],
                "confidence_score": 0,
                "response_time_ms": 0,
                "tokens_used": 0,
                "query_intent": "error",
                "context_used": False,
                "citation_analysis": {
                    "total_citations_found": 0,
                    "high_relevance_citations": 0,
                    "average_relevance_score": 0,
                    "statutes_referenced": [],
                    "judges_mentioned": []
                }
            }
    
    def _create_rag_prompt(self, user_query: str, context_result: Dict[str, Any]) -> str:
        """
        Create a RAG prompt with relevant context
        
        Args:
            user_query: User's question
            context_result: Relevant context from judgments
            
        Returns:
            Formatted prompt for AI
        """
        if not context_result["context"]:
            return f"""
            User Query: {user_query}
            
            Please provide a general legal analysis. Note that no specific case law context is available.
            """
        
        return f"""
        You are Veritus, an AI legal research assistant specializing in Indian Supreme Court judgments.
        
        User Query: {user_query}
        
        Relevant Legal Context from Supreme Court Judgments:
        {context_result["context"]}
        
        Please provide a comprehensive legal analysis that:
        1. Directly answers the user's question
        2. Uses the provided legal context from Supreme Court judgments
        3. Cites specific cases and legal principles from the context
        4. Explains the legal reasoning and precedents
        5. Provides practical implications for legal practice
        
        Format your response professionally with proper legal citations.
        If the context doesn't fully address the query, acknowledge this and provide general guidance.
        """
    
    def _extract_citations(self, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citations from relevant chunks with enhanced metadata
        
        Args:
            relevant_chunks: List of relevant judgment chunks
            
        Returns:
            List of citations with detailed information
        """
        citations = []
        seen_cases = set()
        
        for chunk in relevant_chunks:
            case_number = chunk["case_number"]
            if case_number not in seen_cases and case_number:
                # Get judgment metadata
                judgment_meta = self.judgment_metadata.get(case_number, {})
                
                # Calculate relevance score
                similarity = chunk["similarity"]
                relevance_score = self._calculate_relevance_score(similarity, chunk)
                
                # Determine relevance level
                if relevance_score >= 0.8:
                    relevance_level = "Very High"
                elif relevance_score >= 0.7:
                    relevance_level = "High"
                elif relevance_score >= 0.6:
                    relevance_level = "Medium"
                else:
                    relevance_level = "Low"
                
                citation = {
                    "case_title": chunk["case_title"] or judgment_meta.get("case_title", f"Case {case_number}"),
                    "case_number": case_number,
                    "relevance": relevance_level,
                    "similarity_score": similarity,
                    "relevance_score": relevance_score,
                    "judges": judgment_meta.get("judges", []),
                    "statutes_cited": judgment_meta.get("statutes_cited", []),
                    "text_length": judgment_meta.get("text_length", 0),
                    "page_count": judgment_meta.get("page_count", 0),
                    "context_snippet": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                    "citation_link": f"/judgment/{case_number}",  # For future frontend linking
                    "pdf_url": f"/pdfs/{case_number}.pdf"  # For future PDF access
                }
                
                citations.append(citation)
                seen_cases.add(case_number)
        
        # Sort by relevance score and return top 5
        citations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return citations[:5]
    
    def _calculate_relevance_score(self, similarity: float, chunk: Dict[str, Any]) -> float:
        """
        Calculate enhanced relevance score based on multiple factors
        
        Args:
            similarity: Cosine similarity score
            chunk: Chunk metadata
            
        Returns:
            Enhanced relevance score (0.0 to 1.0)
        """
        try:
            base_score = similarity
            
            # Boost score for longer, more detailed chunks
            text_length = len(chunk.get("text", ""))
            if text_length > 500:
                length_boost = 0.05
            elif text_length > 200:
                length_boost = 0.02
            else:
                length_boost = 0.0
            
            # Boost score for chunks with legal keywords
            legal_keywords = [
                "held", "ratio decidendi", "principle", "precedent", 
                "judgment", "court", "law", "legal", "statute", "section"
            ]
            text_lower = chunk.get("text", "").lower()
            keyword_count = sum(1 for keyword in legal_keywords if keyword in text_lower)
            keyword_boost = min(0.1, keyword_count * 0.02)
            
            # Calculate final score
            final_score = min(1.0, base_score + length_boost + keyword_boost)
            
            return round(final_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
            return similarity
    
    def _calculate_overall_confidence(
        self, 
        top_similarity: float, 
        citations: List[Dict[str, Any]], 
        relevant_chunks_count: int
    ) -> int:
        """
        Calculate overall confidence score for the response
        
        Args:
            top_similarity: Highest similarity score from search
            citations: List of citations found
            relevant_chunks_count: Number of relevant chunks found
            
        Returns:
            Overall confidence score (0-100)
        """
        try:
            # Base confidence from similarity
            base_confidence = top_similarity * 70  # Max 70 points from similarity
            
            # Boost for number of citations
            citation_boost = min(15, len(citations) * 3)  # Max 15 points from citations
            
            # Boost for high relevance citations
            high_relevance_count = len([c for c in citations if c["relevance"] in ["Very High", "High"]])
            relevance_boost = min(10, high_relevance_count * 2)  # Max 10 points from high relevance
            
            # Boost for chunk count (more context = higher confidence)
            context_boost = min(5, relevant_chunks_count * 0.5)  # Max 5 points from context
            
            # Calculate final confidence
            final_confidence = base_confidence + citation_boost + relevance_boost + context_boost
            
            return min(95, int(final_confidence))  # Cap at 95%
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {str(e)}")
            return int(top_similarity * 70)  # Fallback to similarity-based score
    
    async def _get_general_response(self, user_query: str) -> Dict[str, Any]:
        """
        Get a general response when no judgment context is available
        
        Args:
            user_query: User's question
            
        Returns:
            Dictionary with general response
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are Veritus, an expert legal research assistant. Provide general legal guidance based on your knowledge."
                    },
                    {"role": "user", "content": user_query}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return {
                "response": response.choices[0].message.content,
                "citations": [],
                "relevant_judgments": [],
                "confidence_score": 60,  # Lower confidence for general responses
                "response_time_ms": 0,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "query_intent": "general_legal_advice",
                "context_used": False,
                "total_judgments_searched": 0,
                "citation_analysis": {
                    "total_citations_found": 0,
                    "high_relevance_citations": 0,
                    "average_relevance_score": 0,
                    "statutes_referenced": [],
                    "judges_mentioned": []
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting general response: {str(e)}")
            return {
                "response": f"Error processing query: {str(e)}",
                "citations": [],
                "relevant_judgments": [],
                "confidence_score": 0,
                "response_time_ms": 0,
                "tokens_used": 0,
                "query_intent": "error",
                "context_used": False,
                "citation_analysis": {
                    "total_citations_found": 0,
                    "high_relevance_citations": 0,
                    "average_relevance_score": 0,
                    "statutes_referenced": [],
                    "judges_mentioned": []
                }
            }
    
    async def get_knowledge_base_status(self) -> Dict[str, Any]:
        """
        Get status of the knowledge base
        
        Returns:
            Dictionary with knowledge base statistics
        """
        return {
            "total_chunks": len(self.judgment_chunks),
            "total_judgments": len(self.judgment_metadata),
            "judgment_list": list(self.judgment_metadata.keys()),
            "memory_usage_mb": len(str(self.judgment_chunks)) / (1024 * 1024)
        }
    
    async def load_sample_judgments(self, pdf_directory: str, limit: int = 5) -> Dict[str, Any]:
        """
        Load sample judgments for demo purposes
        
        Args:
            pdf_directory: Directory containing PDF files
            limit: Maximum number of PDFs to load
            
        Returns:
            Dictionary with loading results
        """
        try:
            import os
            from pathlib import Path
            
            pdf_dir = Path(pdf_directory)
            if not pdf_dir.exists():
                return {
                    "success": False,
                    "error": f"Directory {pdf_directory} does not exist"
                }
            
            pdf_files = list(pdf_dir.glob("*.pdf"))[:limit]
            loaded_count = 0
            
            for pdf_file in pdf_files:
                result = await self.add_judgment_to_knowledge_base(str(pdf_file))
                if result.get("success", False):
                    loaded_count += 1
                    logger.info(f"Loaded judgment: {result['case_number']}")
            
            return {
                "success": True,
                "loaded_judgments": loaded_count,
                "total_chunks": len(self.judgment_chunks),
                "judgment_list": list(self.judgment_metadata.keys())
            }
            
        except Exception as e:
            logger.error(f"Error loading sample judgments: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
