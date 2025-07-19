# WorkJournalMaker - Technical Specifications

## System Requirements

- **Python:** 3.9+
- **Operating Systems:** macOS, Linux (Windows compatibility may vary)
- **Network:** Internet connection required for AI service authentication (Google Gemini)

## Dependencies

### Core Dependencies
- `fastapi`: For the web framework
- `uvicorn`: For the ASGI server
- `sqlalchemy`: For database operations
- `aiosqlite`: For async SQLite access
- `google-genai`: For AI summarization

### Other Dependencies
- `pytest`
- `pytest-cov`
- `chardet`
- `boto3`
- `botocore`
- `PyYAML`
- `jinja2`
- `python-multipart`
- `greenlet`
- `python-dateutil`
- `aiofiles`

## Configuration

Configuration is managed through a `config.yaml` file, which is created by copying `config.yaml.example`. Key configuration options include:

- **AI Provider:** Set to `google_genai` (AWS Bedrock is not functional).
- **File Paths:** Define the base path for journal storage and output directories.
- **Logging:** Configure logging preferences for the application.
- **Environment Variables:** Override any configuration using `WJS_*` prefixed environment variables.