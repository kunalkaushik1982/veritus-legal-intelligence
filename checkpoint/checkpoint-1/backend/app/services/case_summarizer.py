"""
Case summarization service using OpenAI
File: backend/app/services/case_summarizer.py
"""

import openai
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CaseSummarizer:
    """Service for generating structured case summaries using OpenAI"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key="your-openai-api-key")  # Will be updated from environment
        # Create cache directory
        self.cache_dir = Path("case_summaries_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_openai_client(self):
        """Get OpenAI client with API key from environment"""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return openai.OpenAI(api_key=api_key)
    
    def _get_cache_file_path(self, filename: str) -> Path:
        """Get cache file path for a given filename"""
        # Create a safe filename for caching
        safe_filename = filename.replace('.pdf', '').replace(' ', '_').replace('/', '_')
        return self.cache_dir / f"{safe_filename}_summary.json"
    
    def _load_from_cache(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load summary from cache if it exists"""
        try:
            cache_file = self._get_cache_file_path(filename)
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    logger.info(f"Loaded summary from cache for {filename}")
                    return cached_data
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
        return None
    
    def _save_to_cache(self, filename: str, summary_data: Dict[str, Any]) -> None:
        """Save summary to cache"""
        try:
            cache_file = self._get_cache_file_path(filename)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved summary to cache for {filename}")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")

    async def summarize_case(self, case_text: str, case_title: str, filename: str, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Generate structured case summary using OpenAI with caching
        
        Args:
            case_text: Full text of the judgment
            case_title: Title of the case
            filename: Original filename
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Dictionary containing structured summary
        """
        try:
            # Check cache first (unless force regenerate)
            if not force_regenerate:
                cached_summary = self._load_from_cache(filename)
                if cached_summary:
                    cached_summary["from_cache"] = True
                    cached_summary["cache_loaded_at"] = datetime.now().isoformat()
                    return cached_summary
            
            logger.info(f"Generating new AI summary for {filename}")
            client = self._get_openai_client()
            
            # Create the prompt for structured summarization
            prompt = self._create_summarization_prompt(case_text, case_title)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal expert specializing in Indian Supreme Court judgments. Provide detailed, accurate analysis of legal cases with proper citations and legal terminology."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent, factual output
                top_p=0.9
            )
            
            # Parse the response
            summary_text = response.choices[0].message.content
            
            # Parse the structured response
            structured_summary = self._parse_summary_response(summary_text)
            
            summary_data = {
                "success": True,
                "case_title": case_title,
                "filename": filename,
                "summary": structured_summary,
                "raw_response": summary_text,
                "model_used": "gpt-4",
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "generated_at": datetime.now().isoformat(),
                "from_cache": False
            }
            
            # Save to cache
            self._save_to_cache(filename, summary_data)
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating case summary: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "case_title": case_title,
                "filename": filename,
                "generated_at": datetime.now().isoformat(),
                "from_cache": False
            }
    
    def _create_summarization_prompt(self, case_text: str, case_title: str) -> str:
        """Create the prompt for OpenAI summarization"""
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 12000  # Leave room for prompt and response
        if len(case_text) > max_chars:
            case_text = case_text[:max_chars] + "\n\n[Text truncated for analysis...]"
        
        prompt = f"""
Please analyze the following Supreme Court judgment and provide a comprehensive summary under the following structured headings:

**Case:** {case_title}

**Judgment Text:**
{case_text}

Please provide your analysis under these exact headings:

## Facts
- Summarize the key factual background of the case
- Include relevant dates, parties, and circumstances
- Focus on material facts that influenced the court's decision

## Issues
- List the main legal issues/questions before the court
- Identify the core legal questions that needed resolution
- Number each issue clearly

## Petitioner's Arguments
- Summarize the main arguments presented by the petitioner/appellant
- Include legal precedents cited by the petitioner
- Highlight key legal principles relied upon

## Respondent's Arguments
- Summarize the main arguments presented by the respondent
- Include legal precedents cited by the respondent
- Highlight key legal principles relied upon

## Analysis of the Law
- Explain the relevant legal provisions, statutes, or constitutional articles
- Analyze how the law applies to the facts of the case
- Discuss any legal interpretations or clarifications made

## Precedent Analysis
- Identify and analyze relevant case law cited
- Explain how previous judgments influenced the current decision
- Discuss any distinguishing features from cited precedents

## Court's Reasoning
- Explain the court's logical reasoning process
- Highlight the key legal principles established or reaffirmed
- Discuss the court's interpretation of the law

## Conclusion
- Summarize the court's final decision
- State the ratio decidendi (the legal principle that forms the basis of the decision)
- Mention any orders or directions given by the court

Please ensure your analysis is:
- Accurate and based on the provided text
- Written in clear, professional legal language
- Comprehensive but concise
- Properly structured under each heading
"""
        
        return prompt
    
    def _parse_summary_response(self, response_text: str) -> Dict[str, str]:
        """Parse the OpenAI response into structured sections"""
        
        sections = {
            "facts": "",
            "issues": "",
            "petitioner_arguments": "",
            "respondent_arguments": "",
            "analysis_of_law": "",
            "precedent_analysis": "",
            "courts_reasoning": "",
            "conclusion": ""
        }
        
        # Split response by headings
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if line.lower().startswith('## facts'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'facts'
                current_content = []
            elif line.lower().startswith('## issues'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'issues'
                current_content = []
            elif line.lower().startswith('## petitioner') and 'argument' in line.lower():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'petitioner_arguments'
                current_content = []
            elif line.lower().startswith('## respondent') and 'argument' in line.lower():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'respondent_arguments'
                current_content = []
            elif line.lower().startswith('## analysis') and 'law' in line.lower():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'analysis_of_law'
                current_content = []
            elif line.lower().startswith('## precedent'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'precedent_analysis'
                current_content = []
            elif line.lower().startswith('## court') and 'reasoning' in line.lower():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'courts_reasoning'
                current_content = []
            elif line.lower().startswith('## conclusion'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'conclusion'
                current_content = []
            elif current_section and line:
                current_content.append(line)
        
        # Add the last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
