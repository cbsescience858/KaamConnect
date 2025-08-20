# KaamConnect

A comprehensive job marketplace platform connecting clients with workers, featuring real-time chat, language support, and intelligent job matching.

## Features

- User Registration and Authentication
- Job Posting and Application System
- Real-time Chat (Similar to Telegram)
- Multi-language Support (English, Hindi, Tamil, Telugu, Kannada, Bangla, Marathi, Gujarati)
- Live Translation
- Skill Tag System with ML-based Job Matching
- Location Sharing
- Phone Call Integration
- Money Offer System

## Tech Stack

- Backend: Flask, FastAPI
- Database: SQLAlchemy
- Real-time Communication: Socket.IO
- Machine Learning: Transformers (Hugging Face)
- Frontend: Modern JavaScript/TypeScript
- Authentication: JWT

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:
```bash
flask db init
flask db migrate
flask db upgrade
```

4. Run the application:
```bash
python app.py
```

## Project Structure

```
kaamconnect/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── frontend/
├── migrations/
├── tests/
└── static/
