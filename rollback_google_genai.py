#!/usr/bin/env python3
"""
Google GenAI Integration Rollback Script

This script safely rolls back the Google GenAI integration changes,
restoring the system to Bedrock-only functionality while preserving
user data and providing recovery options.

Author: Work Journal Summarizer Project
Version: Rollback Script for Google GenAI Integration
"""

import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any


class RollbackManager:
    """Manages the rollback process for Google GenAI integration."""
    
    def __init__(self, dry_run: bool = False, keep_files: bool = False):
        self.dry_run = dry_run
        self.keep_files = keep_files
        self.backup_dir = Path(f"rollback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.changes_made = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔄" if level == "INFO" else "⚠️" if level == "WARN" else "❌"
        print(f"[{timestamp}] {prefix} {message}")
        
    def backup_current_state(self) -> bool:
        """Create backup of current state before rollback."""
        self.log("Creating backup of current state...")
        
        if self.dry_run:
            self.log(f"DRY RUN: Would create backup directory: {self.backup_dir}")
            return True
            
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup key files
            files_to_backup = [
                "config_manager.py",
                "work_journal_summarizer.py", 
                "requirements.txt",
                "config.yaml.example",
                "bedrock_client.py"
            ]
            
            for file_path in files_to_backup:
                if Path(file_path).exists():
                    shutil.copy2(file_path, self.backup_dir / file_path)
                    self.log(f"Backed up: {file_path}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create backup: {e}", "ERROR")
            return False
    
    def revert_work_journal_summarizer(self) -> bool:
        """Revert work_journal_summarizer.py to Bedrock-only imports."""
        self.log("Reverting work_journal_summarizer.py...")
        
        file_path = Path("work_journal_summarizer.py")
        if not file_path.exists():
            self.log("work_journal_summarizer.py not found", "WARN")
            return False
            
        if self.dry_run:
            self.log("DRY RUN: Would revert work_journal_summarizer.py imports")
            return True
            
        try:
            # Read current content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace unified client imports with bedrock client imports
            old_import = "from unified_llm_client import UnifiedLLMClient\nfrom llm_data_structures import AnalysisResult, APIStats"
            new_import = "from bedrock_client import BedrockClient, AnalysisResult, APIStats"
            
            if old_import in content:
                content = content.replace(old_import, new_import)
                self.log("Reverted imports to BedrockClient")
            else:
                # Try alternative import patterns
                content = content.replace(
                    "from unified_llm_client import UnifiedLLMClient",
                    "from bedrock_client import BedrockClient"
                )
                content = content.replace(
                    "from llm_data_structures import AnalysisResult, APIStats",
                    ""
                )
                if "AnalysisResult, APIStats" not in content:
                    # Add the import if not present
                    content = content.replace(
                        "from bedrock_client import BedrockClient",
                        "from bedrock_client import BedrockClient, AnalysisResult, APIStats"
                    )
            
            # Replace client initialization
            content = content.replace(
                "llm_client = UnifiedLLMClient(config)",
                "llm_client = BedrockClient(config.bedrock)"
            )
            
            # Write back
            with open(file_path, 'w') as f:
                f.write(content)
                
            self.changes_made.append("work_journal_summarizer.py")
            self.log("Successfully reverted work_journal_summarizer.py")
            return True
            
        except Exception as e:
            self.log(f"Failed to revert work_journal_summarizer.py: {e}", "ERROR")
            return False
    
    def revert_requirements(self) -> bool:
        """Remove google-genai from requirements.txt."""
        self.log("Reverting requirements.txt...")
        
        file_path = Path("requirements.txt")
        if not file_path.exists():
            self.log("requirements.txt not found", "WARN")
            return False
            
        if self.dry_run:
            self.log("DRY RUN: Would remove google-genai from requirements.txt")
            return True
            
        try:
            # Read current content
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Remove google-genai line
            new_lines = [line for line in lines if not line.strip().startswith('google-genai')]
            
            # Write back
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
                
            self.changes_made.append("requirements.txt")
            self.log("Successfully removed google-genai from requirements.txt")
            return True
            
        except Exception as e:
            self.log(f"Failed to revert requirements.txt: {e}", "ERROR")
            return False
    
    def restore_bedrock_client_data_structures(self) -> bool:
        """Restore AnalysisResult and APIStats to bedrock_client.py."""
        self.log("Restoring data structures to bedrock_client.py...")
        
        file_path = Path("bedrock_client.py")
        if not file_path.exists():
            self.log("bedrock_client.py not found", "WARN")
            return False
            
        if self.dry_run:
            self.log("DRY RUN: Would restore data structures to bedrock_client.py")
            return True
            
        try:
            # Read current content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Remove import from llm_data_structures if present
            content = content.replace(
                "from llm_data_structures import AnalysisResult, APIStats\n",
                ""
            )
            
            # Add data structures back if not present
            if "@dataclass" not in content or "class AnalysisResult" not in content:
                data_structures = '''
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class AnalysisResult:
    """Result of content analysis."""
    file_path: Path
    projects: List[str]
    participants: List[str]
    tasks: List[str]
    themes: List[str]
    api_call_time: float
    confidence_score: Optional[float] = None
    raw_response: Optional[str] = None

@dataclass
class APIStats:
    """Statistics for API calls."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0

'''
                # Insert after imports
                import_end = content.find('\n\n')
                if import_end != -1:
                    content = content[:import_end] + data_structures + content[import_end:]
                else:
                    content = data_structures + content
            
            # Write back
            with open(file_path, 'w') as f:
                f.write(content)
                
            self.changes_made.append("bedrock_client.py")
            self.log("Successfully restored data structures to bedrock_client.py")
            return True
            
        except Exception as e:
            self.log(f"Failed to restore bedrock_client.py: {e}", "ERROR")
            return False
    
    def handle_new_files(self) -> bool:
        """Handle new files created during implementation."""
        self.log("Handling new files...")
        
        new_files = [
            "llm_data_structures.py",
            "google_genai_client.py", 
            "unified_llm_client.py",
            "validate_llm_providers.py"
        ]
        
        for file_path in new_files:
            path = Path(file_path)
            if path.exists():
                if self.dry_run:
                    action = "backup" if self.keep_files else "remove"
                    self.log(f"DRY RUN: Would {action} {file_path}")
                elif self.keep_files:
                    backup_path = path.with_suffix(path.suffix + '.backup')
                    shutil.move(str(path), str(backup_path))
                    self.log(f"Backed up {file_path} to {backup_path}")
                else:
                    path.unlink()
                    self.log(f"Removed {file_path}")
        
        return True
    
    def validate_rollback(self) -> bool:
        """Validate that rollback was successful."""
        self.log("Validating rollback...")
        
        if self.dry_run:
            self.log("DRY RUN: Would validate rollback success")
            return True
        
        try:
            # Test imports
            import subprocess
            
            # Test that bedrock_client can be imported
            result = subprocess.run([
                sys.executable, "-c", 
                "from bedrock_client import BedrockClient, AnalysisResult, APIStats; print('OK')"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Import validation failed: {result.stderr}", "ERROR")
                return False
            
            self.log("Import validation successful")
            
            # Test that unified client cannot be imported (should fail)
            result = subprocess.run([
                sys.executable, "-c", 
                "from unified_llm_client import UnifiedLLMClient"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("Warning: unified_llm_client still importable", "WARN")
            else:
                self.log("Unified client properly removed")
            
            return True
            
        except Exception as e:
            self.log(f"Validation failed: {e}", "ERROR")
            return False
    
    def run_rollback(self) -> bool:
        """Execute the complete rollback process."""
        self.log("Starting Google GenAI integration rollback...")
        
        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made")
        
        steps = [
            ("Backup current state", self.backup_current_state),
            ("Revert work_journal_summarizer.py", self.revert_work_journal_summarizer),
            ("Revert requirements.txt", self.revert_requirements),
            ("Restore bedrock_client.py data structures", self.restore_bedrock_client_data_structures),
            ("Handle new files", self.handle_new_files),
            ("Validate rollback", self.validate_rollback)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Executing: {step_name}")
            if not step_func():
                self.log(f"Step failed: {step_name}", "ERROR")
                return False
        
        return True


def main():
    """Main entry point for rollback script."""
    parser = argparse.ArgumentParser(
        description="Rollback Google GenAI integration to Bedrock-only functionality"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true", 
        help="Keep new files as .backup instead of deleting them"
    )
    
    args = parser.parse_args()
    
    print("🔄 Google GenAI Integration Rollback Script")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    if args.keep_files:
        print("💾 KEEP FILES MODE - New files will be backed up")
    
    print()
    
    rollback_manager = RollbackManager(
        dry_run=args.dry_run,
        keep_files=args.keep_files
    )
    
    success = rollback_manager.run_rollback()
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ ROLLBACK COMPLETED SUCCESSFULLY")
        if not args.dry_run:
            print("✅ System restored to Bedrock-only functionality")
            print(f"✅ Backup created in: {rollback_manager.backup_dir}")
            if rollback_manager.changes_made:
                print("📝 Files modified:")
                for file_name in rollback_manager.changes_made:
                    print(f"  - {file_name}")
        else:
            print("🔍 Dry run completed - no changes made")
        return 0
    else:
        print("❌ ROLLBACK FAILED")
        print("❌ Please check the errors above and try manual rollback")
        print("📖 See ROLLBACK_PLAN.md for manual rollback instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())