from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import json
import time
import shutil
import re
from datetime import datetime
from pathlib import Path
from app.api.batch_processing import router as batch_router
from app.collab.routes import router as collab_router
from app.services.rag_service import RAGService
from app.services.citation_analyzer import CitationAnalyzer
from app.services.pdf_processor import PDFProcessor
from app.services.pdf_metadata_extractor import PDFMetadataExtractor
from app.services.judgment_storage import JudgmentMetadataStorage
from app.services.timeline_extractor import TimelineExtractor
from app.services.case_summarizer import CaseSummarizer
from app.models.citation import Citation, CitationType

app = FastAPI(title="Veritus API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(batch_router)
app.include_router(collab_router)

# Initialize services
rag_service = RAGService()
pdf_processor = PDFProcessor()
metadata_extractor = PDFMetadataExtractor()
judgment_storage = JudgmentMetadataStorage()
timeline_extractor = TimelineExtractor()
case_summarizer = CaseSummarizer()

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Veritus Legal Intelligence API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "veritus-backend"}

@app.get("/api/test")
async def test():
    return {"message": "Test endpoint working"}

@app.post("/api/auth/register")
async def register():
    return {
        "access_token": "demo_token_123",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "demo@veritus.com",
            "full_name": "Demo User",
            "subscription_tier": "free",
            "queries_today": 0,
            "total_queries": 0
        }
    }

@app.post("/api/auth/login")
async def login(request: Request):
    # Get username from request body
    body = await request.body()
    username = "User"  # Default fallback
    
    # Parse form data
    if body:
        body_str = body.decode('utf-8')
        for param in body_str.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                if key == 'username':
                    username = value
                    break
    
    # Generate unique user ID based on username hash
    import hashlib
    user_id = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
    
    return {
        "access_token": f"demo_token_{user_id}",
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": f"{username}@veritus.com",
            "full_name": username,
            "subscription_tier": "pro",
            "queries_today": 0,
            "total_queries": 0
        }
    }

@app.post("/api/chatbot/query")
async def chatbot_query(request: Request):
    try:
        start_time = time.time()
        
        # Get request body
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        query = data.get('query', '')
        
        # Check if OpenAI API key is configured
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                "response": "OpenAI API key not configured. Please add your API key to the .env file.",
                "citations": [],
                "relevant_judgments": [],
                "confidence_score": 0,
                "response_time_ms": 0,
                "tokens_used": 0,
                "query_intent": "error",
                "context_used": False
            }
        
        # Use RAG service for query
        result = await rag_service.query_with_rag(query)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        result["response_time_ms"] = response_time_ms
        
        return result
        
    except Exception as e:
        return {
            "response": f"Error processing query: {str(e)}",
            "citations": [],
            "relevant_judgments": [],
            "confidence_score": 0,
            "response_time_ms": 0,
            "tokens_used": 0,
            "query_intent": "error",
            "context_used": False
        }

@app.post("/api/rag/load-judgments")
async def load_judgments():
    """Load sample judgments into the RAG knowledge base"""
    try:
        result = await rag_service.load_sample_judgments("/app/pdfs", limit=3)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/rag/status")
