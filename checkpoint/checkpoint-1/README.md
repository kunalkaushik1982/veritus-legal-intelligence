# Veritus Legal Intelligence Platform

## Overview

Veritus is an AI-powered legal intelligence platform designed to revolutionize how legal professionals conduct research, analyze case law, and manage their practice. The platform combines AI-powered insights with structured legal data to reduce research time and improve legal outcomes.

## Features

### Core Features (MVP)
1. **AI Legal Chatbot** - Natural language queries on case law with contextual answers and linked citations
2. **Citation Strength Analyzer** - Citation graph visualizations and precedent strength scoring
3. **Timeline & Entity Extraction** - Converts long judgments into structured timelines and extracts key entities

### Technical Stack
- **Backend**: FastAPI with Python 3.11
- **Frontend**: Next.js with React and TypeScript
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: OpenAI GPT-4 with RAG (Retrieval Augmented Generation)
- **Vector Database**: Pinecone for semantic search
- **Authentication**: JWT-based authentication
- **Deployment**: Docker with docker-compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- Pinecone API key (optional for development)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd veritus
   ```

2. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Database Setup**
   ```bash
   cd backend
   alembic upgrade head
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Chatbot
- `POST /api/chatbot/query` - Process legal query
- `GET /api/chatbot/history` - Get query history
- `POST /api/chatbot/feedback/{query_id}` - Submit feedback

### Citations
- `POST /api/citations/analyze` - Analyze citation strength
- `GET /api/citations/network/{judgment_id}` - Get citation network
- `GET /api/citations/statistics/{judgment_id}` - Get citation statistics

### Judgments
- `GET /api/judgments/search` - Search judgments
- `GET /api/judgments/{judgment_id}` - Get judgment details
- `GET /api/judgments/` - List judgments

### Timelines
- `POST /api/timelines/extract` - Extract timeline from judgment
- `GET /api/timelines/judgment/{judgment_id}` - Get judgment timeline

## Database Schema

### Core Tables
- `users` - User accounts and profiles
- `teams` - Team/organization management
- `judgments` - Supreme Court judgments (50K+ records)
- `citations` - Citation relationships between judgments
- `entities` - Extracted legal entities
- `timelines` - Case timeline events
- `queries` - User query history

## AI Services

### Chatbot Service
- Uses OpenAI GPT-4 for natural language processing
- Implements RAG (Retrieval Augmented Generation)
- Semantic search through 50K+ judgments
- Context-aware responses with proper citations

### Citation Analyzer
- Analyzes citation strength and relationships
- Builds citation networks using NetworkX
- Calculates influence and authority scores
- Supports multiple citation types (relied upon, distinguished, overruled, etc.)

### Entity Extractor
- Extracts legal entities from judgment text
- Identifies parties, judges, statutes, dates, and legal principles
- Creates structured timelines from case events
- Uses regex patterns and AI for entity recognition

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS protection
- SQL injection prevention through ORM

## Deployment

### Production Deployment
1. Set up production environment variables
2. Configure SSL certificates
3. Set up database backups
4. Configure monitoring and logging
5. Deploy using Docker Swarm or Kubernetes

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@veritus.com
- Documentation: https://docs.veritus.com
- Issues: GitHub Issues

## Roadmap

### Phase 1 (Current MVP)
- ✅ AI-powered chatbot
- ✅ Citation analysis
- ✅ Timeline extraction
- ✅ User authentication
- ✅ Basic web interface

### Phase 2 (Next 3 months)
- [ ] Advanced search filters
- [ ] Team collaboration features
- [ ] Mobile app
- [ ] API rate limiting improvements
- [ ] Advanced analytics dashboard

### Phase 3 (6 months)
- [ ] Multi-language support
- [ ] Integration with legal databases
- [ ] Advanced AI features
- [ ] Enterprise features
- [ ] Third-party integrations