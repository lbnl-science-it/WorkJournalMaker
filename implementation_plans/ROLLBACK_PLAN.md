# Google GenAI Integration Rollback Plan

## Overview
This document provides a comprehensive rollback plan for the Google GenAI integration implementation. It allows users to quickly return to the previous Bedrock-only functionality if issues are discovered after deployment.

## Files Modified During Implementation

### Core Implementation Files
1. **`config_manager.py`** - Added GoogleGenAIConfig and LLMConfig classes
2. **`work_journal_summarizer.py`** - Updated imports and client initialization
3. **`requirements.txt`** - Added google-genai dependency
4. **`config.yaml.example`** - Added new configuration sections

### New Files Created
1. **`llm_data_structures.py`** - Shared data structures (extracted from bedrock_client.py)
2. **`google_genai_client.py`** - Google GenAI client implementation
3. **`unified_llm_client.py`** - Unified client interface
4. **`validate_llm_providers.py`** - Validation script

### Test Files Created
1. **`tests/test_google_genai_client.py`** - Google GenAI client tests
2. **`tests/test_unified_llm_client.py`** - Unified client tests
3. **`tests/test_integration_llm_providers.py`** - Integration tests
4. **Various other test files** - Supporting test infrastructure

## Rollback Strategy

### Option 1: Quick Rollback (Recommended)
Use the automated rollback script to restore previous functionality while preserving new files for future use.

### Option 2: Complete Rollback
Remove all new files and restore original state completely.

### Option 3: Selective Rollback
Keep new files but revert core functionality to Bedrock-only mode.

## Pre-Rollback Checklist

Before executing rollback:

1. **Backup Current State**
   ```bash
   # Create backup of current implementation
   cp -r . ../JournalSummarizer_backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Document Issues**
   - Record specific problems encountered
   - Note which provider was being used when issues occurred
   - Save any error logs or stack traces

3. **Check Configuration**
   - Identify current LLM provider setting
   - Note any custom configuration changes

## Rollback Execution

### Automated Rollback (Recommended)

Run the rollback script:
```bash
python rollback_google_genai.py
```

This script will:
- Revert core files to Bedrock-only functionality
- Preserve new files with `.backup` extension
- Update configuration to use Bedrock only
- Validate rollback success

### Manual Rollback Steps

If automated rollback fails, follow these manual steps:

#### Step 1: Revert Core Files

1. **Revert `work_journal_summarizer.py`**
   ```bash
   # Restore original imports (line 29)
   # FROM: from unified_llm_client import UnifiedLLMClient
   #       from llm_data_structures import AnalysisResult, APIStats
   # TO:   from bedrock_client import BedrockClient, AnalysisResult, APIStats
   
   # Restore original client initialization (line 572)
   # FROM: llm_client = UnifiedLLMClient(config)
   # TO:   llm_client = BedrockClient(config.bedrock)
   ```

2. **Revert `config_manager.py`**
   ```bash
   # Remove GoogleGenAIConfig and LLMConfig classes
   # Remove google_genai and llm fields from AppConfig
   # Keep only original BedrockConfig functionality
   ```

3. **Revert `requirements.txt`**
   ```bash
   # Remove the line: google-genai
   ```

4. **Revert `config.yaml.example`**
   ```bash
   # Remove llm: and google_genai: sections
   # Keep only original bedrock: section
   ```

#### Step 2: Restore Data Structures

1. **Restore `bedrock_client.py`**
   ```bash
   # Add back AnalysisResult and APIStats dataclass definitions
   # Remove import from llm_data_structures
   ```

#### Step 3: Clean Up (Optional)

If complete removal is desired:
```bash
# Remove new files
rm -f llm_data_structures.py
rm -f google_genai_client.py
rm -f unified_llm_client.py
rm -f validate_llm_providers.py

