#!/usr/bin/env python3
"""
Bedrock Model Checker - Diagnostic Tool

This tool helps diagnose AWS Bedrock model availability and connection issues.
It lists available models in your region and tests connections to specific models.

Usage:
    python bedrock_model_checker.py --list-models
    python bedrock_model_checker.py --test-model anthropic.claude-3-5-sonnet-20241022-v2:0
    python bedrock_model_checker.py --test-all-claude
"""

import argparse
import boto3
import json
import os
from botocore.exceptions import ClientError, BotoCoreError
from typing import List, Dict, Any


class BedrockModelChecker:
    """Diagnostic tool for AWS Bedrock model availability and testing."""
    
    def __init__(self, region: str = "us-east-2"):
        """Initialize the model checker with AWS region."""
        self.region = region
        self.bedrock_client = self._create_bedrock_client()
        self.runtime_client = self._create_runtime_client()
    
    def _create_bedrock_client(self):
        """Create Bedrock client for listing models."""
        try:
            return boto3.client('bedrock', region_name=self.region)
        except Exception as e:
            print(f"❌ Failed to create Bedrock client: {e}")
            return None
    
    def _create_runtime_client(self):
        """Create Bedrock Runtime client for testing models."""
        try:
            return boto3.client('bedrock-runtime', region_name=self.region)
        except Exception as e:
            print(f"❌ Failed to create Bedrock Runtime client: {e}")
            return None
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available foundation models in the region."""
        if not self.bedrock_client:
            return []
        
        try:
            response = self.bedrock_client.list_foundation_models()
            return response.get('modelSummaries', [])
        except Exception as e:
            print(f"❌ Failed to list models: {e}")
            return []
    
    def filter_claude_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for Claude models only."""
        claude_models = []
        for model in models:
            model_id = model.get('modelId', '')
            if 'claude' in model_id.lower():
                claude_models.append(model)
        return claude_models
    
    def print_model_info(self, models: List[Dict[str, Any]]):
        """Print formatted model information."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📋 Found {len(models)} models:")
        print("=" * 80)
        
        for model in models:
            model_id = model.get('modelId', 'Unknown')
            model_name = model.get('modelName', 'Unknown')
            provider = model.get('providerName', 'Unknown')
            input_modalities = model.get('inputModalities', [])
            output_modalities = model.get('outputModalities', [])
            
            print(f"🤖 Model: {model_name}")
            print(f"   ID: {model_id}")
            print(f"   Provider: {provider}")
            print(f"   Input: {', '.join(input_modalities)}")
            print(f"   Output: {', '.join(output_modalities)}")
            print("-" * 80)
    
    def test_model_connection(self, model_id: str) -> bool:
        """Test connection to a specific model."""
        if not self.runtime_client:
            return False
        
        print(f"\n🔍 Testing connection to: {model_id}")
        print("-" * 50)
        
        try:
            # Create a simple test request
            test_prompt = "Respond with valid JSON: {\"test\": \"success\"}"
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ],
                "temperature": 0.1
            }
            
            print(f"📤 Sending test request...")
            response = self.runtime_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            print(f"✅ Connection successful!")
            print(f"📥 Response: {json.dumps(response_body, indent=2)}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            print(f"❌ Connection failed: {error_code}")
            print(f"📝 Error: {error_message}")
            
            # Provide specific guidance
            if error_code == 'ValidationException':
                if 'on-demand throughput' in error_message:
                    print("💡 DIAGNOSIS: Model requires inference profile")
                    print("💡 SOLUTION: Use inference profile ARN or different model")
                elif 'model access' in error_message.lower():
                    print("💡 DIAGNOSIS: Model access not granted")
                    print("💡 SOLUTION: Request model access in Bedrock console")
            elif error_code == 'AccessDeniedException':
                print("💡 DIAGNOSIS: Access denied - check permissions")
                print("💡 SOLUTION: Verify model access in Bedrock console")
            elif error_code == 'ResourceNotFoundException':
                print("💡 DIAGNOSIS: Model not found in this region")
                print(f"💡 SOLUTION: Check if model is available in {self.region}")
            
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def test_all_claude_models(self):
        """Test connection to all available Claude models."""
        models = self.list_available_models()
        claude_models = self.filter_claude_models(models)
        
        if not claude_models:
            print("❌ No Claude models found in region")
            return
        
        print(f"\n🧪 Testing {len(claude_models)} Claude models...")
        
        successful_models = []
        failed_models = []
        
        for model in claude_models:
            model_id = model.get('modelId', '')
            if self.test_model_connection(model_id):
                successful_models.append(model_id)
            else:
                failed_models.append(model_id)
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"✅ Successful: {len(successful_models)}")
        print(f"❌ Failed: {len(failed_models)}")
        
        if successful_models:
            print(f"\n✅ Working models:")
            for model_id in successful_models:
                print(f"   - {model_id}")
        
        if failed_models:
            print(f"\n❌ Failed models:")
            for model_id in failed_models:
                print(f"   - {model_id}")


def main():
    """Main entry point for the diagnostic tool."""
    parser = argparse.ArgumentParser(
        description='AWS Bedrock Model Diagnostic Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-models
  %(prog)s --list-claude
  %(prog)s --test-model anthropic.claude-3-5-sonnet-20241022-v2:0
  %(prog)s --test-all-claude
  %(prog)s --region us-west-2 --list-models
        """
    )
    
    parser.add_argument(
        '--region',
        default='us-east-2',
        help='AWS region to check (default: us-east-2)'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available foundation models'
    )
    
    parser.add_argument(
        '--list-claude',
        action='store_true',
        help='List only Claude models'
    )
    
    parser.add_argument(
        '--test-model',
        help='Test connection to a specific model ID'
    )
    
    parser.add_argument(
        '--test-all-claude',
        action='store_true',
        help='Test connection to all Claude models'
    )
    
    args = parser.parse_args()
    
    # Check AWS credentials
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("❌ AWS credentials not found")
        print("💡 Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return
    
    print(f"🔍 AWS Bedrock Model Checker")
    print(f"📍 Region: {args.region}")
    print("=" * 50)
    
    checker = BedrockModelChecker(args.region)
    
    if args.list_models:
        models = checker.list_available_models()
        checker.print_model_info(models)
    
    elif args.list_claude:
        models = checker.list_available_models()
        claude_models = checker.filter_claude_models(models)
        checker.print_model_info(claude_models)
    
    elif args.test_model:
        checker.test_model_connection(args.test_model)
    
    elif args.test_all_claude:
        checker.test_all_claude_models()
    
    else:
        print("❌ No action specified. Use --help for usage information.")


if __name__ == "__main__":
    main()