async def get_rag_status():
    """Get RAG knowledge base status"""
    try:
        status = await rag_service.get_knowledge_base_status()
        return status
    except Exception as e:
        return {
            "error": str(e)
        }

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF judgment"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(file_path), 1)
        
        if result.get("success", False):
            # Move to pdfs directory for permanent storage
            pdfs_dir = Path("pdfs")
            pdfs_dir.mkdir(exist_ok=True)
            final_path = pdfs_dir / file.filename
            shutil.move(str(file_path), str(final_path))
            
            # Get the full text for metadata extraction
            full_text = result.get("full_text", "")
            
            # Extract metadata using our new service
            extracted_metadata = metadata_extractor.extract_metadata(full_text, file.filename)
            
            # Add file information
            extracted_metadata.update({
                "file_path": str(final_path),
                "file_size": final_path.stat().st_size,
                "upload_date": datetime.now().isoformat()
            })
            
            # Generate judgment ID
            judgment_id = len(list(pdfs_dir.glob("*.pdf")))
            extracted_metadata["id"] = judgment_id
            
            # Store metadata persistently
            judgment_storage.save_judgment_metadata(judgment_id, extracted_metadata)
            
            # Prepare response data
            judgment_data = {
                "id": judgment_id,
                "case_title": extracted_metadata.get("case_title", file.filename.replace('.pdf', '')),
                "case_number": extracted_metadata.get("case_number", file.filename.replace('.pdf', '')),
                "petitioner": extracted_metadata.get("petitioner", "Unknown Petitioner"),
                "respondent": extracted_metadata.get("respondent", "Unknown Respondent"),
                "judgment_date": extracted_metadata.get("judgment_date"),
                "summary": extracted_metadata.get("summary", "PDF uploaded and processed"),
                "court": extracted_metadata.get("court", "Supreme Court"),
                "judges": extracted_metadata.get("judges", []),
                "is_processed": True,
                "filename": file.filename,
                "extraction_status": extracted_metadata.get("extraction_status", "success")
            }
            
            return {
                "success": True,
                "message": "PDF uploaded and processed successfully",
                "filename": file.filename,
                "file_path": str(final_path),
                "judgment": judgment_data,
                "extracted_metadata": extracted_metadata,
                "processing_result": result
            }
        else:
            # Clean up failed upload
            if file_path.exists():
                file_path.unlink()
            
            return {
                "success": False,
                "error": result.get("error", "Failed to process PDF"),
                "filename": file.filename
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}",
            "filename": file.filename if file else "unknown"
        }

@app.get("/api/judgments/")
async def list_judgments():
    """List all uploaded PDF judgments with extracted metadata"""
    try:
        # First, try to load from processed JSON file
        processed_file = Path("processed_judgments.json")
        if processed_file.exists():
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
                    judgments = processed_data.get("judgments", [])
                    if judgments:
                        return {"judgments": judgments}
            except Exception as e:
                print(f"Error loading processed judgments: {e}")
        
        # Fallback to stored metadata
        stored_judgments = judgment_storage.get_all_judgments()
        
        if not stored_judgments:
            # Fallback to basic file listing if no metadata exists
            pdfs_dir = Path("pdfs")
            if not pdfs_dir.exists():
                return {"judgments": []}
            
            judgments = []
            pdf_files = list(pdfs_dir.glob("*.pdf"))
            
            for i, pdf_file in enumerate(pdf_files, 1):
                filename = pdf_file.stem
                judgments.append({
                    "id": i,
                    "case_title": filename.replace('_', ' ').replace('-', ' '),
                    "case_number": filename,
                    "petitioner": "Unknown Petitioner",
                    "respondent": "Unknown Respondent",
                    "judgment_date": None,
                    "summary": f"Uploaded PDF: {filename}",
                    "court": "Supreme Court",
                    "judges": [],
                    "is_processed": True,
                    "filename": pdf_file.name,
                    "extraction_status": "pending"
                })
            
            return {"judgments": judgments}
        
        # Return stored metadata
        return {"judgments": stored_judgments}
        
    except Exception as e:
        return {"judgments": [], "error": str(e)}

@app.get("/api/judgments/{judgment_id}/view")
async def view_judgment(judgment_id: int):
    """View a specific judgment PDF"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Return the PDF file
        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename=pdf_file.name,
            headers={"Content-Disposition": f"inline; filename={pdf_file.name}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing PDF: {str(e)}")

@app.get("/api/judgments/{judgment_id}/download")
async def download_judgment(judgment_id: int):
    """Download a specific judgment PDF"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Return the PDF file for download
        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename=pdf_file.name,
            headers={"Content-Disposition": f"attachment; filename={pdf_file.name}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")