# Remove test files
rm -f tests/test_google_genai_client.py
rm -f tests/test_unified_llm_client.py
rm -f tests/test_integration_llm_providers.py
```

## Configuration Preservation

### Preserving User Configuration

If users have existing configurations with new LLM settings:

1. **Backup Current Config**
   ```bash
   cp config.yaml config.yaml.backup
   ```

2. **Extract Bedrock Settings**
   ```yaml
   # Keep only the bedrock section from existing config
   bedrock:
     region: us-east-1
     model_id: anthropic.claude-3-sonnet-20240229-v1:0
   
   processing:
     max_file_size_mb: 10
     supported_extensions: ['.md', '.txt']
   ```

3. **Update Config After Rollback**
   - Merge preserved settings with rolled-back configuration
   - Ensure no references to removed LLM providers remain

## Rollback Validation

### Validation Steps

After rollback, validate the system works correctly:

1. **Test Import**
   ```bash
   python -c "import work_journal_summarizer; print('Import successful')"
   ```

2. **Test Configuration**
   ```bash
   python -c "from config_manager import ConfigManager; cm = ConfigManager(); print('Config OK')"
   ```

3. **Test Bedrock Client**
   ```bash
   python -c "from bedrock_client import BedrockClient; print('BedrockClient OK')"
   ```

4. **Run Existing Tests**
   ```bash
   python -m pytest tests/test_bedrock_client.py -v
   python -m pytest tests/test_config_manager.py -v
   ```

5. **Test Dry Run**
   ```bash
   python work_journal_summarizer.py --dry-run
   ```

### Success Criteria

Rollback is successful if:
- ✅ All imports work without errors
- ✅ Configuration loads correctly
- ✅ BedrockClient can be instantiated
- ✅ Existing tests pass
- ✅ Dry-run mode works
- ✅ No references to Google GenAI remain in active code

## Recovery Procedures

### If Rollback Fails

1. **Restore from Backup**
   ```bash
   # If you created a backup before rollback
   rm -rf *
   cp -r ../JournalSummarizer_backup_YYYYMMDD_HHMMSS/* .
   ```

2. **Fresh Installation**
   ```bash
   # Clone original repository
   git clone <original-repo-url> JournalSummarizer_fresh
   # Copy your data and configuration
   cp config.yaml JournalSummarizer_fresh/
   ```

### If Partial Rollback Needed

To keep new functionality but disable Google GenAI:

1. **Update Configuration**
   ```yaml
   llm:
     provider: bedrock  # Force Bedrock usage
   ```

2. **Remove Google GenAI Dependency**
   ```bash
   pip uninstall google-genai
   ```

## Post-Rollback Actions

### Immediate Actions
1. **Verify System Functionality**
   - Test with sample journal files
   - Verify output generation
   - Check error handling

2. **Update Documentation**
   - Note rollback completion
   - Document any issues encountered
   - Update user instructions if needed

### Future Considerations
1. **Issue Analysis**
   - Investigate root cause of problems
   - Document lessons learned
   - Plan fixes for future implementation

2. **Re-implementation Planning**
   - Address identified issues
   - Improve testing procedures
   - Consider phased rollout approach

## Emergency Contacts

If rollback issues persist:
1. Check project documentation
2. Review error logs carefully
3. Consider restoring from version control
4. Document all steps taken for future reference

## Rollback Script Usage

The automated rollback script (`rollback_google_genai.py`) provides:
- Safe, reversible rollback process
- Automatic backup of current state
- Validation of rollback success
- Detailed logging of all actions

Run with:
```bash
python rollback_google_genai.py [--dry-run] [--keep-files]
```

Options:
- `--dry-run`: Show what would be done without making changes
- `--keep-files`: Keep new files as `.backup` instead of deleting

## Summary

This rollback plan ensures users can quickly and safely return to a working Bedrock-only configuration if issues arise with the Google GenAI integration. The automated script provides the safest approach, while manual steps are available as a fallback option.