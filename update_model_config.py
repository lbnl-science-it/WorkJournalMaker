#!/usr/bin/env python3
"""
Model Configuration Updater

This script helps update the model configuration for the Work Journal Summarizer
after you've gained access to a new model in AWS Bedrock.

Usage:
    python update_model_config.py --model anthropic.claude-3-5-sonnet-20241022-v2:0
    python update_model_config.py --model anthropic.claude-3-sonnet-20240229-v1:0 --test
"""

import argparse
import os
import sys
from pathlib import Path
from config_manager import ConfigManager, BedrockConfig
from bedrock_client import BedrockClient


def update_model_via_env_var(model_id: str):
    """Update model configuration via environment variable."""
    print(f"🔧 Setting environment variable for model: {model_id}")
    
    # Set the environment variable
    os.environ['WJS_BEDROCK_MODEL_ID'] = model_id
    
    print(f"✅ Environment variable set: WJS_BEDROCK_MODEL_ID={model_id}")
    print("💡 To make this permanent, add to your shell profile:")
    print(f"   export WJS_BEDROCK_MODEL_ID=\"{model_id}\"")


def create_config_file(model_id: str, config_path: Path):
    """Create a configuration file with the new model."""
    print(f"📝 Creating configuration file: {config_path}")
    
    config_manager = ConfigManager()
    config_manager.save_example_config(config_path)
    
    # Read the file and update the model ID
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Replace the model ID in the content
    updated_content = content.replace(
        'anthropic.claude-sonnet-4-20250514-v1:0',
        model_id
    )
    
    with open(config_path, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Configuration file created with model: {model_id}")


def test_model_connection(model_id: str) -> bool:
    """Test connection to the specified model."""
    print(f"🧪 Testing connection to model: {model_id}")
    
    try:
        # Create a temporary config with the new model
        temp_config = BedrockConfig(model_id=model_id)
        client = BedrockClient(temp_config)
        
        if client.test_connection():
            print("✅ Model connection successful!")
            return True
        else:
            print("❌ Model connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False


def main():
    """Main entry point for the configuration updater."""
    parser = argparse.ArgumentParser(
        description='Update Work Journal Summarizer model configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --model anthropic.claude-3-5-sonnet-20241022-v2:0
  %(prog)s --model anthropic.claude-3-sonnet-20240229-v1:0 --test
  %(prog)s --model anthropic.claude-3-5-sonnet-20241022-v2:0 --config-file config.yaml
        """
    )
    
    parser.add_argument(
        '--model',
        required=True,
        help='Model ID to configure (e.g., anthropic.claude-3-5-sonnet-20241022-v2:0)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the model connection after updating configuration'
    )
    
    parser.add_argument(
        '--config-file',
        help='Create a configuration file instead of using environment variable'
    )
    
    args = parser.parse_args()
    
    print("🔧 Work Journal Summarizer - Model Configuration Updater")
    print("=" * 60)
    
    # Validate model ID format
    if not args.model.startswith('anthropic.claude'):
        print("⚠️  Warning: Model ID doesn't appear to be a Claude model")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return
    
    # Update configuration
    if args.config_file:
        config_path = Path(args.config_file)
        create_config_file(args.model, config_path)
    else:
        update_model_via_env_var(args.model)
    
    # Test connection if requested
    if args.test:
        print("\n" + "=" * 60)
        success = test_model_connection(args.model)
        
        if success:
            print("\n🎉 Configuration update successful!")
            print("💡 You can now run your journal summarizer with the new model")
        else:
            print("\n❌ Configuration updated but model test failed")
            print("💡 Check that you have access to this model in AWS Bedrock console")
    
    print("\n🎯 Next steps:")
    print("1. Verify model access in AWS Bedrock console")
    print("2. Test with: python work_journal_summarizer.py --dry-run ...")
    print("3. Run your actual journal summarization")


if __name__ == "__main__":
    main()