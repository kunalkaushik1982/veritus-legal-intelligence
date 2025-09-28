# Veritus

# masterplan.md

## App Overview and Objectives
The application is a **legal intelligence and productivity platform** designed to assist lawyers, law firms, in-house legal teams, and students.  
Its primary mission is to reduce the time spent on legal research, case analysis, and drafting by combining **AI-powered insights** with **structured legal data**.  

**MVP Objective:**  
Launch with a **chat-first experience** that allows advocates to query judgments conversationally, analyze the strength of citations, and extract case timelines/entities.  

---

## Target Audience
- **Primary (MVP launch):** Individual advocates handling multiple cases.  
- **Secondary (Phase 2):**  
  - Law firms with small teams.  
  - In-house legal departments.  
  - Law students for research and drafting practice.  

---

## Core Features (MVP)
1. **Chatbot trained on judgments**  
   - Natural language queries on case law.  
   - Contextual answers with linked citations.  

2. **Citation Strength Analyzer**  
   - Citation graph visualizations.  
   - Precedent strength scoring (relied upon vs. distinguished vs. overruled).  

3. **Timeline & Entity Extraction**  
   - Converts long judgments into structured timelines.  
   - Extracts parties, statutes, dates, issues, and ratio decidendi.  

---

## Future Feature Expansion
- Smart Draft Checker (like Grammarly for law).  
- AI Co-Counsel with counter-arguments.  
- Cross-jurisdictional comparative analysis.  
- Predictive analytics on benches and statutes.  
- Automated translation and summarization for regional courts.  
- Full practice management (case tracking, deadlines, reminders).  

---

## Platform Strategy
- **Hybrid Launch:**  
  - **Web App:** Full feature set (chat, citation analyzer, timeline extraction).  
  - **Mobile Companion:** Quick chatbot queries, basic timelines, push notifications.  

---

## High-Level Technical Stack
- **Frontend:**  
  - Web: React or Next.js.  
  - Mobile: React Native or Flutter for cross-platform development.  

- **Backend:**  
  - API layer: Node.js/Express or Python/FastAPI.  
  - Authentication: OAuth2 (Google/LinkedIn) + email/password.  

- **Databases:**  
  - Relational DB (PostgreSQL) → users, teams, structured metadata.  
  - Graph DB (Neo4j) → citations, knowledge graph.  
  - Search Engine (Elasticsearch / OpenSearch) → fast full-text queries.  

- **AI Layer:**  
  - Pre-trained LLMs (GPT/Claude) fine-tuned on Indian legal corpus.  
  - Vector database (Pinecone/Weaviate) for embeddings & semantic search.  

- **Cloud & Storage:**  
  - Cloud storage (AWS S3/GCP/Azure) for raw judgments.  
  - Processing pipeline for PDF → structured text → embeddings.  

---

## Conceptual Data Model
- **Judgment**: ID, Court, Bench, Date, Statutes, Full text.  
- **Citation**: Source case → Target case (with relation type: relied, distinguished, overruled).  
- **Entities**: Parties, Dates, Issues, Statutes.  
- **User**: Profile, Workspace, Queries, Saved judgments.  

---

## User Interface Design Principles
- Minimalist and lawyer-friendly.  
- First screen = **chat/search interface**.  
- Expandable panels for citations and timelines.  
- Visualizations: simple, clear, not overwhelming.  
- Mobile: focus on speed, clarity, and one-hand use.  

---

## Security Considerations
- Encryption at rest (cloud storage) and in transit (TLS).  
- Data isolation between users/teams.  
- Private AI endpoints → no provider training on legal data.  
- Role split: Admin (billing & user mgmt) vs Member.  

---

## Development Phases / Milestones
**Phase 1 (MVP, 3–4 months):**  
- Chatbot on judgments.  
- Citation strength analyzer (basic graph view).  
- Timeline/entity extraction.  
- User accounts (individual + small team).  
- Hybrid web + mobile companion.  

**Phase 2 (6–9 months):**  
- Saved judgments & dashboard.  
- Smart draft checker.  
- Expanded firm/team features.  

**Phase 3 (12+ months):**  
- AI Co-Counsel.  
- Predictive analytics.  
- Multilingual summarization.  
- Full case management system.  

---

## Potential Challenges and Solutions
- **Data cleaning/OCR errors:** Use preprocessing pipeline + manual QA on random samples.  
- **LLM hallucinations:** Combine retrieval-augmented generation (RAG) with strict citation linking.  
- **Scalability:** Start with single-server setup → move to distributed DB/search when adoption grows.  
- **Adoption resistance:** Use freemium model for easy entry, deliver “wow” value immediately.  

---

## Monetization Model
- **Freemium:**  
  - Free: limited chatbot queries.  
  - Pro (₹X/month): unlimited queries, citation graph, timelines.  
  - Team (₹Y/month/user): shared workspace, admin controls.  

---

## Future Expansion Possibilities
- Integrations with existing legal databases & court cause lists.  
- API access for law schools and researchers.  
- Contract analysis and drafting modules.  
- Expansion into other jurisdictions (UK, US, Singapore).  
- AI-powered oral argument assistant (voice queries in court).  

---

## Roadmap Diagram

```mermaid
flowchart TD
    A[Phase 1 - MVP] --> B[Phase 2 - Growth]
    B --> C[Phase 3 - Expansion]

    A --> A1[Chatbot on judgments]
    A --> A2[Citation strength analyzer]
    A --> A3[Timeline and entity extraction]
    A --> A4[User accounts - individual and small team]
    A --> A5[Hybrid web and mobile companion]

    B --> B1[Saved judgments and dashboard]
    B --> B2[Smart draft checker]
    B --> B3[Expanded firm and team features]

    C --> C1[AI Co-Counsel]
    C --> C2[Predictive analytics]
    C --> C3[Multilingual summarization]
    C --> C4[Full case management system]


