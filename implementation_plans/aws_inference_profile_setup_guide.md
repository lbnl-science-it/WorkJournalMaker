# AWS Bedrock Inference Profile Setup Guide
## Comprehensive Implementation Guide for Claude Sonnet

### **Overview**
This guide provides detailed step-by-step instructions for setting up AWS Bedrock inference profiles to resolve the "on-demand throughput" error in your Journal Summarizer application. Inference profiles provide cross-region routing, improved reliability, and better cost tracking for Claude models.

---

## **Phase 1: AWS Console Setup & Investigation**

### **Step 1: Access AWS Bedrock Console**

1. **Navigate to AWS Bedrock Console**
   - Open your web browser and go to: https://console.aws.amazon.com/bedrock/
   - **Important**: Switch to the **US East (N. Virginia) - us-east-1** region
     - Click the region dropdown in the top-right corner
     - Select "US East (N. Virginia)" 
     - Inference profiles are primarily available in this region

2. **Verify Your Current Region**
   - Confirm the region shows "US East (N. Virginia)" in the top navigation
   - This is crucial as inference profiles have region-specific availability

### **Step 2: Explore Available Inference Profiles**

1. **Navigate to Model Access**
   - In the left sidebar, expand **"Inference and Assessment"** (click the arrow next to it)
   - Click **"Model access"** under the expanded section
   - You'll see a list of foundation models and inference profiles

2. **Identify Inference Profiles**
   - Look for entries marked with **"Inference Profile"** badge
   - Search for these specific profiles:
     - **US Anthropic Claude 3 Opus** (most likely available)
     - **US Anthropic Claude 3.5 Sonnet** (check availability)
     - **US Anthropic Claude 3 Sonnet** (fallback option)

3. **Document Available Profiles**
   - Take screenshots of available inference profiles
   - Note the exact ARN format (e.g., `us.anthropic.claude-3-opus-20240229-v1:0`)
   - Check the "Status" column for each profile

### **Step 3: Request Access to Inference Profiles**

#### **For Each Available Inference Profile:**

1. **Click on the Profile Name**
   - This opens the model details page
   - Review the model capabilities and pricing

2. **Request Access (if needed)**
   - If status shows "Request access", click the **"Request model access"** button
   - If status shows "Available", you may already have access

3. **Fill Out Access Request Form**
   ```
   Use Case: Work journal analysis and summarization
   
   Description: Automated analysis of daily work journals to extract 
   projects, participants, tasks, and themes for weekly/monthly summaries. 
   Using inference profiles for improved reliability and cross-region routing.
   
   Expected Usage: 50-200 API calls per day for personal productivity analysis
   ```

4. **Submit and Wait for Approval**
   - Typical approval time: 5 minutes to 2 hours
   - You'll receive email notification when approved
   - Status will change to "Access granted" with green checkmark

### **Step 4: Test Inference Profile Access**

1. **Navigate to Text Generation**
   - In the left sidebar, expand **"Playgrounds"**
   - Click **"Chat / Text"** under the expanded section
   - This opens the Bedrock playground

2. **Select Inference Profile**
   - In the model dropdown, look for your approved inference profiles
   - They'll be listed separately from direct model IDs
   - Select the Claude 3.5 Sonnet inference profile (preferred) or Claude 3 Opus

3. **Test with Sample Prompt**
   ```
   Test prompt: "Respond with valid JSON format: {\"test\": \"success\", \"model\": \"inference_profile\"}"
   ```

4. **Verify Response**
   - Ensure you get a proper JSON response
   - Note any latency or performance characteristics
   - Take a screenshot of successful test

5. **Document the Exact ARN**
   - Copy the exact inference profile ARN from the console
   - Format will be like: `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

---

## **Phase 2: Application Configuration Updates**

### **Step 5: Update Configuration Management**

#### **Modify BedrockConfig Class**

1. **Edit [`config_manager.py`](config_manager.py:26)**
   - Add new fields for inference profile support
   - Add fallback model configuration

```python
@dataclass
class BedrockConfig:
    """Configuration for AWS Bedrock API integration with inference profile support."""
    # Primary model (inference profile preferred)
    model_id: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # Update with actual ARN
    
    # Fallback models in priority order
    fallback_models: List[str] = field(default_factory=lambda: [
        "us.anthropic.claude-3-opus-20240229-v1:0",  # Inference profile fallback
        "anthropic.claude-3-sonnet-20240229-v1:0"    # Direct model emergency fallback
    ])
    
    # Inference profile settings
    use_inference_profiles: bool = True
    inference_profile_region: str = "us-east-1"  # Required for inference profiles
    
    # Existing settings
    region: str = "us-east-2"  # Fallback region for direct models
    aws_access_key_env: str = "AWS_ACCESS_KEY_ID"
    aws_secret_key_env: str = "AWS_SECRET_ACCESS_KEY"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
