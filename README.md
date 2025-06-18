# Work Journal Summarizer

A comprehensive Python application that generates intelligent weekly and monthly summaries of daily work journal text files using multiple LLM providers (AWS Bedrock Claude API [Untested and in development] or Google GenAI Gemini). The program automatically discovers journal files, processes content with advanced encoding detection, extracts key entities (projects, participants, tasks, themes), and generates professional markdown summaries with detailed processing statistics.

## ✨ Key Features

### 🔍 **Intelligent File Discovery**
- Automatically discovers journal files across complex directory structures
- Supports work-period-based organization with `week_ending_YYYY-MM-DD` directories
- Handles cross-year date ranges seamlessly
- Tracks missing files without stopping processing
- Configurable base paths and comprehensive discovery statistics

### 📝 **Advanced Content Processing**
- Automatic encoding detection with fallback strategies (UTF-8 → Latin-1 → CP1252)
- Content sanitization and normalization
- File size validation and memory management (configurable limits)
- Chronological file ordering and word/line count analysis
- Robust error handling with detailed recovery guidance

### 🤖 **AI-Powered Analysis**
- **Multi-Provider LLM Support**: Choose between AWS Bedrock Claude API or Google GenAI Gemini
- Automatic entity extraction: projects, participants, tasks, and themes
- Retry logic with exponential backoff and rate limiting
- Entity deduplication and normalization
- Comprehensive API usage statistics and performance tracking
- Seamless provider switching with unified interface

### 📊 **Smart Summary Generation**
- Weekly and monthly summary grouping with intelligent date handling
- LLM-powered narrative generation with professional tone
- Entity aggregation across time periods
- Quality controls and content validation
- Cross-year period handling

### 📄 **Professional Output Management**
- Clean markdown output with proper formatting
- Comprehensive metadata and processing statistics
- Timestamped file naming for organization
- Processing performance metrics and error reporting
- Markdown structure validation

### ⚙️ **Comprehensive Configuration Management**
- YAML/JSON configuration file support
- Environment variable overrides with precedence handling
- Configuration file auto-discovery in standard locations
- Validation and connection testing
- Example configuration generation

### 🔧 **Production-Grade Logging & Error Handling**
- Structured logging with rotating log files
- Categorized error handling with recovery guidance
- Real-time progress tracking with ETA calculations
- Graceful degradation strategies
- Dry run mode for configuration validation

## 🔧 LLM Provider Support

The Work Journal Summarizer supports multiple LLM providers, allowing you to choose the best option for your infrastructure and requirements:

### Supported Providers

| Provider | Status | Best For | Setup Complexity |
|----------|--------|----------|------------------|
| **Google GenAI** | ✅ Fully Supported | Development, testing, GCP environments | Low |
| **AWS Bedrock** | ⚠️ Experimental | AWS environments (requires Provisioned Throughput) | Medium |

### Quick Provider Selection

```yaml
# Choose your LLM provider
llm:
  provider: google_genai  # or "bedrock"

# Google GenAI Configuration (Recommended)
google_genai:
  project: your-gcp-project-id
  location: us-central1
  model: gemini-2.0-flash-001

# AWS Bedrock Configuration (Experimental)
bedrock:
  region: us-east-2
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
```

📖 **For detailed setup instructions, troubleshooting, and provider comparison, see the [LLM Provider Guide](docs/llm_providers.md)**

### Recent Updates

**🎉 Google GenAI Integration (Latest)**
- ✅ Full Google GenAI Gemini support with Vertex AI integration
- ✅ Unified LLM client architecture for seamless provider switching
- ✅ Comprehensive configuration management with YAML/JSON support
- ✅ Production-ready error handling and retry logic
- ✅ Complete test coverage for all provider integrations

## 🚀 Installation

### Prerequisites
- **Python 3.8+** - Required for modern async/await syntax and type hints
- **LLM Provider Access** - Choose one:
  - **Google GenAI** (Recommended): GCP project with Vertex AI API enabled
  - **AWS Bedrock** (Experimental): AWS account with Bedrock API access

