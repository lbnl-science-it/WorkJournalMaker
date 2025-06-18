# AWS Bedrock Claude 3.5 Sonnet Setup Guide

## Problem Diagnosis Summary
Your Journal Summarizer is failing because the model `anthropic.claude-sonnet-4-20250514-v1:0` doesn't support on-demand throughput in AWS Bedrock. The error message indicates you need to either:
1. Use an inference profile ARN, or 
2. Switch to a model that supports on-demand throughput

## Solution: Enable Claude 3.5 Sonnet Access

### Step 1: Request Model Access in AWS Bedrock Console

1. **Navigate to AWS Bedrock Console**
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
   - Ensure you're in the correct region: `us-east-2` (Ohio)

2. **Access Model Access Page**
   - In the left sidebar, click **"Model access"**
   - You'll see a list of available foundation models

3. **Find Claude 3.5 Sonnet**
   - Look for **"Anthropic Claude 3.5 Sonnet"** 
   - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Status should show "Available" or "Request access"

4. **Request Access**
   - Click **"Request model access"** or **"Manage"**
   - Fill out the use case form:
     - **Use case**: "Work journal analysis and summarization"
     - **Description**: "Automated analysis of daily work journals to extract projects, participants, tasks, and themes for weekly/monthly summaries"
   - Submit the request

### Step 2: Wait for Approval
- **Typical wait time**: 5 minutes to 2 hours
- **Check status**: Return to "Model access" page periodically
- **Confirmation**: Status changes to "Access granted" with green checkmark

### Step 3: Verify Model Access

1. **Test in Console**
   - Go to **"Text"** or **"Chat"** in Bedrock console
   - Select Claude 3.5 Sonnet model
   - Send a test message: "Respond with JSON: {\"test\": \"success\"}"
   - Verify you get a proper response

2. **Note the Exact Model ID**
   - The console will show the exact model identifier
   - Should be: `anthropic.claude-3-5-sonnet-20241022-v2:0`

### Step 4: Update Application Configuration

Once access is granted, you'll need to update your application configuration:

#### Option A: Environment Variable (Recommended)
```bash
export WJS_BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
```

#### Option B: Configuration File
Create a `config.yaml` file:
```yaml
bedrock:
  region: us-east-2
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0

processing:
  base_path: ~/Desktop/worklogs/
  output_path: ~/Desktop/worklogs/summaries/
  max_file_size_mb: 50
  batch_size: 10
  rate_limit_delay: 1.0

logging:
  level: INFO
  console_output: true
  file_output: true
  log_dir: ~/Desktop/worklogs/summaries/error_logs/
  include_timestamps: true
  include_module_names: true
  max_file_size_mb: 10
  backup_count: 5
```

### Step 5: Test the Fix

After updating configuration, test with dry run:
```bash
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
```

Expected output should show:
```
✅ Bedrock API connection successful
```

## Alternative Models (if Claude 3.5 Sonnet unavailable)

If Claude 3.5 Sonnet access is denied or unavailable, try these alternatives:

1. **Claude 3 Sonnet (Original)**
   - Model ID: `anthropic.claude-3-sonnet-20240229-v1:0`
   - Generally available with on-demand throughput

2. **Claude 3 Haiku (Faster/Cheaper)**
   - Model ID: `anthropic.claude-3-haiku-20240307-v1:0`
   - Good for basic text analysis tasks

## Troubleshooting

### Common Issues:

1. **"Access Denied" Error**
   - Verify model access is granted in console
   - Check AWS credentials have Bedrock permissions
   - Ensure you're in the correct region

2. **"Model Not Found" Error**
   - Double-check the exact model ID
   - Verify the model is available in your region
   - Try listing available models in console

3. **"Throttling" Errors**
   - Increase `rate_limit_delay` in configuration
   - Reduce `batch_size` for processing

### Next Steps After Setup:
1. Test connection with dry run
2. Process a small date range first
3. Monitor logs for any remaining issues
4. Adjust rate limits if needed for your usage patterns

## Cost Considerations

- **Claude 3.5 Sonnet**: Higher cost but better performance
- **Claude 3 Sonnet**: Moderate cost, good performance
- **Claude 3 Haiku**: Lower cost, faster responses

Choose based on your quality vs. cost requirements.