```

#### **Update Environment Variable Mappings**

2. **Add New Environment Variables**
   - Add support for inference profile configuration via environment variables

```python
# In _apply_env_overrides method, add:
env_mappings = {
    # Existing mappings...
    'WJS_USE_INFERENCE_PROFILES': ['bedrock', 'use_inference_profiles'],
    'WJS_INFERENCE_PROFILE_REGION': ['bedrock', 'inference_profile_region'],
    'WJS_FALLBACK_MODELS': ['bedrock', 'fallback_models'],
}
```

### **Step 6: Update Bedrock Client**

#### **Enhance Model Selection Logic**

1. **Modify [`BedrockClient`](bedrock_client.py:51)**
   - Add intelligent model selection with fallback
   - Support both inference profiles and direct model IDs

```python
def __init__(self, config: BedrockConfig):
    """Initialize Bedrock client with inference profile support."""
    self.config = config
    self.logger = logging.getLogger(__name__)
    self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)
    
    # Determine effective region based on model type
    self.effective_region = self._determine_effective_region()
    self.client = self._create_bedrock_client()
    
    # Test and select working model
    self.active_model = self._select_working_model()

def _determine_effective_region(self) -> str:
    """Determine which region to use based on model type."""
    if self.config.use_inference_profiles and self._is_inference_profile(self.config.model_id):
        return self.config.inference_profile_region
    return self.config.region

def _is_inference_profile(self, model_id: str) -> bool:
    """Check if model ID is an inference profile ARN."""
    return model_id.startswith('us.') and 'anthropic' in model_id

def _select_working_model(self) -> str:
    """Test models in priority order and return first working one."""
    models_to_try = [self.config.model_id] + self.config.fallback_models
    
    for model_id in models_to_try:
        try:
            if self._test_model_connection(model_id):
                self.logger.info(f"Successfully connected using model: {model_id}")
                return model_id
        except Exception as e:
            self.logger.warning(f"Model {model_id} failed: {e}")
            continue
    
    raise Exception("No working models found in configuration")

def _test_model_connection(self, model_id: str) -> bool:
    """Test connection to specific model."""
    test_prompt = "Respond with valid JSON: {\"test\": \"success\"}"
    request_body = self._format_bedrock_request(test_prompt)
    
    try:
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        return True
    except Exception:
        return False