@app.get("/api/judgments/{judgment_id}/text")
async def get_judgment_text(judgment_id: int):
    """Get the full extracted text from a specific judgment PDF"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(pdf_file), judgment_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error extracting text: {result.get('error', 'Unknown error')}")
        
        full_text = result.get("full_text", "")
        text_length = result.get("text_length", 0)
        page_count = result.get("page_count", 0)
        
        return {
            "judgment_id": judgment_id,
            "filename": pdf_file.name,
            "full_text": full_text,
            "text_length": text_length,
            "page_count": page_count,
            "extraction_status": "success",
            "processing_timestamp": result.get("processing_timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

@app.post("/api/batch/process-existing")
async def process_existing_pdfs():
    """Process all existing PDFs in the pdfs directory"""
    try:
        # Simple test first
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            return {"success": False, "error": "PDFs directory not found", "processed": 0, "failed": 0, "total": 0}
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            return {"success": False, "error": "No PDF files found", "processed": 0, "failed": 0, "total": 0}
        
        # For now, just return the count of PDFs found
        return {
            "success": True,
            "message": f"Found {len(pdf_files)} PDF files ready for processing",
            "processed": 0,
            "failed": 0,
            "total": len(pdf_files),
            "pdf_files": [f.name for f in pdf_files[:5]]  # Show first 5 filenames
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

# Citation analysis endpoints
@app.post("/api/citations/analyze")
async def analyze_citation(request: Request):
    """Analyze citation relationship between two judgments"""
    try:
        body = await request.json()
        source_judgment_id = body.get("source_judgment_id", 1)
        target_judgment_id = body.get("target_judgment_id", 2)
        context_text = body.get("context_text", "")
        
        # Try to get actual PDF content for analysis
        pdfs_dir = Path("pdfs")
        source_content = ""
        target_content = ""
        
        # Get source PDF content
        if pdfs_dir.exists():
            pdf_files = list(pdfs_dir.glob("*.pdf"))
            if source_judgment_id <= len(pdf_files):
                source_file = pdf_files[source_judgment_id - 1]
                try:
                    source_result = await pdf_processor.process_judgment_pdf(str(source_file), source_judgment_id)
                    if source_result.get("success"):
                        source_content = source_result.get("full_text", "")
                except Exception as e:
                    print(f"Error processing source PDF: {e}")
        
        # Get target PDF content  
        if pdfs_dir.exists():
            pdf_files = list(pdfs_dir.glob("*.pdf"))
            if target_judgment_id <= len(pdf_files):
                target_file = pdf_files[target_judgment_id - 1]
                try:
                    target_result = await pdf_processor.process_judgment_pdf(str(target_file), target_judgment_id)
                    if target_result.get("success"):
                        target_content = target_result.get("full_text", "")
                except Exception as e:
                    print(f"Error processing target PDF: {e}")
        
        # Use actual PDF content if available, otherwise use context text
        analysis_text = context_text
        if source_content and target_content:
            # Look for citations of target in source
            analysis_text = f"Source judgment content: {source_content[:1000]}... Target judgment: {target_content[:500]}... Context: {context_text}"
        
        analyzer = CitationAnalyzer(None)
        
        analysis = await analyzer.analyze_citation_strength(
            source_judgment_id=source_judgment_id,
            target_judgment_id=target_judgment_id,
            context_text=analysis_text
        )
        
        # Add metadata about whether real PDFs were analyzed
        analysis["pdf_analysis"] = {
            "source_content_length": len(source_content),
            "target_content_length": len(target_content),
            "used_real_pdfs": bool(source_content and target_content)
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/api/timeline/{judgment_id}")
async def extract_timeline(judgment_id: int):
    """Extract timeline events from a specific judgment"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(pdf_file), judgment_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error extracting text: {result.get('error', 'Unknown error')}")
        
        full_text = result.get("full_text", "")
        
        # Extract timeline events using our timeline extractor
        timeline_events = await timeline_extractor.extract_timeline_events(full_text, pdf_file.name)
        
        return {
            "judgment_id": judgment_id,
            "filename": pdf_file.name,
            "case_title": pdf_file.stem.replace('_', ' ').replace('-', ' '),
            "timeline_events": timeline_events,
            "total_events": len(timeline_events),
            "extraction_status": "success",
            "processing_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting timeline: {str(e)}")

