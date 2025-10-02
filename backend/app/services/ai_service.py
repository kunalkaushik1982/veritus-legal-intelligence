"""
AI service for OpenAI integration and RAG implementation
File: backend/app/services/ai_service.py
"""

import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import asyncio
from datetime import datetime
import logging
import re
from dataclasses import dataclass

from app.config import settings
from app.services.vector_service import VectorService
from app.services.pdf_processor import PDFProcessor
from app.database import get_redis

logger = logging.getLogger(__name__)


@dataclass
class LegalQuery:
    """Structured representation of a legal query"""
    text: str
    intent: str  # question, search, explanation, comparison
    entities: List[str]  # extracted legal entities
    statutes: List[str]  # mentioned statutes
    cases: List[str]  # mentioned case names
    confidence: float  # query understanding confidence


class AIService:
    """
    AI service for legal chatbot functionality
    
    This service implements a sophisticated RAG (Retrieval Augmented Generation)
    system specifically designed for legal research.
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vector_service = VectorService()
        self.pdf_processor = PDFProcessor()
        self.redis_client = get_redis()
        
        # Legal-specific system prompts
        self.legal_system_prompt = """
        You are Veritus, an AI legal research assistant specializing in Indian Supreme Court judgments.
        
        Your role:
        - Provide accurate, contextual answers based on Supreme Court case law
        - Always cite specific judgments with case numbers and dates
        - Explain legal principles clearly and concisely
        - Highlight relevant statutes and legal precedents
        - Maintain professional legal language
        
        Guidelines:
        - Only use information from the provided judgment excerpts
        - If information is not available in the context, clearly state this
        - Provide case citations in standard legal format
        - Explain complex legal concepts in accessible language
        - Always mention the year and case number for citations
        
        Response format:
        - Start with a direct answer to the query
        - Provide supporting case law with proper citations
        - Include relevant legal principles
        - End with practical implications if applicable
        """
        
        # Query intent detection patterns
        self.intent_patterns = {
            "question": [
                r"what\s+(?:is|are|was|were)",
                r"how\s+(?:does|did|can|could)",
                r"when\s+(?:does|did|can|could)",
                r"where\s+(?:does|did|can|could)",
                r"why\s+(?:does|did|can|could)",
                r"explain\s+(?:the|this|that)",
                r"define\s+(?:the|this|that)"
            ],
            "search": [
                r"find\s+(?:cases?|judgments?|precedents?)",
                r"search\s+for",
                r"locate\s+(?:cases?|judgments?)",
                r"show\s+me\s+(?:cases?|judgments?)"
            ],
            "comparison": [
                r"compare\s+(?:with|to)",
                r"difference\s+(?:between|in)",
                r"versus\s+",
                r"vs\.?\s+",
                r"contrast\s+(?:with|to)"
            ],
            "explanation": [
                r"explain\s+(?:the|this|that)",
                r"describe\s+(?:the|this|that)",
                r"elaborate\s+(?:on|about)",
                r"clarify\s+(?:the|this|that)"
            ]
        }
    
    async def process_legal_query(
        self, 
        query: str, 
        user_id: int,
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Process a legal query using RAG approach
        
        Args:
            query: User's legal question
            user_id: ID of the user making the query
            context_limit: Number of relevant judgments to retrieve
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Analyze the query
            legal_query = await self._analyze_legal_query(query)
            logger.info(f"Query analysis completed: {legal_query.intent}, confidence: {legal_query.confidence}")
            
            # Step 2: Retrieve relevant judgments
            relevant_judgments = await self._retrieve_relevant_judgments(
                legal_query, context_limit
            )
            
            if not relevant_judgments:
                return await self._handle_no_results(legal_query, start_time)
            
            # Step 3: Prepare context for OpenAI
            context_text = self._prepare_context(relevant_judgments)
            
            # Step 4: Generate response using OpenAI
            response = await self._generate_response(query, context_text)
            
            # Step 5: Extract citations and metadata
            citations = self._extract_citations(response, relevant_judgments)
            
            # Calculate metrics
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "response": response["content"],
                "citations": citations,
                "relevant_judgments": [j["id"] for j in relevant_judgments],
                "confidence_score": self._calculate_confidence(response, relevant_judgments),
                "response_time_ms": int(response_time),
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "query_intent": legal_query.intent
            }
            
        except Exception as e:
            logger.error(f"Error processing legal query: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your query. Please try again.",
                "citations": [],
                "confidence_score": 0,
                "response_time_ms": 0,
                "tokens_used": 0,
                "error": str(e)
            }
    
    async def _analyze_legal_query(self, query: str) -> LegalQuery:
        """Analyze and structure the legal query"""
        query_lower = query.lower()
        
        # Detect intent
        intent = "general"
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent = intent_type
                    break
            if intent != "general":
                break
        
        # Extract entities (simplified for demo)
        entities = []
        statutes = []
        cases = []
        
        # Extract statutes
        statute_pattern = r"section\s+(\d+[A-Z]?)\s+(?:of\s+)?([A-Z][^,\n]*?)(?:Act|Code)"
        matches = re.findall(statute_pattern, query, re.IGNORECASE)
        for match in matches:
            statute_text = f"Section {match[0]} of {match[1]}"
            statutes.append(statute_text)
        
        # Calculate confidence
        confidence = 0.5
        if intent != "general":
            confidence += 0.2
        if statutes or cases or entities:
            confidence += 0.2
        if len(query) > 20:
            confidence += 0.1
        
        return LegalQuery(
            text=query,
            intent=intent,
            entities=entities,
            statutes=statutes,
            cases=cases,
            confidence=min(confidence, 1.0)
        )
    
    async def _retrieve_relevant_judgments(
        self, 
        legal_query: LegalQuery, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant judgments using vector similarity search"""
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(legal_query.text)
            
            # Search vector database
            search_results = await self.vector_service.search_similar(
                query_embedding, 
                limit=limit,
                filter_metadata={"is_processed": True}
            )
            
            # Format results
            judgments = []
            for result in search_results:
                judgments.append({
                    "id": result["id"],
                    "case_title": result["metadata"]["case_title"],
                    "case_number": result["metadata"]["case_number"],
                    "judgment_date": result["metadata"]["judgment_date"],
                    "summary": result["metadata"]["summary"],
                    "similarity_score": result["score"],
                    "text_excerpt": result["text"][:1000]
                })
            
            return judgments
            
        except Exception as e:
            logger.error(f"Error retrieving judgments: {str(e)}")
            return []
    
    def _prepare_context(self, judgments: List[Dict[str, Any]]) -> str:
        """Prepare context text for OpenAI from relevant judgments"""
        context_parts = []
        
        for i, judgment in enumerate(judgments, 1):
            context_part = f"""
Judgment {i}:
Case: {judgment['case_title']}
Case Number: {judgment['case_number']}
Date: {judgment['judgment_date']}
Summary: {judgment['summary']}
Relevant Text: {judgment['text_excerpt']}
---
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, query: str, context: str) -> Dict[str, Any]:
        """Generate response using OpenAI GPT-4"""
        try:
            messages = [
                {"role": "system", "content": self.legal_system_prompt},
                {
                    "role": "user", 
                    "content": f"""
