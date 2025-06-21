# LLM Provider Guide

A comprehensive guide to configuring and using different LLM providers with the Work Journal Summarizer.

## Overview

The Work Journal Summarizer supports multiple LLM providers for content analysis and summarization. This multi-provider architecture allows you to choose the best option for your specific needs, infrastructure, and cost requirements.

### Supported Providers

| Provider | Service | Models | Best For |
|----------|---------|--------|----------|
| **AWS Bedrock** | Amazon Bedrock | Claude 3.5 Sonnet, Claude 3 Sonnet, Claude 3 Haiku | Experimental (needs testing with Provisioned Throughput), AWS infrastructure |
| **Google GenAI** | Google Cloud Vertex AI | Gemini 2.0 Flash, Gemini Pro | Development/testing, GCP infrastructure |

## Quick Start

### 1. Choose Your Provider

Set the provider in your configuration file:

```yaml
llm:
  provider: bedrock  # or "google_genai"
```

Or use an environment variable:
```bash
export WJS_LLM_PROVIDER=google_genai
```

### 2. Configure Provider Settings

Each provider requires specific configuration. See the detailed setup sections below.

### 3. Test Your Configuration

Always test your setup with a dry run:
```bash
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
```

## Google GenAI Provider

### Overview

Google GenAI provides access to Gemini models through Google Cloud's Vertex AI service. This is currently the only tested and fully supported provider for the tool. 

### Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **Application Default Credentials** configured
3. **Vertex AI API** enabled in your project
4. **Appropriate IAM Permissions** for Vertex AI

### Step-by-Step Setup

#### 1. Create and Configure GCP Project

1. Create a new project or use existing one:
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. Enable required APIs:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable generativelanguage.googleapis.com
   ```

#### 2. Set Up Authentication

**Option A: Application Default Credentials (Recommended)**
```bash
gcloud auth application-default login
```

**Option B: Service Account Key**
1. Create service account:
   ```bash
   gcloud iam service-accounts create journal-summarizer
   ```

2. Grant necessary permissions:
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:journal-summarizer@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. Create and download key:
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=journal-summarizer@your-project-id.iam.gserviceaccount.com
   ```

4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

#### 3. Configure the Application

**Configuration File (`config.yaml`):**
```yaml
llm:
  provider: google_genai

google_genai:
  project: your-gcp-project-id
  location: us-central1
  model: gemini-2.0-flash-001
```

**Environment Variables:**
```bash
export WJS_LLM_PROVIDER=google_genai
export WJS_GOOGLE_GENAI_PROJECT=your-gcp-project-id
export WJS_GOOGLE_GENAI_LOCATION=us-central1
export WJS_GOOGLE_GENAI_MODEL=gemini-2.0-flash-001
```

### Available Models

| Model | Model ID | Use Case | Cost |
|-------|----------|----------|------|
| **Gemini 2.0 Flash** | `gemini-2.0-flash-001` | Fast responses, good performance | Lower |
| **Gemini Pro** | `gemini-pro` | Balanced performance | Medium |

### Troubleshooting

**"Authentication Error":**
- Verify Application Default Credentials are set up
- Check service account has proper permissions
- Ensure GOOGLE_APPLICATION_CREDENTIALS points to valid key file

**"API Not Enabled" Error:**
- Enable Vertex AI API in your project
- Enable Generative Language API if needed
- Wait a few minutes for API activation

**"Project Not Found" Error:**
- Verify project ID is correct
- Ensure you have access to the project
- Check project is active and billing is enabled

## AWS Bedrock Provider

### Overview

AWS Bedrock provides access to Claude models through Amazon's managed service. THIS IS UNTESTED LIVE.  

### Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS Credentials** configured (Access Key ID and Secret Access Key)
3. **Model Access** granted in AWS Bedrock Console
4. **Appropriate IAM Permissions** for Bedrock service

### Step-by-Step Setup

#### 1. Configure AWS Credentials

**Option A: Environment Variables (Recommended)**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
```

**Option B: AWS CLI Configuration**
```bash
aws configure
```

**Option C: IAM Roles (for EC2/Lambda)**
- Attach appropriate IAM role to your compute instance

#### 2. Request Model Access

1. Navigate to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Go to **"Model access"** in the left sidebar
3. Find **"Anthropic Claude 3.5 Sonnet"** or your preferred model
4. Click **"Request model access"**
5. Fill out the use case form:
   - **Use case**: "Work journal analysis and summarization"
   - **Description**: "Automated analysis of daily work journals to extract projects, participants, tasks, and themes"
6. Wait for approval (typically 5 minutes to 2 hours)

#### 3. Configure the Application

**Configuration File (`config.yaml`):**
```yaml
llm:
  provider: bedrock

