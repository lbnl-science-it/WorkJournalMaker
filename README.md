# Work Journal Maker - Installation Guide -- ALPHA RELEASE SOME FUNCTIONALITY BROKEN 

A hybrid work journal application combining a web interface with CLI functionality for managing journal entries and generating AI-powered insights. Built with Python 3.9+, FastAPI, SQLite, and Google Gemini AI integration.

## System Requirements

- **Python**: 3.9+ required
- **Operating Systems**: Primarily tested on macOS/Linux (Windows compatibility may vary)
- **Dependencies**: May require additional system packages for full functionality
- **Network**: Internet connection required for AI service authentication
- **Storage**: Minimal local storage for SQLite database

## Installation

### 1. Repository Setup
```bash
git clone <repository-url>
cd WorkJournalMaker
```

### 2. Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Key dependencies include FastAPI, SQLite, SQLAlchemy, and google-genai for AI integration.

### 3. Configuration Setup
```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` to configure:
- AI provider settings (use Google Gemini - see below)
- File paths for journal storage (`~/Desktop/worklogs/` by default)
- Output directories for summaries (`~/Desktop/worklogs/summaries/` by default)
- Logging preferences

### 4. AI Service Authentication

**⚠️ Important**: AWS Bedrock integration is currently broken. Use Google Gemini instead.

**Google Gemini Setup** (Required ONLY IF you want summarization):
1. Create a Google Cloud Platform project
2. Enable the Generative AI API
3. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
4. Update `config.yaml`:
   ```yaml
   llm:
     provider: google_genai
   google_genai:
     project: your-gcp-project-id
     location: us-central1
     model: gemini-2.0-flash-001
   ```

**AWS Bedrock** (Currently Unavailable):
While AWS Bedrock is configured in the application, it's currently non-functional. Avoid using `provider: bedrock` in your configuration.

### 5. Database Initialization
The SQLite database initializes automatically on first run. No manual setup required.

## Running the Application

### Web Interface (Recommended for New Users)
```bash
python -m web.app
```
Access at: http://localhost:8000

The web interface provides an intuitive way to create and manage journal entries, view summaries, and configure settings.

### CLI Commands (Advanced Features)
After familiarizing yourself with the web interface, explore CLI functionality:

- **Create entries**: Process and import journal files
- **Generate summaries**: Bulk summarization of existing entries  
- **Import files**: Batch import from various file formats
- **Export data**: Extract journal data for backup or analysis

## Configuration Customization

### Default Paths
- Working now (2025-07-10)
- **Input**: `~/Desktop/worklogs/` (journal files)
- **Output**: `~/Desktop/worklogs/summaries/` (generated summaries)
- **Logs**: `~/Desktop/worklogs/summaries/error_logs/`

### Work Week Settings
- CURRENTLY BROKEN: Fixed on M-F work week. 
Modify work week definitions and date ranges through the web interface settings panel or by editing the configuration file.

### Environment Variables
Override any configuration using `WJS_*` prefixed environment variables:
```bash
export WJS_LLM_PROVIDER=google_genai
export WJS_BASE_PATH=/custom/journal/path
export WJS_LOG_LEVEL=DEBUG
```

## Troubleshooting

**AI Authentication Issues**: Verify Google Cloud credentials with `gcloud auth list` and ensure the Generative AI API is enabled in your GCP project.

**Path Configuration Problems**: Check directory permissions and ensure specified paths exist or can be created by the application.

**Port Conflicts**: If port 8000 is unavailable, the application will attempt to use alternative ports automatically.

## Getting Started

1. Start with the web interface for ease of use
2. Create your first journal entry through the web UI
3. Explore AI summarization features
4. Graduate to CLI commands for bulk processing and advanced workflows

The application stores all data locally while leveraging cloud AI services only for content analysis and summarization.