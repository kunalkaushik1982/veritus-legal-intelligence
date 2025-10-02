"""
Vector database service for semantic search and embeddings
File: backend/app/services/vector_service.py
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from openai import OpenAI
import json
import hashlib

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector embeddings and semantic search"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = "text-embedding-ada-002"
        self.embedding_dimension = 1536
        
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            
            # Process in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=self.embedding_model
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
                logger.info(f"Created embeddings for batch {i//batch_size + 1}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            return []
    
    async def create_judgment_embeddings(self, judgment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create embeddings for a judgment document
        
        Args:
            judgment_data: Dictionary containing judgment information
            
        Returns:
            Dictionary with embeddings and metadata
        """
        try:
            # Prepare text chunks for embedding
            text_chunks = self._prepare_text_chunks(judgment_data)
            
            if not text_chunks:
                return {"success": False, "error": "No text chunks to embed"}
            
            # Create embeddings for each chunk
            chunk_texts = [chunk["text"] for chunk in text_chunks]
            embeddings = await self.create_embeddings(chunk_texts)
            
            if not embeddings:
                return {"success": False, "error": "Failed to create embeddings"}
            
            # Combine chunks with their embeddings
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                embedded_chunk = {
                    "chunk_id": f"{judgment_data.get('case_number', 'unknown')}_{i}",
                    "text": chunk["text"],
                    "embedding": embedding,
                    "metadata": {
                        "case_number": judgment_data.get("case_number"),
                        "case_title": judgment_data.get("case_title"),
                        "chunk_index": i,
                        "start_position": chunk.get("start_position"),
                        "end_position": chunk.get("end_position"),
                        "judges": judgment_data.get("judges", []),
                        "statutes_cited": judgment_data.get("statutes_cited", []),
                        "text_hash": hashlib.md5(chunk["text"].encode()).hexdigest()
                    }
                }
                embedded_chunks.append(embedded_chunk)
            
            return {
                "success": True,
                "case_number": judgment_data.get("case_number"),
                "chunks": embedded_chunks,
                "total_chunks": len(embedded_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error creating judgment embeddings: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _prepare_text_chunks(self, judgment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare text chunks for embedding
        
        Args:
            judgment_data: Dictionary containing judgment information
            
        Returns:
            List of text chunks with metadata
        """
        try:
            full_text = judgment_data.get("full_text", "")
            if not full_text:
                return []
            
            # Split text into chunks
            chunk_size = 1000
            overlap = 200
            chunks = []
            
            start = 0
            while start < len(full_text):
                end = start + chunk_size
                chunk_text = full_text[start:end]
                
                # Try to break at sentence boundary
                if end < len(full_text):
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    break_point = max(last_period, last_newline)
                    
                    if break_point > chunk_size * 0.7:
                        chunk_text = full_text[start:start + break_point + 1]
                        end = start + break_point + 1
                
                chunks.append({
                    "text": chunk_text.strip(),
                    "start_position": start,
                    "end_position": end,
                    "length": len(chunk_text)
                })
                
                start = end - overlap
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error preparing text chunks: {str(e)}")
            return []
    
    async def search_similar_chunks(
        self, 
        query: str, 
        embedded_chunks: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity
        
        Args:
            query: Search query
            embedded_chunks: List of embedded chunks to search
            top_k: Number of top results to return
            
        Returns:
            List of similar chunks with similarity scores
        """
        try:
            # Create embedding for the query
            query_embeddings = await self.create_embeddings([query])
            if not query_embeddings:
                return []
            
            query_embedding = query_embeddings[0]
            
            # Calculate cosine similarity
            similarities = []
            for chunk in embedded_chunks:
                similarity = self._cosine_similarity(
                    query_embedding, 
                    chunk["embedding"]
                )
                similarities.append({
                    "chunk": chunk,
                    "similarity": similarity
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    async def get_relevant_context(
        self, 
        query: str, 
        judgment_chunks: List[Dict[str, Any]], 
        max_context_length: int = 3000
    ) -> Dict[str, Any]:
        """
        Get relevant context from judgments for a query
        
        Args:
            query: Search query
            judgment_chunks: List of judgment chunks to search
            max_context_length: Maximum length of context to return
            
        Returns:
            Dictionary with relevant context and metadata
        """
        try:
            # Search for similar chunks
            similar_chunks = await self.search_similar_chunks(
                query, 
                judgment_chunks, 
                top_k=10
            )
            
            if not similar_chunks:
                return {
                    "context": "",
                    "relevant_chunks": [],
                    "total_chunks_searched": len(judgment_chunks)
                }
            
            # Build context from top similar chunks
            context_parts = []
            relevant_chunks = []
            current_length = 0
            
            for item in similar_chunks:
                chunk = item["chunk"]
                similarity = item["similarity"]
                
                if current_length + len(chunk["text"]) > max_context_length:
                    break
                
                context_parts.append(chunk["text"])
                relevant_chunks.append({
                    "case_number": chunk["metadata"]["case_number"],
                    "case_title": chunk["metadata"]["case_title"],
                    "similarity": similarity,
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                })
                
                current_length += len(chunk["text"])
            
            return {
                "context": "\n\n".join(context_parts),
                "relevant_chunks": relevant_chunks,
                "total_chunks_searched": len(judgment_chunks),
                "top_similarity": similar_chunks[0]["similarity"] if similar_chunks else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return {
                "context": "",
                "relevant_chunks": [],
                "total_chunks_searched": 0
            }