bedrock:
  region: us-east-2
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  aws_access_key_env: AWS_ACCESS_KEY_ID
  aws_secret_key_env: AWS_SECRET_ACCESS_KEY
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0
```

**Environment Variables:**
```bash
export WJS_LLM_PROVIDER=bedrock
export WJS_BEDROCK_REGION=us-east-2
export WJS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Available Models

| Model | Model ID | Use Case | Cost |
|-------|----------|----------|------|
| **Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Best performance, production | Higher |
| **Claude 3 Sonnet** | `anthropic.claude-3-sonnet-20240229-v1:0` | Good performance, balanced | Medium |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Fast responses, cost-effective | Lower |

### Troubleshooting

**"Access Denied" Error:**
- Verify model access is granted in Bedrock Console
- Check AWS credentials have Bedrock permissions
- Ensure you're in the correct region

**"Model Not Found" Error:**
- Double-check the exact model ID
- Verify the model is available in your region
- Try listing available models in console

**"Throttling" Errors:**
- Increase `rate_limit_delay` in configuration
- Reduce `batch_size` for processing
- Consider upgrading to provisioned throughput

## Provider Comparison

### Performance Characteristics

| Aspect | AWS Bedrock | Google GenAI |
|--------|-------------|--------------|
| **Response Time** | 1-3 seconds | 0.5-2 seconds |
| **Rate Limits** | Model-dependent | Project quotas |
| **Reliability** | Very High | High |
| **Global Availability** | Multiple regions | Limited regions |

### Cost Considerations

| Provider | Pricing Model | Typical Cost | Best For |
|----------|---------------|--------------|----------|
| **AWS Bedrock** | Per-token usage | Higher per token | Production, enterprise |
| **Google GenAI** | Per-request/token | Lower per token | Development, testing |

### Feature Availability

| Feature | AWS Bedrock | Google GenAI |
|---------|-------------|--------------|
| **Content Analysis** | ✅ Full support | ✅ Full support |
| **Entity Extraction** | ✅ Excellent | ✅ Good |
| **Error Handling** | ✅ Comprehensive | ✅ Basic |
| **Retry Logic** | ✅ Advanced | ✅ Standard |
| **Statistics Tracking** | ✅ Detailed | ✅ Basic |

## Switching Between Providers

### Configuration Method

Simply change the provider in your configuration file:

```yaml
llm:
  provider: google_genai  # Changed from "bedrock"
```

### Environment Variable Method

```bash
export WJS_LLM_PROVIDER=google_genai
```

### Validation

Always test after switching providers:
```bash
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
```

The dry run will show which provider is active:
```
✅ LLM Provider: google_genai
📝 GCP Project: your-project-id
📍 Location: us-central1
🤖 Model: gemini-2.0-flash-001
```

## Migration Guide

### From Bedrock-Only to Multi-Provider

If you're upgrading from a version that only supported Bedrock:

1. **Update Configuration File**
   Add the new LLM section:
   ```yaml
   llm:
     provider: bedrock  # Maintains existing behavior
   ```

2. **No Code Changes Required**
   The application automatically uses the unified client

3. **Test Existing Setup**
   ```bash
   python work_journal_summarizer.py --dry-run --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly
   ```

### Adding Google GenAI to Existing Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt  # Includes google-genai
   ```

2. **Add Google GenAI Configuration**
   ```yaml
   llm:
     provider: bedrock  # Keep existing default
   
   google_genai:
     project: your-gcp-project-id
     location: us-central1
     model: gemini-2.0-flash-001
   ```

3. **Test Both Providers**
   ```bash
   # Test Bedrock (existing)
   WJS_LLM_PROVIDER=bedrock python work_journal_summarizer.py --dry-run --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly
   
   # Test Google GenAI (new)
   WJS_LLM_PROVIDER=google_genai python work_journal_summarizer.py --dry-run --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly
   ```

## Common Issues and Solutions

### Configuration Issues

**Problem: "Invalid provider" error**
```
Solution: Ensure provider is exactly "bedrock" or "google_genai" (case-sensitive)
```

**Problem: Provider-specific configuration missing**
```yaml
# Wrong - missing provider-specific config
llm:
  provider: google_genai
