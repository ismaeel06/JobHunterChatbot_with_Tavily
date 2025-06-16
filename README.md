# AI-Powered Talent Scraper and Technical Term Simplifier

This repository contains two interconnected AI tools:

1. **Talent Scraper Chatbot**: An AI-powered agent that uses OpenAI and Tavily to find, evaluate, and explain talent profiles based on user requests.
2. **Technical Term Simplifier**: A hover/selection-based agent that explains technical terms in simple, non-technical language for better understanding.

## 🚀 Features

### Talent Scraper Chatbot

- Natural language processing for understanding talent requirements
- Web search capabilities for finding relevant talent profiles using Tavily
- AI-powered candidate evaluation and ranking
- Conversational interface with context awareness
- REST API for easy integration

### Technical Term Simplifier

- Select any technical term to get a simplified explanation
- User-friendly tooltips that position intelligently around the selected text
- Jargon-free explanations with everyday analogies
- In-memory caching for improved performance
- Seamless integration with any web content

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Tavily API key

## 🔧 Installation

1. Clone this repository

   ```bash
   git clone https://github.com/yourusername/talent-scraper-simplifier.git
   cd talent-scraper-simplifier
   ```

2. Create and activate a virtual environment

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   LOG_LEVEL=INFO
   ```

## 💻 Usage

### Starting the Server

Run the main application:

```bash
python app.py
```

This starts a FastAPI server with both the Talent Scraper and Technical Term Simplifier on port 8000.

### Running Tests

The project includes a comprehensive test suite for API endpoints. To run the tests:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_app.py

# Run with verbose output
pytest -v
```

Note: Some tests require valid API keys to be set in the environment variables.

### Deployment

To deploy the application to production:

1. Set up a production environment with Python 3.8+
2. Clone the repository and install dependencies

   ```bash
   git clone https://github.com/yourusername/talent-scraper-simplifier.git
   cd talent-scraper-simplifier
   pip install -r requirements.txt
   ```

3. Set up production environment variables (consider using a .env file not checked into git)

   ```
   OPENAI_API_KEY=your_production_openai_key
   TAVILY_API_KEY=your_production_tavily_key
   LOG_LEVEL=WARNING  # Set to WARNING or ERROR in production
   ```

4. Run the application with a production ASGI server like Gunicorn

   ```bash
   pip install gunicorn
   gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

5. For added security and performance in production, consider placing behind a reverse proxy like Nginx

### Using the Talent Scraper Chatbot

#### API Endpoints

- `POST /api/v1/chat` - Send a chat message to the talent scraper bot
- `POST /api/v1/reset-conversation` - Reset the conversation history
- `GET /api/v1/conversation-summary` - Get a summary of the current conversation

#### Example Request

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "Find me 3 senior React developers with AI experience",
        "session_id": "user123"
    }
)

print(response.json())
```

#### Command Line Testing

You can also use the included test client:

```bash
python chatbot_test_client.py
```

## 📁 Project Structure

```
├── app.py                     # Main application entry point
├── chatbot_api_legacy.py      # Legacy entry point for backward compatibility
├── chatbot_test_client.py     # Command-line test client
├── requirements.txt           # Project dependencies
├── talent_scraper_chatbot.py  # Core chatbot implementation
│
├── talent_scraper/            # Talent scraper package
│   ├── __init__.py
│   ├── api.py                 # FastAPI routes for talent scraping
│   └── models.py              # Data models for talent profiles
│
├── term_simplifier/           # Term simplifier package
│   ├── __init__.py
│   ├── api.py                 # FastAPI routes for term simplification
│   └── service.py             # Business logic for term simplification
│
├── static/                    # Static assets
│   ├── css/
│   │   └── simplifier.css     # Styles for the term simplifier
│   └── js/
│       └── simplifier.js      # Frontend script for term simplifier
│
├── templates/                 # HTML templates
│   └── demo.html              # Demo page for the term simplifier
│
└── tests/                     # Test suite
    ├── conftest.py            # Shared test fixtures
    ├── test_app.py            # Tests for main application
    ├── test_talent_scraper_api.py  # Tests for talent scraper API
    └── test_term_simplifier_api.py # Tests for term simplifier API
```

## 📝 Notes

### Migration and Refactoring

This project has been refactored from its original structure to follow better software engineering practices:

1. **Modular Package Structure**: Separated functionality into `talent_scraper` and `term_simplifier` packages
2. **Clear Separation of Concerns**: API routes, business logic, and data models are now in separate files
3. **Unified Entry Point**: `app.py` serves as the main application entry point
4. **Backward Compatibility**: `chatbot_api_legacy.py` maintains backward compatibility
5. **Comprehensive Testing**: Added test suite with pytest

The legacy `simplifier` directory has been deprecated and should be removed in a future update. All functionality has been migrated to the `term_simplifier` package.

### Using the Technical Term Simplifier

#### Demo Page

Access the demo page to see the term simplifier in action:

```
http://localhost:8000/simplifier-demo
```

Select any technical term on the page to see its simplified explanation.

#### API Endpoint

- `POST /simplifier/explain` - Get a simplified explanation of a technical term

```python
import requests

response = requests.post(
    "http://localhost:8000/simplifier/explain",
    json={"term": "API"}
)

print(response.json())
```

## 🏗️ Project Structure

```
talent-scraper-simplifier/
├── app.py                    # Main application entry point
├── requirements.txt          # Project dependencies
├── .env                      # Environment variables (not in repo)
├── README.md                 # This documentation
│
├── talent_scraper/           # Talent scraper module
│   ├── __init__.py
│   ├── models.py             # Data models
│   ├── chatbot.py            # Core chatbot logic
│   ├── api.py                # API endpoints for talent scraper
│   └── utils.py              # Utility functions
│
├── term_simplifier/          # Term simplifier module
│   ├── __init__.py
│   ├── api.py                # API endpoints for term simplifier
│   └── service.py            # Service for term explanation
│
├── static/                   # Static assets
│   ├── css/
│   │   └── simplifier.css    # Styles for term simplifier
│   └── js/
│       └── simplifier.js     # Client-side term simplifier logic
│
├── templates/                # HTML templates
│   └── demo.html             # Demo page for term simplifier
│
└── tests/                    # Test suite
    ├── test_talent_scraper.py
    └── test_term_simplifier.py
```

## 🛠️ Development

### Adding New Features

1. For the Talent Scraper:

   - Update the models in `talent_scraper/models.py`
   - Modify core logic in `talent_scraper/chatbot.py`
   - Add new API endpoints in `talent_scraper/api.py`

2. For the Term Simplifier:
   - Modify explanation logic in `term_simplifier/service.py`
   - Update the frontend in `static/js/simplifier.js`
   - Add new API endpoints in `term_simplifier/api.py`

## 🔒 Security Notes

- API keys are stored in environment variables and should never be committed to the repository
- The `.env` file is included in `.gitignore` to prevent accidental exposure of secrets
- Consider implementing rate limiting for production deployments

## 📝 License

[MIT License](LICENSE)

## 👥 Contributors

- Your Name (@yourusername)

## 🙏 Acknowledgements

This project uses the following technologies:

- OpenAI API for AI-powered analysis and explanations
- Tavily API for web search capabilities
- FastAPI for the backend framework
- JavaScript for client-side functionality