Context from Supreme Court judgments:
{context}

User Query: {query}

Please provide a comprehensive legal answer based on the above judgments. Include proper citations and explain the legal principles clearly.
"""
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.3,
                top_p=0.9
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {}
            }
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise
    
    def _extract_citations(self, response: Dict[str, Any], judgments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and format citations from the response"""
        citations = []
        
        for judgment in judgments:
            citation = {
                "judgment_id": judgment["id"],
                "case_title": judgment["case_title"],
                "case_number": judgment["case_number"],
                "judgment_date": judgment["judgment_date"],
                "similarity_score": judgment["similarity_score"],
                "relevance_reason": "Relevant to user query based on semantic similarity"
            }
            citations.append(citation)
        
        return citations
    
    def _calculate_confidence(self, response: Dict[str, Any], judgments: List[Dict[str, Any]]) -> int:
        """Calculate confidence score for the response"""
        if not judgments:
            return 0
        
        # Base confidence on number of relevant judgments and their similarity scores
        avg_similarity = sum(j["similarity_score"] for j in judgments) / len(judgments)
        judgment_count_factor = min(len(judgments) / 5, 1.0)
        
        confidence = int((avg_similarity * 0.7 + judgment_count_factor * 0.3) * 100)
        return min(max(confidence, 0), 100)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def _handle_no_results(self, legal_query: LegalQuery, start_time: datetime) -> Dict[str, Any]:
        """Handle cases where no relevant judgments are found"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "response": f"""
I couldn't find relevant Supreme Court judgments for your query about "{legal_query.text}".

This could be because:
1. The legal issue is very recent and hasn't been decided by the Supreme Court yet
2. The query might be too specific or use terminology not found in our database
3. The issue might be more commonly addressed by High Courts or other tribunals

Suggestions:
- Try rephrasing your query with more general legal terms
- Break down complex queries into simpler, more specific questions
- Consider searching for related legal concepts or broader legal principles

If you believe this is an error, please try again or contact support.
""",
            "citations": [],
            "confidence_score": 0,
            "response_time_ms": int(processing_time),
            "tokens_used": 0,
            "query_intent": legal_query.intent
        }