# No google_genai section

# Correct - includes provider config
llm:
  provider: google_genai
google_genai:
  project: your-project-id
  location: us-central1
  model: gemini-2.0-flash-001
```

### Authentication Issues

**AWS Bedrock:**
- Verify AWS credentials are set correctly
- Check IAM permissions include Bedrock access
- Ensure model access is granted in console

**Google GenAI:**
- Verify Application Default Credentials are configured
- Check service account has Vertex AI permissions
- Ensure APIs are enabled in your project

### Performance Issues

**High Latency:**
- Check network connectivity to provider
- Consider switching to a closer region
- Verify rate limiting isn't causing delays

**Rate Limiting:**
- Increase `rate_limit_delay` in configuration
- Reduce `batch_size` for processing
- Consider upgrading service tier

## Best Practices

### Provider Selection

**Use AWS Bedrock when:**
- Running in production environments
- Already using AWS infrastructure
- Need maximum reliability and performance
- Cost is less of a concern

**Use Google GenAI when:**
- Developing or testing the application
- Already using GCP infrastructure
- Need lower costs for experimentation
- Want faster response times

### Configuration Management

1. **Use Environment Variables for Secrets**
   ```bash
   export AWS_ACCESS_KEY_ID="your-key"
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

2. **Keep Provider Configs Separate**
   ```yaml
   llm:
     provider: bedrock
   
   bedrock:
     # Bedrock-specific settings
   
   google_genai:
     # Google GenAI-specific settings
   ```

3. **Test Configuration Changes**
   Always use `--dry-run` to validate configuration changes

### Monitoring and Maintenance

1. **Monitor API Usage**
   - Check provider billing dashboards regularly
   - Set up usage alerts
   - Track API call statistics

2. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade google-genai boto3
   ```

3. **Regular Testing**
   - Test both providers periodically
   - Validate configuration after updates
   - Monitor error rates and performance

## Support and Resources

### AWS Bedrock
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude Model Documentation](https://docs.anthropic.com/claude/docs)
- [AWS Support](https://aws.amazon.com/support/)

### Google GenAI
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google Cloud Support](https://cloud.google.com/support)

### Application Support
- Check application logs in the configured log directory
- Use `--dry-run` mode for configuration validation
- Enable DEBUG logging for detailed troubleshooting:
  ```bash
  python work_journal_summarizer.py --log-level DEBUG
  ```

## Example Configurations

### Production AWS Setup
```yaml
llm:
  provider: bedrock

bedrock:
  region: us-east-2
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0

processing:
  base_path: /data/journals/
  output_path: /data/summaries/
  max_file_size_mb: 50
  batch_size: 5
  rate_limit_delay: 2.0

logging:
  level: INFO
  file_output: true
  log_dir: /var/log/journal-summarizer/
```

### Development Google GenAI Setup
```yaml
llm:
  provider: google_genai

google_genai:
  project: dev-journal-project
  location: us-central1
  model: gemini-2.0-flash-001

processing:
  base_path: ~/Desktop/test-journals/
  output_path: ~/Desktop/test-summaries/
  max_file_size_mb: 10
  batch_size: 10
  rate_limit_delay: 0.5

logging:
  level: DEBUG
  console_output: true
  file_output: true
```

### Multi-Environment Setup
```yaml
llm:
  provider: ${WJS_LLM_PROVIDER:-bedrock}  # Environment variable with fallback

bedrock:
  region: ${WJS_BEDROCK_REGION:-us-east-2}
  model_id: ${WJS_BEDROCK_MODEL_ID:-anthropic.claude-3-5-sonnet-20241022-v2:0}

google_genai:
  project: ${WJS_GOOGLE_GENAI_PROJECT:-your-project-id}
  location: ${WJS_GOOGLE_GENAI_LOCATION:-us-central1}
  model: ${WJS_GOOGLE_GENAI_MODEL:-gemini-2.0-flash-001}
```

This allows easy switching between environments:
```bash
# Production (AWS)
export WJS_LLM_PROVIDER=bedrock

# Development (Google)
export WJS_LLM_PROVIDER=google_genai
export WJS_GOOGLE_GENAI_PROJECT=dev-project