### Quick Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd JournalSummarizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your chosen LLM provider**
   
   **For Google GenAI (Recommended):**
   ```bash
   # Set up Google Cloud authentication
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
   # Or use gcloud CLI
   gcloud auth application-default login
   ```
   
   **For AWS Bedrock (Experimental):**
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   ```

4. **Generate example configuration**
   ```bash
   python work_journal_summarizer.py --save-example-config config.yaml
   ```

5. **Test your setup**
   ```bash
   python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
   ```

## ⚙️ Configuration

### Configuration File Support
The application supports both YAML and JSON configuration files with automatic discovery:

**Standard locations searched:**
- `./config.yaml` or `./config.json`
- `~/.config/work-journal-summarizer/config.yaml`
- `~/.work-journal-summarizer.yaml`

### Example Configuration (`config.yaml`)
```yaml
# LLM Provider Selection
llm:
  provider: google_genai  # Choose: "google_genai" or "bedrock"

# Google GenAI Configuration (Recommended)
google_genai:
  project: your-gcp-project-id
  location: us-central1
  model: gemini-2.0-flash-001
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0

# AWS Bedrock Configuration (Experimental)
bedrock:
  region: us-east-2
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  aws_access_key_env: AWS_ACCESS_KEY_ID
  aws_secret_key_env: AWS_SECRET_ACCESS_KEY
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0

# File Processing Configuration
processing:
  base_path: ~/Desktop/worklogs/
  output_path: ~/Desktop/worklogs/summaries/
  max_file_size_mb: 50
  batch_size: 10
  rate_limit_delay: 1.0

# Logging Configuration
logging:
  level: INFO
  console_output: true
  file_output: true
  log_dir: ~/Desktop/worklogs/summaries/error_logs/
  max_file_size_mb: 10
  backup_count: 5
```

### Environment Variable Overrides
Override any configuration value using environment variables with `WJS_` prefix:
```bash
# LLM Provider Configuration
export WJS_LLM_PROVIDER=google_genai
export WJS_GOOGLE_GENAI_PROJECT=your-gcp-project
export WJS_GOOGLE_GENAI_LOCATION=us-central1
export WJS_GOOGLE_GENAI_MODEL=gemini-2.0-flash-001

# Or for AWS Bedrock
export WJS_LLM_PROVIDER=bedrock
export WJS_BEDROCK_REGION=us-west-2
export WJS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# General Configuration
export WJS_BASE_PATH=/custom/journal/path
export WJS_OUTPUT_PATH=/custom/output/path
export WJS_LOG_LEVEL=DEBUG
```

## 📖 Usage

### Basic Command Structure
```bash
python work_journal_summarizer.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --summary-type TYPE [OPTIONS]
```

### Required Arguments
- `--start-date` - Start date in YYYY-MM-DD format (inclusive)
- `--end-date` - End date in YYYY-MM-DD format (inclusive)
- `--summary-type` - Either `weekly` or `monthly`

### Configuration Options
- `--config PATH` - Path to configuration file (YAML or JSON)
- `--save-example-config PATH` - Generate example configuration file
- `--base-path PATH` - Override base directory for journal files
- `--output-dir PATH` - Override output directory for summaries

### Logging & Debug Options
- `--log-level LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-dir PATH` - Custom directory for log files
- `--no-console` - Disable console output (file logging only)
- `--dry-run` - Validate configuration without processing files

### 💡 Usage Examples

#### Basic Usage
```bash
# Generate weekly summaries for May 2024
python work_journal_summarizer.py --start-date 2024-05-01 --end-date 2024-05-30 --summary-type weekly

# Generate monthly summaries for entire year
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-12-31 --summary-type monthly
```

#### Configuration Management
```bash
# Generate and customize configuration file
python work_journal_summarizer.py --save-example-config my-config.yaml
# Edit my-config.yaml with your preferences

# Use custom configuration
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-31 --summary-type monthly --config my-config.yaml

# Override configuration with CLI arguments
python work_journal_summarizer.py --config my-config.yaml --start-date 2024-01-01 --end-date 2024-01-31 --summary-type weekly --output-dir /custom/output --log-level DEBUG
```

#### Advanced Usage
```bash
# Cross-year processing with custom paths
python work_journal_summarizer.py --start-date 2024-12-30 --end-date 2025-01-03 --summary-type weekly --base-path /work/journals/ --output-dir /work/summaries/

