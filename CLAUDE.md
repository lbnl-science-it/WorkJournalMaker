# Work Journal Maker - CLAUDE.md
REMEMBER YOU SHOULD HAVE THE DEMEANOR OF MR SPOCK FROM STAR TREK

## Project Overview
**Work Journal Maker** is a production-grade Python application that generates intelligent weekly and monthly summaries of daily work journal text files using multiple LLM providers. The project includes both a command-line interface and a FastAPI-based web application with a comprehensive backend system.

## Key Features

### Core Functionality
- **Intelligent Summarization**: Generates weekly and monthly summaries from daily work journal entries
- **Multi-Provider LLM Support**: Unified architecture supporting Google GenAI and AWS Bedrock
- **File Discovery Engine v2.0**: Revolutionary directory-first approach with 95%+ success rate
- **Web Interface**: Complete FastAPI-based web application with frontend
- **Production-Ready**: Comprehensive error handling, logging, and configuration management

### Architecture Components
- **CLI Application**: `work_journal_summarizer.py` - Main command-line interface
- **Web Application**: `web/app.py` - FastAPI-based web interface
- **File Discovery**: `file_discovery.py` - Advanced file discovery system
- **Content Processing**: `content_processor.py` - Text processing and analysis
- **LLM Integration**: `unified_llm_client.py` - Multi-provider LLM client
- **Configuration**: `config_manager.py` - Unified configuration management
- **Logging**: `logger.py` - Comprehensive logging system

## Technology Stack

### Core Dependencies
- **Python 3.8+**: Modern async/await syntax support
- **FastAPI**: Web framework for API endpoints
- **SQLAlchemy**: Database ORM with async support
- **pytest**: Comprehensive testing framework
- **Google GenAI**: Google's Generative AI client
- **AWS Bedrock**: Amazon's LLM service (via boto3)
- **PyYAML**: Configuration file parsing

### Web Technologies
- **Jinja2**: Template engine for HTML rendering
- **Uvicorn**: ASGI server for production deployment
- **SQLite**: Database for journal indexing
- **Static Assets**: CSS, JavaScript, and HTML templates

## Project Structure

```
WorkJournalMaker/
├── Core CLI Application
│   ├── work_journal_summarizer.py    # Main CLI interface
│   ├── file_discovery.py             # File discovery engine
│   ├── content_processor.py          # Content processing
│   ├── unified_llm_client.py         # Multi-provider LLM client
│   ├── config_manager.py             # Configuration management
│   └── logger.py                     # Logging system
├── LLM Provider Clients
│   ├── google_genai_client.py        # Google GenAI implementation
│   ├── bedrock_client.py             # AWS Bedrock implementation
│   └── llm_data_structures.py        # Shared data structures
├── Web Application
│   ├── web/
│   │   ├── app.py                    # FastAPI application
│   │   ├── database.py               # Database management
│   │   ├── middleware.py             # Request middleware
│   │   ├── api/                      # API endpoints
│   │   │   ├── calendar.py           # Calendar functionality
│   │   │   ├── entries.py            # Journal entries
│   │   │   ├── settings.py           # Configuration
│   │   │   └── summarization.py      # Summary generation
│   │   ├── services/                 # Business logic
│   │   │   ├── calendar_service.py   # Calendar operations
│   │   │   ├── entry_manager.py      # Entry management
│   │   │   └── web_summarizer.py     # Web summarization
│   │   ├── static/                   # Frontend assets
│   │   │   ├── css/                  # Stylesheets
│   │   │   └── js/                   # JavaScript modules
│   │   └── templates/                # HTML templates
│   │       ├── dashboard.html        # Main dashboard
│   │       ├── calendar.html         # Calendar view
│   │       └── settings.html         # Settings page
├── Testing & Validation
│   ├── tests/                        # Comprehensive test suite
│   ├── validate_llm_providers.py     # System validation
│   └── debug_file_discovery.py       # Discovery diagnostics
└── Documentation
    ├── README.md                     # Project documentation
    ├── docs/llm_providers.md         # LLM setup guide
    └── implementation_plans/         # Technical specifications
```

## Development Guidelines

### Running the Application