@app.get("/api/summary/{judgment_id}")
async def summarize_case(judgment_id: int):
    """Generate AI-powered case summary for a specific judgment"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(pdf_file), judgment_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error extracting text: {result.get('error', 'Unknown error')}")
        
        full_text = result.get("full_text", "")
        case_title = pdf_file.stem.replace('_', ' ').replace('-', ' ')
        
        # Generate AI summary with caching
        summary_result = await case_summarizer.summarize_case(full_text, case_title, pdf_file.name, False)
        
        if not summary_result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error generating summary: {summary_result.get('error', 'Unknown error')}")
        
        return {
            "judgment_id": judgment_id,
            "filename": pdf_file.name,
            "case_title": case_title,
            "summary": summary_result.get("summary", {}),
            "model_used": summary_result.get("model_used"),
            "tokens_used": summary_result.get("tokens_used"),
            "generated_at": summary_result.get("generated_at"),
            "from_cache": summary_result.get("from_cache", False),
            "cache_loaded_at": summary_result.get("cache_loaded_at"),
            "extraction_status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating case summary: {str(e)}")

@app.get("/api/citations/network/{judgment_id}")
async def get_citation_network(judgment_id: int, request: Request):
    """Get citation network for a specific judgment"""
    try:
        pdfs_dir = Path("pdfs")
        
        if not pdfs_dir.exists() or not list(pdfs_dir.glob("*.pdf")):
            # Return sample data if no PDFs
            sample_network = {
                "judgment_id": judgment_id,
                "network": {
                    "nodes": [
                        {
                            "id": judgment_id,
                            "label": f"Judgment {judgment_id}",
                            "type": "source",
                            "size": 40
                        },
                        {
                            "id": judgment_id + 1,
                            "label": f"Related Case {judgment_id + 1}",
                            "type": "target",
                            "size": 30
                        },
                        {
                            "id": judgment_id + 2,
                            "label": f"Precedent {judgment_id + 2}",
                            "type": "target",
                            "size": 35
                        }
                    ],
                    "edges": [
                        {
                            "source": judgment_id,
                            "target": judgment_id + 1,
                            "weight": 85,
                            "citation_type": "relied_upon",
                            "color": "#2E8B57"
                        },
                        {
                            "source": judgment_id,
                            "target": judgment_id + 2,
                            "weight": 72,
                            "citation_type": "followed",
                            "color": "#32CD32"
                        }
                    ]
                },
                "metrics": {
                    "in_degree": 2,
                    "out_degree": 2,
                    "pagerank": 0.3456,
                    "avg_citation_strength": 78.5
                },
                "total_citations": 2,
                "is_sample_data": True
            }
            return {
                "success": True,
                "network": sample_network,
                "timestamp": time.time()
            }
        
        # Build real network from uploaded PDFs
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        
        if judgment_id > len(pdf_files):
            return {
                "success": False,
                "error": f"Judgment {judgment_id} not found. Only {len(pdf_files)} PDFs available."
            }
        
        # Get the target judgment content
        target_file = pdf_files[judgment_id - 1]
        target_result = await pdf_processor.process_judgment_pdf(str(target_file), judgment_id)
        
        if not target_result.get("success"):
            return {
                "success": False,
                "error": "Failed to process target judgment"
            }
        
        target_content = target_result.get("full_text", "")
        
        # Find citations to other uploaded judgments
        nodes = []
        edges = []
        citations_found = 0
        
        # Add the target judgment as central node
        nodes.append({
            "id": judgment_id,
            "label": target_file.stem.replace('_', ' ').replace('-', ' '),
            "type": "source",
            "size": 50
        })
        
        # Check for citations to other uploaded PDFs
        for i, pdf_file in enumerate(pdf_files):
            if i + 1 == judgment_id:
                continue  # Skip self
            
            # Look for references to this PDF in the target content
            filename_refs = [
                pdf_file.stem,
                pdf_file.stem.replace('_', ' '),
                pdf_file.stem.replace('-', ' '),
                pdf_file.name
            ]
            
            citation_found = False
            citation_strength = 0
            
            for ref in filename_refs:
                if ref.lower() in target_content.lower():
                    citation_found = True
                    citation_strength = 60  # Base strength for filename match
                    break
            
            # Also check for common legal citation patterns
            if not citation_found:
                # Look for case citation patterns
                case_patterns = [
                    r"case\s+no\.?\s*\d+",
                    r"civil\s+appeal\s+no\.?\s*\d+",
                    r"criminal\s+appeal\s+no\.?\s*\d+",
                    r"writ\s+petition\s+no\.?\s*\d+"
                ]
                
                for pattern in case_patterns:
                    if re.search(pattern, target_content, re.IGNORECASE):
                        citation_found = True
                        citation_strength = 40
                        break
            
            if citation_found:
                # Add node for cited judgment
                nodes.append({
                    "id": i + 1,
                    "label": pdf_file.stem.replace('_', ' ').replace('-', ' '),
                    "type": "target",
                    "size": 35
                })
                
                # Add edge
                edges.append({
                    "source": judgment_id,
                    "target": i + 1,
                    "weight": citation_strength,
                    "citation_type": "cited",
                    "color": "#4A90E2"
                })
                
                citations_found += 1
        
        # Calculate metrics
        in_degree = 0  # How many cite this judgment
        out_degree = citations_found  # How many this judgment cites
        
        # Simple PageRank calculation
        pagerank = min(0.1 + (out_degree * 0.1), 1.0)
        
        avg_citation_strength = sum(edge["weight"] for edge in edges) / len(edges) if edges else 0
        
        network_data = {
            "judgment_id": judgment_id,
            "network": {
                "nodes": nodes,
                "edges": edges
            },
            "metrics": {
                "in_degree": in_degree,
                "out_degree": out_degree,
                "pagerank": pagerank,
                "avg_citation_strength": avg_citation_strength
            },
            "total_citations": citations_found,
            "is_sample_data": False,
            "target_file": target_file.name
        }
        
        return {
            "success": True,
            "network": network_data,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/api/timeline/{judgment_id}")
async def extract_timeline(judgment_id: int):
    """Extract timeline events from a specific judgment"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(pdf_file), judgment_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error extracting text: {result.get('error', 'Unknown error')}")
        
        full_text = result.get("full_text", "")
        
        # Extract timeline events using our timeline extractor
        timeline_events = await timeline_extractor.extract_timeline_events(full_text, pdf_file.name)
        
        return {
            "judgment_id": judgment_id,
            "filename": pdf_file.name,
            "case_title": pdf_file.stem.replace('_', ' ').replace('-', ' '),
            "timeline_events": timeline_events,
            "total_events": len(timeline_events),
            "extraction_status": "success",
            "processing_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting timeline: {str(e)}")