# Dry run for configuration validation
python work_journal_summarizer.py --start-date 2024-05-01 --end-date 2024-05-30 --summary-type weekly --config my-config.yaml --dry-run

# Debug mode with detailed logging
python work_journal_summarizer.py --start-date 2024-05-01 --end-date 2024-05-30 --summary-type weekly --log-level DEBUG --log-dir /tmp/debug-logs/

# Silent processing (file logging only)
python work_journal_summarizer.py --start-date 2024-05-01 --end-date 2024-05-30 --summary-type weekly --no-console
```

#### Environment Variable Configuration
```bash
# Set LLM provider configuration
export WJS_LLM_PROVIDER="google_genai"
export WJS_GOOGLE_GENAI_PROJECT="your-gcp-project"
export WJS_GOOGLE_GENAI_LOCATION="us-central1"

# Set processing configuration
export WJS_BASE_PATH="/work/journals"
export WJS_OUTPUT_PATH="/work/summaries"
export WJS_LOG_LEVEL="DEBUG"

# Run with environment configuration
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-31 --summary-type monthly
```

### 📋 Expected Directory Structure

The application expects journal files organized in this structure:
```
~/Desktop/worklogs/
├── worklogs_2024/
│   ├── worklogs_2024-04/
│   │   └── week_ending_2024-04-19/        # End date of work period
│   │       ├── worklog_2024-04-15.txt
│   │       ├── worklog_2024-04-16.txt
│   │       ├── worklog_2024-04-17.txt
│   │       ├── worklog_2024-04-18.txt
│   │       └── worklog_2024-04-19.txt
│   └── worklogs_2024-12/
│       └── week_ending_2025-01-03/        # Cross-year work period
│           ├── worklog_2024-12-30.txt
│           └── worklog_2024-12-31.txt
└── worklogs_2025/
    └── worklogs_2025-01/
        └── week_ending_2025-01-03/        # Same work period, different year
            ├── worklog_2025-01-01.txt
            ├── worklog_2025-01-02.txt
            └── worklog_2025-01-03.txt
```

**Key Features:**
- `week_ending_YYYY-MM-DD` uses the **end date** of your work period
- Files are organized by their actual date in year/month directories
- Cross-year work periods are handled seamlessly
- Missing files are tracked but don't stop processing

### 📄 Output Structure

Generated summaries are saved with timestamped filenames:
```
~/Desktop/worklogs/summaries/
├── weekly_summary_2024-04-01_to_2024-04-30_20250616_121600.md
├── monthly_summary_2024-01-01_to_2024-12-31_20250616_121700.md
└── error_logs/
    └── journal_summarizer_20250616_121600.log
```

### 🆘 Getting Help
```bash
python work_journal_summarizer.py --help
```

## 📊 Sample Output

### Dry Run Mode (Configuration Validation)
```
✅ Work Journal Summarizer - Phase 8
==================================================
Start Date: 2024-05-01
End Date: 2024-05-30
Summary Type: weekly
Base Path: ~/Desktop/worklogs/
Output Path: ~/Desktop/worklogs/summaries/
Date Range: 30 days
LLM Provider: google_genai
Model: gemini-2.0-flash-001

🔍 DRY RUN MODE - Configuration Validation
==================================================
✅ Date range valid: 2024-05-01 to 2024-05-30 (30 days)
✅ Base path accessible: /Users/username/Desktop/worklogs
✅ Output path accessible: /Users/username/Desktop/worklogs/summaries
📊 Estimated weekly summaries: 5
✅ Google GenAI credentials found
✅ Google GenAI API connection successful
📝 GCP Project: your-gcp-project-id
📍 Location: us-central1
🤖 Model: gemini-2.0-flash-001
📁 Max file size: 50 MB
📝 Log level: INFO
📁 Log directory: /Users/username/Desktop/worklogs/summaries/error_logs
📄 Log file: journal_summarizer_20250616_160107.log

🎯 Dry run complete - configuration validated
```

### Full Processing Output
```
✅ Work Journal Summarizer - Phase 8
==================================================
Start Date: 2024-05-01
End Date: 2024-05-30
Summary Type: weekly
Base Path: ~/Desktop/worklogs/
Output Path: ~/Desktop/worklogs/summaries/
Date Range: 30 days
LLM Provider: google_genai
Model: gemini-2.0-flash-001