#### CLI Usage
```bash
# Basic weekly summary
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-31 --summary-type weekly

# Monthly summary with custom paths
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-12-31 --summary-type monthly --base-path /path/to/journals

# Dry run for configuration validation
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-31 --summary-type weekly --dry-run
```

#### Web Application
```bash
# Start the web server
cd web
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Or use the main app
python -m web.app
```

### Configuration Management

The application uses a unified configuration system with YAML/JSON support:

```yaml
# config.yaml
llm:
  provider: google_genai  # or "bedrock"

google_genai:
  project: your-gcp-project-id
  location: us-central1
  model: gemini-2.0-flash-001

processing:
  base_path: ~/Desktop/worklogs/
  output_path: ~/Desktop/worklogs/summaries/
  max_file_size_mb: 50

logging:
  level: INFO
  console_output: true
  file_output: true
```

### Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/test_file_discovery_v2_*.py -v
pytest tests/test_*_llm_*.py -v
pytest tests/test_web_*.py -v
```

### Common Development Tasks

#### Adding New LLM Providers
1. Create a new client class in the pattern of `google_genai_client.py`
2. Implement the required interface methods
3. Add provider configuration to `config_manager.py`
4. Update `unified_llm_client.py` to include the new provider
5. Add comprehensive tests

#### Extending Web API
1. Create new endpoint modules in `web/api/`
2. Add corresponding service classes in `web/services/`
3. Update database models if needed in `web/models/`
4. Add frontend components in `web/static/`
5. Create HTML templates in `web/templates/`

#### File Discovery Improvements
1. Modify `file_discovery.py` for new patterns
2. Update discovery logic in the main class
3. Add validation and error handling
4. Update tests to cover new scenarios

### Expected Directory Structure

The application expects journal files in this structure:
```
~/Desktop/worklogs/
├── worklogs_2024/
│   ├── worklogs_2024-04/
│   │   └── week_ending_2024-04-19/
│   │       ├── worklog_2024-04-15.txt
│   │       ├── worklog_2024-04-16.txt
│   │       └── worklog_2024-04-17.txt
│   └── worklogs_2024-12/
│       └── week_ending_2025-01-03/
│           ├── worklog_2024-12-30.txt
│           └── worklog_2024-12-31.txt
```

### Error Handling and Logging

The application includes comprehensive error handling:
- Structured logging with rotating log files
- Categorized error handling (file system, API, configuration)
- Graceful degradation for missing files
- Detailed error reporting with recovery guidance

### Performance Considerations

- **File Discovery**: Optimized for large date ranges (year-long processing in <1 second)
- **Memory Management**: Configurable file size limits and batch processing
- **API Rate Limiting**: Built-in rate limiting and retry logic
- **Database**: Efficient SQLite usage with proper indexing

## Troubleshooting

### Common Issues

1. **File Discovery Problems**
   - Check directory structure matches expected format
   - Verify file permissions
   - Use `debug_file_discovery.py` for diagnostics

2. **LLM Provider Issues**
   - Validate API credentials and configuration
   - Use `validate_llm_providers.py` for comprehensive testing
   - Check provider-specific setup guides

3. **Web Application Issues**
   - Verify database initialization
   - Check port availability
   - Review middleware configuration

### Validation Tools

```bash
# Complete system validation
python validate_llm_providers.py

# Web application testing
python -m pytest tests/test_web_*.py -v

# File discovery diagnostics
python debug_file_discovery.py
```

## Code Quality Standards

- **Type Hints**: All functions must have complete type annotations
- **Docstrings**: Comprehensive docstrings for all public functions
- **Error Handling**: Proper exception handling for all external calls
- **Logging**: Structured logging for all significant operations
- **Testing**: Comprehensive test coverage for all components

## Contributing

1. Follow TDD principles - write tests first
2. Maintain comprehensive test coverage
3. Add proper type hints and docstrings
4. Update documentation for new features
5. Validate changes with the provided testing tools

## Security Considerations

- No secrets or API keys should be committed to the repository
- Use environment variables for sensitive configuration
- Implement proper input validation and sanitization
- Follow secure coding practices for web endpoints

---

This project represents a production-ready work journal summarization system with both CLI and web interfaces, designed for extensibility and maintainability.
Before running any code or tests, make sure that the `pyenv` virtual environment `WorkJournal` is active.
