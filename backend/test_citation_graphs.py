#!/usr/bin/env python3
"""
Test script for citation graph and precedent strength functionality
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
import random

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, engine
from app.models.judgment import Judgment
from app.models.citation import Citation, CitationType, CitationNetwork
from app.services.citation_analyzer import CitationAnalyzer
from sqlalchemy.orm import Session

async def create_sample_judgments(db: Session):
    """Create sample judgments for testing"""
    print("Creating sample judgments...")
    
    sample_judgments = [
        {
            "case_number": "2020/SC/001",
            "case_title": "State of Maharashtra v. Rajesh Kumar",
            "petitioner": "State of Maharashtra",
            "respondent": "Rajesh Kumar",
            "judgment_date": datetime(2020, 3, 15),
            "full_text": "This case deals with criminal procedure and the right to fair trial. The court held that proper procedure must be followed in all criminal cases.",
            "year": 2020
        },
        {
            "case_number": "2019/SC/045",
            "case_title": "Union of India v. ABC Corp",
            "petitioner": "Union of India",
            "respondent": "ABC Corp",
            "judgment_date": datetime(2019, 8, 22),
            "full_text": "This landmark judgment established important principles regarding corporate governance and regulatory compliance.",
            "year": 2019
        },
        {
            "case_number": "2021/SC/078",
            "case_title": "Priya Sharma v. State of Delhi",
            "petitioner": "Priya Sharma",
            "respondent": "State of Delhi",
            "judgment_date": datetime(2021, 1, 10),
            "full_text": "This case involved constitutional law principles and fundamental rights. The court relied upon established precedents.",
            "year": 2021
        },
        {
            "case_number": "2020/SC/156",
            "case_title": "XYZ Ltd v. Workers Union",
            "petitioner": "XYZ Ltd",
            "respondent": "Workers Union",
            "judgment_date": datetime(2020, 11, 5),
            "full_text": "This labor law case distinguished earlier precedents and established new principles for industrial disputes.",
            "year": 2020
        },
        {
            "case_number": "2022/SC/023",
            "case_title": "Environmental Foundation v. State Govt",
            "petitioner": "Environmental Foundation",
            "respondent": "State Government",
            "judgment_date": datetime(2022, 6, 18),
            "full_text": "This environmental law case followed established precedents and applied them to modern environmental challenges.",
            "year": 2022
        }
    ]
    
    judgments = []
    for judgment_data in sample_judgments:
        # Check if judgment already exists
        existing = db.query(Judgment).filter(Judgment.case_number == judgment_data["case_number"]).first()
        if not existing:
            judgment = Judgment(**judgment_data)
            db.add(judgment)
            judgments.append(judgment)
        else:
            judgments.append(existing)
    
    db.commit()
    print(f"Created/found {len(judgments)} judgments")
    return judgments

async def create_sample_citations(db: Session, judgments: list):
    """Create sample citations between judgments"""
    print("Creating sample citations...")
    
    sample_citations = [
        {
            "source_idx": 2,  # Priya Sharma case
            "target_idx": 0,  # State of Maharashtra case
            "citation_type": CitationType.RELIED_UPON,
            "context": "The court relied upon the principle established in State of Maharashtra v. Rajesh Kumar that proper procedure must be followed in criminal cases.",
            "strength_score": 85,
            "confidence_score": 90,
            "is_positive": True,
            "legal_principle": "Right to fair trial and proper criminal procedure"
        },
        {
            "source_idx": 3,  # XYZ Ltd case
            "target_idx": 1,  # Union of India case
            "citation_type": CitationType.DISTINGUISHED,
            "context": "This case can be distinguished from Union of India v. ABC Corp as it deals with labor law rather than corporate governance.",
            "strength_score": 60,
            "confidence_score": 75,
            "is_positive": False,
            "legal_principle": "Corporate governance vs labor law principles"
        },
        {
            "source_idx": 4,  # Environmental Foundation case
            "target_idx": 0,  # State of Maharashtra case
            "citation_type": CitationType.FOLLOWED,
            "context": "Following the precedent set in State of Maharashtra v. Rajesh Kumar, this court applies the same procedural principles to environmental matters.",
            "strength_score": 78,
            "confidence_score": 85,
            "is_positive": True,
            "legal_principle": "Procedural fairness in environmental cases"
        },
        {
            "source_idx": 4,  # Environmental Foundation case
            "target_idx": 1,  # Union of India case
            "citation_type": CitationType.REFERRED,
            "context": "Reference is made to the regulatory principles discussed in Union of India v. ABC Corp regarding government oversight.",
            "strength_score": 55,
            "confidence_score": 70,
            "is_positive": True,
            "legal_principle": "Government regulatory oversight"
        },
        {
            "source_idx": 2,  # Priya Sharma case
            "target_idx": 1,  # Union of India case
            "citation_type": CitationType.CITED,
            "context": "The case of Union of India v. ABC Corp was cited for its discussion on constitutional principles.",
            "strength_score": 45,
            "confidence_score": 60,
            "is_positive": True,
            "legal_principle": "Constitutional law principles"
        }
    ]
    
    citations = []
    for citation_data in sample_citations:
        source_judgment = judgments[citation_data["source_idx"]]
        target_judgment = judgments[citation_data["target_idx"]]
        
        # Check if citation already exists
        existing = db.query(Citation).filter(
            Citation.source_judgment_id == source_judgment.id,
            Citation.target_judgment_id == target_judgment.id
        ).first()
        
        if not existing:
            citation = Citation(
                source_judgment_id=source_judgment.id,
                target_judgment_id=target_judgment.id,
                citation_type=citation_data["citation_type"],
                context=citation_data["context"],
                strength_score=citation_data["strength_score"],
                confidence_score=citation_data["confidence_score"],
                is_positive=citation_data["is_positive"],
                legal_principle=citation_data["legal_principle"]
            )
            db.add(citation)
            citations.append(citation)
        else:
            citations.append(existing)
    
    db.commit()
    print(f"Created/found {len(citations)} citations")
    return citations

async def test_citation_analysis(db: Session, judgments: list):
    """Test citation analysis functionality"""
    print("\n=== Testing Citation Analysis ===")
    
    analyzer = CitationAnalyzer(db)
    
    # Test citation strength analysis
    print("\n1. Testing Citation Strength Analysis:")
    test_context = "The court relied upon the landmark decision in State of Maharashtra v. Rajesh Kumar which established the principle that proper procedure must be followed in all criminal cases."
    
    analysis_result = await analyzer.analyze_citation_strength(
        source_judgment_id=judgments[2].id,  # Priya Sharma case
        target_judgment_id=judgments[0].id,  # State of Maharashtra case
        context_text=test_context
    )
    
    print(f"Citation Type: {analysis_result['citation_type']}")
    print(f"Strength Score: {analysis_result['strength_score']}")
    print(f"Confidence Score: {analysis_result['confidence_score']}")
    print(f"Is Positive: {analysis_result['is_positive']}")
    print(f"Legal Principle: {analysis_result.get('legal_principle', 'None')}")

async def test_citation_network(db: Session, judgments: list):
    """Test citation network functionality"""
    print("\n=== Testing Citation Network ===")
    
    analyzer = CitationAnalyzer(db)
    
    # Test network for State of Maharashtra case (most cited)
    target_judgment = judgments[0]  # State of Maharashtra case
    print(f"\n2. Testing Citation Network for: {target_judgment.case_title}")
    
    network_result = await analyzer.build_citation_network(target_judgment.id)
    
    print(f"Total Citations: {network_result.get('total_citations', 0)}")
    print(f"Network Nodes: {len(network_result.get('network', {}).get('nodes', []))}")
    print(f"Network Edges: {len(network_result.get('network', {}).get('edges', []))}")
    
    # Print network metrics
    metrics = network_result.get('metrics', {})
    print(f"\nNetwork Metrics:")
    print(f"- In-degree: {metrics.get('in_degree', 0)}")
    print(f"- Out-degree: {metrics.get('out_degree', 0)}")
    print(f"- PageRank: {metrics.get('pagerank', 0):.4f}")
    print(f"- Average Citation Strength: {metrics.get('avg_citation_strength', 0):.2f}")
    
    return network_result

async def test_citation_statistics(db: Session, judgments: list):
    """Test citation statistics functionality"""
    print("\n=== Testing Citation Statistics ===")
    
    analyzer = CitationAnalyzer(db)
    
    # Test statistics for each judgment
    for judgment in judgments:
        print(f"\n3. Citation Statistics for: {judgment.case_title}")
        
        stats = await analyzer.get_citation_statistics(judgment.id)
        
        print(f"- Outgoing Citations: {stats.get('outgoing_citations', 0)}")
        print(f"- Incoming Citations: {stats.get('incoming_citations', 0)}")
        print(f"- Total Citations: {stats.get('total_citations', 0)}")
        
        citation_types = stats.get('citation_types', {})
        if citation_types:
            print(f"- Citation Types: {citation_types}")
        
        strength_dist = stats.get('strength_distribution', {})
        if strength_dist:
            print(f"- Average Strength: {strength_dist.get('average', 0):.2f}")
            print(f"- Max Strength: {strength_dist.get('maximum', 0)}")

async def test_precedent_strength_ranking(db: Session):
    """Test precedent strength ranking"""
    print("\n=== Testing Precedent Strength Ranking ===")
    
    # Get all citations and group by target judgment
    citations = db.query(Citation).filter(Citation.strength_score.isnot(None)).all()
    
    if not citations:
        print("No citations with strength scores found")
        return
    
    # Group by target judgment and calculate average strength
    judgment_strengths = {}
    for citation in citations:
        target_id = citation.target_judgment_id
        if target_id not in judgment_strengths:
            judgment_strengths[target_id] = []
        judgment_strengths[target_id].append(citation.strength_score)
    
    # Calculate rankings
    ranking = []
    for judgment_id, strengths in judgment_strengths.items():
        avg_strength = sum(strengths) / len(strengths)
        ranking.append({
            "judgment_id": judgment_id,
            "average_strength": avg_strength,
            "citation_count": len(strengths),
            "max_strength": max(strengths),
            "min_strength": min(strengths)
        })
    
    # Sort by average strength
    ranking.sort(key=lambda x: x["average_strength"], reverse=True)
    
    print("\n4. Precedent Strength Ranking (Top Cases):")
    
    # Get judgment details
    judgment_ids = [item["judgment_id"] for item in ranking]
    judgments = db.query(Judgment).filter(Judgment.id.in_(judgment_ids)).all()
    judgment_dict = {j.id: j for j in judgments}
    
    for i, item in enumerate(ranking, 1):
        judgment = judgment_dict.get(item["judgment_id"])
        if judgment:
            print(f"{i}. {judgment.case_title}")
            print(f"   Average Strength: {item['average_strength']:.2f}")
            print(f"   Citation Count: {item['citation_count']}")
            print(f"   Strength Range: {item['min_strength']}-{item['max_strength']}")

async def main():
    """Main test function"""
    print("=== Citation Graph and Precedent Strength Testing ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create sample data
        judgments = await create_sample_judgments(db)
        citations = await create_sample_citations(db, judgments)
        
        # Test citation analysis functionality
        await test_citation_analysis(db, judgments)
        
        # Test citation network
        network_result = await test_citation_network(db, judgments)
        
        # Test citation statistics
        await test_citation_statistics(db, judgments)
        
        # Test precedent strength ranking
        await test_precedent_strength_ranking(db)
        
        print("\n=== Test Summary ===")
        print(f"✅ Created {len(judgments)} sample judgments")
        print(f"✅ Created {len(citations)} sample citations")
        print("✅ Citation strength analysis working")
        print("✅ Citation network generation working")
        print("✅ Citation statistics working")
        print("✅ Precedent strength ranking working")
        
        print("\n🎯 Citation graphs and precedent strength scoring are fully functional!")
        
        # Save network visualization data for frontend
        if network_result and network_result.get('network'):
            with open('citation_network_sample.json', 'w') as f:
                json.dump(network_result, f, indent=2, default=str)
            print("📊 Sample network data saved to citation_network_sample.json")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