🔍 Phase 2: Discovering journal files...
📊 File Discovery Results:
------------------------------
Total files expected: 22
Files found: 20
Files missing: 2
Discovery success rate: 90.9%
Processing time: 0.045 seconds

📁 Found Files (showing first 5):
  1. /Users/username/Desktop/worklogs/worklogs_2024/worklogs_2024-05/week_ending_2024-05-03/worklog_2024-05-01.txt
  2. /Users/username/Desktop/worklogs/worklogs_2024/worklogs_2024-05/week_ending_2024-05-03/worklog_2024-05-02.txt
  3. /Users/username/Desktop/worklogs/worklogs_2024/worklogs_2024-05/week_ending_2024-05-03/worklog_2024-05-03.txt
  4. /Users/username/Desktop/worklogs/worklogs_2024/worklogs_2024-05/week_ending_2024-05-10/worklog_2024-05-06.txt
  5. /Users/username/Desktop/worklogs/worklogs_2024/worklogs_2024-05/week_ending_2024-05-10/worklog_2024-05-07.txt
  ... and 15 more files

📝 Phase 3: Processing file content...
📊 Content Processing Results:
------------------------------
Files processed: 20
Successfully processed: 20
Failed to process: 0
Success rate: 100.0%
Total content size: 45,678 bytes
Total words extracted: 7,234
Processing time: 0.156 seconds
Average processing speed: 128.2 files/second

📄 Sample Processed Content (first file):
----------------------------------------
File: worklog_2024-05-01.txt
Date: 2024-05-01
Encoding: utf-8
Word count: 342
Line count: 28
Processing time: 0.008s
Content preview: Today I worked on the quarterly planning project with Sarah and Mike. We reviewed the budget allocations and identified three key areas for improvement...

🤖 Phase 4: Analyzing content with LLM API...
📊 Analyzing 20 files for entity extraction...
  Processing file 1/20: worklog_2024-05-01.txt
  Processing file 2/20: worklog_2024-05-02.txt
  ...
    Progress: 20/20 files analyzed

📊 LLM API Analysis Results:
------------------------------
Total API calls: 20
Successful calls: 20
Failed calls: 0
Success rate: 100.0%
Total API time: 28.456 seconds
Average response time: 1.423 seconds

🎯 Entity Extraction Summary:
------------------------------
Unique projects identified: 8
Unique participants identified: 12
Total tasks extracted: 45
Major themes identified: 6

📋 Sample Projects (showing first 5):
  1. Quarterly Planning Initiative
  2. Customer Onboarding System
  3. Database Migration Project
  4. Marketing Campaign Analysis
  5. Security Audit Preparation
  ... and 3 more projects

👥 Sample Participants (showing first 5):
  1. Sarah Johnson
  2. Mike Chen
  3. Alex Rodriguez
  4. Jennifer Kim
  5. David Thompson
  ... and 7 more participants

📝 Phase 5: Generating intelligent summaries...
📊 Summary Generation Results:
------------------------------
Total periods processed: 5
Successful summaries: 5
Failed summaries: 0
Success rate: 100.0%
Total entries processed: 20
Generation time: 12.345 seconds
Average summary length: 287 words

📋 Generated Summaries:
==================================================

1. Week of May 1-3, 2024
   Date Range: 2024-05-01 to 2024-05-03
   Journal Entries: 3
   Word Count: 1,024
   Generation Time: 2.456s

   📋 Projects: Quarterly Planning Initiative, Customer Onboarding System, Database Migration Project
   👥 Participants: Sarah Johnson, Mike Chen, Alex Rodriguez
   🎨 Themes: Strategic Planning, System Integration, Performance Optimization

   📄 Summary:
   ----------------------------------------
   This week focused primarily on strategic planning and system improvements.
   The quarterly planning initiative made significant progress with Sarah and
   Mike, where we completed the budget review and identified key improvement
   areas. The customer onboarding system received attention with Alex leading
   the integration testing phase. Database migration planning continued with
   performance optimization being a central theme throughout all activities.
   
   Key accomplishments include finalizing Q2 budget allocations, completing
   initial onboarding system tests, and establishing migration timelines.
   Next week will focus on implementation of the identified improvements.
   ========================================