@app.get("/api/citations/strength-ranking")
async def get_strength_ranking(limit: int = 10):
    """Get precedent strength ranking"""
    try:
        # Sample ranking data
        sample_ranking = [
            {
                "judgment_id": 1,
                "case_title": "State of Maharashtra v. Rajesh Kumar",
                "case_number": "2020/SC/001",
                "average_strength": 82.0,
                "citation_count": 5,
                "max_strength": 90,
                "min_strength": 75,
                "consistency": 83.3
            },
            {
                "judgment_id": 4,
                "case_title": "XYZ Ltd v. Workers Union", 
                "case_number": "2020/SC/156",
                "average_strength": 70.0,
                "citation_count": 3,
                "max_strength": 72,
                "min_strength": 68,
                "consistency": 94.4
            },
            {
                "judgment_id": 2,
                "case_title": "Union of India v. ABC Corp",
                "case_number": "2019/SC/045", 
                "average_strength": 59.5,
                "citation_count": 4,
                "max_strength": 65,
                "min_strength": 55,
                "consistency": 84.6
            }
        ]
        
        return {
            "success": True,
            "ranking": sample_ranking[:limit],
            "total_judgments": len(sample_ranking),
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/api/timeline/{judgment_id}")
async def extract_timeline(judgment_id: int):
    """Extract timeline events from a specific judgment"""
    try:
        pdfs_dir = Path("pdfs")
        if not pdfs_dir.exists():
            raise HTTPException(status_code=404, detail="PDFs directory not found")
        
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if judgment_id < 1 or judgment_id > len(pdf_files):
            raise HTTPException(status_code=404, detail=f"Judgment {judgment_id} not found")
        
        pdf_file = pdf_files[judgment_id - 1]
        
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process the PDF to extract text
        result = await pdf_processor.process_judgment_pdf(str(pdf_file), judgment_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=f"Error extracting text: {result.get('error', 'Unknown error')}")
        
        full_text = result.get("full_text", "")
        
        # Extract timeline events using our timeline extractor
        timeline_events = await timeline_extractor.extract_timeline_events(full_text, pdf_file.name)
        
        return {
            "judgment_id": judgment_id,
            "filename": pdf_file.name,
            "case_title": pdf_file.stem.replace('_', ' ').replace('-', ' '),
            "timeline_events": timeline_events,
            "total_events": len(timeline_events),
            "extraction_status": "success",
            "processing_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting timeline: {str(e)}")