```

#### **Update API Call Method**

2. **Modify `_make_api_call_with_retry`**
   - Use the active model instead of config model

```python
def _make_api_call_with_retry(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Make API call with exponential backoff retry logic using active model."""
    for attempt in range(self.config.max_retries + 1):
        try:
            response = self.client.invoke_model(
                modelId=self.active_model,  # Use active model instead of config.model_id
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            return json.loads(response['body'].read())
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Handle inference profile specific errors
            if error_code == 'ValidationException' and 'inference profile' in str(e):
                self.logger.error(f"Inference profile error: {e}")
                # Could attempt fallback to next model here
                
            # Existing error handling...
```

### **Step 7: Create Configuration File**

#### **Create Enhanced config.yaml**

```yaml
# Enhanced configuration with inference profile support
bedrock:
  # Primary model (inference profile ARN - update with your actual ARN)
  model_id: "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
  
  # Fallback models in priority order
  fallback_models:
    - "us.anthropic.claude-3-opus-20240229-v1:0"      # Inference profile fallback
    - "anthropic.claude-3-sonnet-20240229-v1:0"       # Direct model emergency fallback
  
  # Inference profile settings
  use_inference_profiles: true
  inference_profile_region: "us-east-1"  # Required for inference profiles
  
  # Standard settings
  region: "us-east-2"  # Fallback region for direct models
  timeout: 30
  max_retries: 3
  rate_limit_delay: 1.0

processing:
  base_path: "~/Desktop/worklogs/"
  output_path: "~/Desktop/worklogs/summaries/"
  max_file_size_mb: 50
  batch_size: 10
  rate_limit_delay: 1.0

logging:
  level: "INFO"
  console_output: true
  file_output: true
  log_dir: "~/Desktop/worklogs/summaries/error_logs/"
  include_timestamps: true
  include_module_names: true
  max_file_size_mb: 10
  backup_count: 5
```

---

## **Phase 3: Testing & Validation**

### **Step 8: Test the Implementation**

#### **Connection Test**

1. **Run Connection Test**
   ```bash
   python -c "
   from config_manager import ConfigManager
   from bedrock_client import BedrockClient
   
   config_manager = ConfigManager()
   bedrock_config = config_manager.get_config().bedrock
   client = BedrockClient(bedrock_config)
   
   print(f'Active model: {client.active_model}')
   print(f'Connection test: {client.test_connection()}')
   "
   ```

2. **Expected Output**
   ```
   Active model: us.anthropic.claude-3-5-sonnet-20241022-v2:0
   Connection test: True
   ✅ Bedrock API connection successful
   ```

#### **Journal Summarizer Test**

3. **Test with Dry Run**
   ```bash
   python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-01-07 --summary-type weekly --dry-run
   ```

4. **Expected Behavior**
   - Should connect successfully without "on-demand throughput" errors
   - Should show which model is being used
   - Should process test data without API errors

#### **Fallback Testing**

5. **Test Fallback Mechanism**
   - Temporarily use an invalid primary model in config
   - Verify it falls back to working model
   - Check logs for fallback messages

### **Step 9: Monitor and Optimize**

#### **Performance Monitoring**

1. **Check Response Times**
   - Compare inference profile vs direct model performance
   - Monitor for any latency differences
   - Document typical response times

2. **Cost Tracking**
   - Monitor AWS billing for Bedrock usage
   - Compare costs between inference profiles and direct models
   - Set up billing alerts if needed

3. **Error Monitoring**
   - Watch for any new error patterns
   - Monitor fallback usage frequency
   - Adjust retry settings if needed

---

## **Troubleshooting Guide**

### **Common Issues and Solutions**

#### **Issue 1: "Inference profile not found"**
**Symptoms:** Error when trying to use inference profile ARN
**Solutions:**
- Verify you're in the correct region (us-east-1 for inference profiles)
- Check that access was granted in AWS console
- Confirm exact ARN format from console

#### **Issue 2: "Access denied to inference profile"**
**Symptoms:** Permission errors when calling inference profile
**Solutions:**
- Verify model access is granted in Bedrock console
- Check IAM permissions include Bedrock access
- Ensure AWS credentials are correctly configured

#### **Issue 3: "No working models found"**
**Symptoms:** All models in fallback chain fail
**Solutions:**
- Check AWS credentials and permissions
- Verify at least one model has granted access
- Test individual models in AWS console first

#### **Issue 4: Higher than expected costs**
**Symptoms:** Increased AWS billing
**Solutions:**
- Monitor usage in AWS console
- Consider using Claude 3 Haiku for less critical tasks
- Implement request batching and caching

### **Performance Optimization Tips**

1. **Model Selection Strategy**
   - Use Claude 3.5 Sonnet for complex analysis
   - Use Claude 3 Opus for balanced performance/cost
   - Use Claude 3 Haiku for simple tasks

2. **Request Optimization**
   - Batch multiple small requests when possible
   - Implement response caching for repeated queries
   - Use appropriate temperature settings (0.1 for consistent extraction)

3. **Error Handling**
   - Implement exponential backoff for retries
   - Log detailed error information for debugging
   - Set up monitoring alerts for high error rates

---

## **Next Steps After Setup**

### **Immediate Actions**
1. ✅ Test connection with inference profiles
2. ✅ Run journal summarizer with small date range
3. ✅ Verify fallback mechanisms work
4. ✅ Monitor initial performance and costs

### **Long-term Optimization**
1. **Monitor Usage Patterns**
   - Track which models are used most frequently
   - Identify optimal batch sizes and timing
   - Adjust rate limits based on actual usage

2. **Cost Optimization**
   - Review monthly usage and costs
   - Consider model selection based on task complexity
   - Implement usage quotas if needed

3. **Reliability Improvements**
   - Add health checks for model availability
   - Implement circuit breaker patterns for failed models
   - Set up monitoring and alerting

### **Documentation Updates**
- Update README with new configuration options
- Document troubleshooting steps for team members
- Create runbook for common maintenance tasks

---

## **Configuration Reference**

### **Environment Variables**
```bash
# AWS Credentials (required)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Inference Profile Settings (optional)
export WJS_BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
export WJS_USE_INFERENCE_PROFILES="true"
export WJS_INFERENCE_PROFILE_REGION="us-east-1"

# Processing Settings (optional)
export WJS_BASE_PATH="~/Desktop/worklogs/"
export WJS_OUTPUT_PATH="~/Desktop/worklogs/summaries/"
```

### **Model ARN Reference**
```
# Inference Profiles (us-east-1 region)
us.anthropic.claude-3-5-sonnet-20241022-v2:0    # Claude 3.5 Sonnet (preferred)
us.anthropic.claude-3-opus-20240229-v1:0        # Claude 3 Opus (fallback)

# Direct Models (any supported region)
anthropic.claude-3-sonnet-20240229-v1:0         # Claude 3 Sonnet (emergency fallback)
anthropic.claude-3-haiku-20240307-v1:0          # Claude 3 Haiku (cost-effective)
```

---

## **Success Criteria**

Your setup is successful when:
- ✅ No more "on-demand throughput" errors
- ✅ Journal Summarizer processes files without API errors
- ✅ Fallback mechanism works when primary model unavailable
- ✅ Response times are acceptable (< 30 seconds per request)
- ✅ Costs are within expected range
- ✅ Logs show successful model selection and usage

**Estimated Total Setup Time:** 4-6 hours
**Difficulty Level:** Intermediate
**Prerequisites:** AWS account with Bedrock access, basic Python knowledge

---

*This guide was created to resolve the "on-demand throughput" error in the Journal Summarizer application by implementing AWS Bedrock inference profiles for improved reliability and cross-region routing.*