📄 Phase 6: Generating markdown output...
📊 Output Generation Results:
------------------------------
Output file: /Users/username/Desktop/worklogs/summaries/weekly_summary_2024-05-01_to_2024-05-30_20250616_160234.md
File size: 15,432 bytes
Generation time: 0.234 seconds
Sections count: 7
Metadata included: Yes
Validation passed: Yes

🎉 Work Journal Summarizer - All Phases Complete!
==================================================
📁 Summary file created: /Users/username/Desktop/worklogs/summaries/weekly_summary_2024-05-01_to_2024-05-30_20250616_160234.md
📊 Total processing time: 41.24 seconds
📈 Files processed: 20/22
🤖 API calls made: 20/20
📋 Summaries generated: 5

Your professional work journal summary is ready!
```

### Generated Markdown Summary Sample
The application generates professional markdown summaries like this:

```markdown
# Weekly Summary: 2024-05-01 to 2024-05-30

*Generated on 2025-06-16 at 16:02:34*

## Week of May 1-3, 2024

**Date Range:** May 1, 2024 - May 3, 2024
**Journal Entries:** 3 files processed
**Key Projects:** Quarterly Planning Initiative, Customer Onboarding System
**Participants:** Sarah Johnson, Mike Chen, Alex Rodriguez

### Summary
This week focused primarily on strategic planning and system improvements. The quarterly planning initiative made significant progress with Sarah and Mike, where we completed the budget review and identified key improvement areas...

## Processing Statistics

- **Files Processed:** 20 out of 22 expected files
- **Processing Success Rate:** 90.9%
- **API Calls Made:** 20 successful calls
- **Total Processing Time:** 41.24 seconds
- **Unique Projects Identified:** 8
- **Unique Participants:** 12
- **Major Themes:** 6
```

## Validation Rules

### Date Format
- Must be in YYYY-MM-DD format exactly
- Invalid formats will be rejected with clear error messages
- Examples of valid dates: `2024-04-01`, `2024-12-31`
- Examples of invalid dates: `2024/04/01`, `2024.04.01`, `2024-4-1`

### Date Range
- End date must be **after** start date (minimum 2-day range)
- Same start and end dates are not allowed
- Cross-year ranges are supported
- Invalid dates (like Feb 30) are rejected

### Summary Type
- Must be exactly "weekly" or "monthly" (case-sensitive)
- Invalid values like "daily", "yearly", "WEEKLY" are rejected

## Error Handling

The program provides clear, specific error messages for common issues:

### Date Format Errors
```
Invalid date format for start-date. Expected YYYY-MM-DD, got: 2024/04/01
```

### Date Range Errors
```
End date must be after start date. Start: 2024-04-30, End: 2024-04-01
```

### Summary Type Errors
```
Invalid summary type. Must be 'weekly' or 'monthly', got: 'daily'
```

### Invalid Dates
```
Invalid date for end-date: 2024-02-30. Please check that the date exists (e.g., Feb 30 is invalid).
```

## 🔧 Troubleshooting

### Common Issues

#### LLM Provider Connection Issues
```bash
# Test your LLM provider configuration
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
```

**Google GenAI Issues:**
- Ensure your GCP project has Vertex AI API enabled
- Verify authentication: `gcloud auth application-default login`
- Check project ID and location in configuration
- See [LLM Provider Guide](docs/llm_providers.md) for detailed setup

**AWS Bedrock Issues:**
- Verify AWS credentials are configured
- Ensure Bedrock API access is enabled in your region
- Check if model requires Provisioned Throughput
- See [LLM Provider Guide](docs/llm_providers.md) for detailed setup

#### File Discovery Issues
```bash
# Check if your directory structure matches expected format
ls -la ~/Desktop/worklogs/worklogs_2024/worklogs_2024-*/week_ending_*/
```

#### Configuration Issues
```bash
# Generate a fresh example configuration
python work_journal_summarizer.py --save-example-config debug-config.yaml
```

📖 **For comprehensive troubleshooting, see the [LLM Provider Guide](docs/llm_providers.md)**

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=work_journal_summarizer --cov-report=term-missing

# Run tests with HTML coverage report
pytest --cov=work_journal_summarizer --cov-report=html

# Run specific test class
pytest tests/test_cli.py::TestCLIArguments -v
```

### Test Coverage

The project maintains comprehensive test coverage with test suites covering:

**Core Functionality:**
- ✅ CLI argument parsing for both weekly and monthly summaries
- ✅ Date format validation (various invalid formats)
- ✅ Date range validation (end before start, same dates)
- ✅ Summary type validation (invalid values, case sensitivity)
- ✅ Missing required arguments and help message content
- ✅ Leap year handling and cross-year date ranges

**LLM Provider Integration:**
- ✅ Google GenAI client functionality and error handling
- ✅ AWS Bedrock client functionality (experimental)
- ✅ Unified LLM client provider switching
- ✅ Configuration management and validation
- ✅ API retry logic and rate limiting
- ✅ Provider-specific authentication and connection testing

**System Integration:**
- ✅ File discovery across complex directory structures
- ✅ Content processing with encoding detection
- ✅ Summary generation and markdown output
- ✅ Logging system and error handling
- ✅ Dry run functionality and configuration validation

### Project Structure

```
JournalSummarizer/
├── work_journal_summarizer.py    # Main CLI module with Phase 8 integration
├── file_discovery.py             # File discovery engine (Phase 2)
├── content_processor.py          # Content processing system (Phase 3)
├── llm_client.py                 # Legacy LLM client (Phase 4)
├── unified_llm_client.py         # Multi-provider LLM client (Phase 8)
├── bedrock_client.py             # AWS Bedrock client implementation
├── google_genai_client.py        # Google GenAI client implementation
├── summary_generator.py          # Summary generation system (Phase 5)
├── output_manager.py             # Output management system (Phase 6)
├── logger.py                     # Comprehensive error handling & logging (Phase 7)
├── config_manager.py             # Configuration management system
├── config.yaml.example           # Example configuration file
├── docs/
│   └── llm_providers.md          # LLM provider setup and troubleshooting guide
├── tests/                        # Test directory
│   ├── test_cli.py              # CLI tests (Phase 1)
│   ├── test_file_discovery.py   # File discovery tests (Phase 2)
│   ├── test_content_processor.py # Content processing tests (Phase 3)
│   ├── test_llm_client.py       # Legacy LLM API tests (Phase 4)
│   ├── test_unified_llm_client.py # Multi-provider LLM tests
│   ├── test_bedrock_client.py   # AWS Bedrock client tests
│   ├── test_google_genai_client.py # Google GenAI client tests
│   ├── test_summary_generator.py # Summary generation tests (Phase 5)
│   ├── test_output_manager.py   # Output management tests (Phase 6)
│   ├── test_logger.py           # Logger tests (Phase 7)
│   ├── test_config_manager.py   # Configuration management tests
│   ├── test_integration_llm_providers.py # LLM provider integration tests
│   └── test_integration_logging.py # Integration tests (Phase 7)
├── requirements.txt             # Project dependencies
├── README.md                    # This file
├── .gitignore                   # Python gitignore
└── implementation_plans/        # Implementation documentation
    ├── work_journal_summarizer_implementation_blueprint.md
    ├── google_genai_implementation_blueprint.md
    └── phase1_implementation_plan.md
```

**Key Features:**
- `week_ending_YYYY-MM-DD` uses the **end date** of your work period (not calendar Sunday)
- Files are organized by their actual date in year/month directories
- Cross-year work periods are handled seamlessly
- Missing files are tracked but don't stop processing

## Expected Output Structure 

```
~/Desktop/worklogs/summaries/
├── weekly_summary_2024-04-01_to_2024-04-30_20250616_121600.md
├── monthly_summary_2024-01-01_to_2024-12-31_20250616_121700.md
└── error_logs/
    └── journal_summarizer_20250616_121600.log
```

## Contributing

This project follows Test-Driven Development (TDD) principles:

1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor for clarity and maintainability
4. Maintain 100% test coverage
5. Add comprehensive docstrings and type hints
