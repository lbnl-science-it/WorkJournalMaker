# Executable-Compatible Configurable Database Location Feature Specification

## Overview

This specification defines a feature to make the database file location configurable in the Work Journal Maker application. This enables power users and developers to run multiple instances with separate databases while maintaining default behavior for regular users. **CRITICAL**: This specification ensures full compatibility with PyInstaller and other executable compilation systems.

## Current State Analysis

### File Storage Locations
- **Database**: 
  - Development: `./web/journal_index.db`
  - Production: OS-specific app data directory + `journal_index.db`
- **Logs**: `~/Desktop/worklogs/summaries/error_logs/` (configurable)
- **Journal files**: `~/Desktop/worklogs/` (configurable via `base_path`)
- **Summaries**: `~/Desktop/worklogs/summaries/` (configurable via `output_path`)

### Executable Environment Compatibility Requirements
- **Challenge**: PyInstaller creates temporary directories and changes working directory behavior
- **Solution**: Must detect executable location explicitly, not rely on current working directory
- **Critical**: Relative paths must be resolved against executable directory, not CWD

## Feature Requirements

### 1. Configuration File Discovery (EXECUTABLE-AWARE)

#### New Priority Order (Highest to Lowest)
1. **Executable directory config** (co-located with executable binary) - **PARAMOUNT**
2. Command-line `--config` argument
3. Standard system locations (`~/.config/work-journal-summarizer/config.yaml`)
4. Default behavior

#### Required Implementation in ConfigManager
**CRITICAL**: Must use executable detection logic, not working directory:
```python
import sys
from pathlib import Path
from typing import Optional

def _get_executable_directory() -> Path:
    """Get the directory containing the executable, handling both dev and compiled environments."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return Path(sys.executable).parent
    else:
        # Running as Python script in development
        return Path(__file__).parent

def _find_config_file(self) -> Optional[Path]:
    """Find configuration file with executable-aware priority order."""
    
    # PARAMOUNT: Check executable directory FIRST
    exe_dir = self._get_executable_directory()
    exe_locations = [
        exe_dir / "config.yaml",
        exe_dir / "config.yml",
        exe_dir / "config.json"
    ]
    
    for location in exe_locations:
        if location.exists() and location.is_file():
            return location
    
    # Then check standard system locations
    for location in self.CONFIG_LOCATIONS:
        expanded_path = location.expanduser()
        if expanded_path.exists() and expanded_path.is_file():
            return expanded_path
    
    return None
```

### 2. Database Path Configuration

#### Config File Structure
Add `database_path` to existing `processing` section:

```yaml
processing:
  base_path: ~/Desktop/worklogs/
  output_path: ~/Desktop/worklogs/summaries/
  database_path: ~/Desktop/worklogs/journal_index.db  # NEW
  max_file_size_mb: 50
  batch_size: 10
  rate_limit_delay: 1.0
```

#### Configuration Priority (Highest to Lowest)
1. **Config file in executable directory** (automatic detection)
2. Command-line argument `--database-path`
3. Config file setting `processing.database_path` (from system locations)
4. Default behavior (current runtime detection logic)

### 3. Path Specification (EXECUTABLE-AWARE)

#### Path Format
- **Complete file path**: Users specify full path including filename
- **Tilde expansion**: Support `~` for home directory expansion
- **Relative paths**: **CRITICAL** - Resolved relative to executable directory, NOT working directory
- **Absolute paths**: Support full system paths
- **No extension restrictions**: Accept any filename regardless of extension

#### Executable-Safe Path Resolution
```python
def _resolve_path_executable_safe(self, path: str, source: str = "config") -> str:
    """Resolve path with executable-aware logic for compiled environments."""
    resolved_path = Path(path).expanduser()
    
    if not resolved_path.is_absolute():
        # CRITICAL: Relative paths are relative to executable directory
        exe_dir = self._get_executable_directory()
        resolved_path = exe_dir / resolved_path
    
    resolved_path = resolved_path.resolve()
    
    # Ensure parent directories exist with proper error handling
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        # Fallback to user data directory for permission issues
        user_data_dir = self._get_user_data_directory()
        fallback_path = user_data_dir / f"fallback_{resolved_path.name}"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Permission denied for {resolved_path}, using fallback: {fallback_path}")
        return str(fallback_path)
    
    return str(resolved_path)
```

#### Examples (Executable-Aware)
```yaml
database_path: ~/my-journals/work.db                    # Tilde expansion (safe)
database_path: ./data/journal_index.sqlite              # Relative to EXECUTABLE dir (not CWD)
database_path: /opt/workjournal/databases/main.database # Absolute path (safe)
database_path: C:\WorkData\journal.db                   # Windows absolute (safe)
database_path: data/local.db                           # Relative to executable dir
```

### 4. Directory Handling

#### Automatic Directory Creation
- **Auto-create parent directories** if they don't exist
- **No user confirmation required** (power user feature)
- **Log directory creation** for audit trail

### 5. Application Integration

#### Supported Applications
Both applications must support `--database-path` command-line option:
1. **CLI Summarizer** (`work_journal_summarizer.py`)
2. **Web Application Server** (`server_runner.py`)

#### Executable Directory Behavior (CRITICAL CLARIFICATION)
When executable and `config.yaml` are co-located in the same directory:
```bash
# IMPORTANT: Config file must be in SAME directory as executable
/path/to/WorkJournalMaker                    # Uses /path/to/config.yaml (if exists)
cd /different/dir && /path/to/WorkJournalMaker # Still uses /path/to/config.yaml
./WorkJournalMaker --host localhost          # Uses ./config.yaml + CLI overrides

# NOT working directory dependent - executable location dependent
cd ~/Desktop && ~/Apps/WorkJournalMaker      # Uses ~/Apps/config.yaml (if exists)
```

#### Multi-Instance Setup (Executable-Safe)
```bash
# Each executable copy uses its own co-located config
mkdir ~/work-instance1 ~/work-instance2

# Instance 1 setup
cp WorkJournalMaker ~/work-instance1/
cat > ~/work-instance1/config.yaml << EOF
processing:
  database_path: ./personal.db    # Resolves to ~/work-instance1/personal.db
  base_path: ~/Documents/personal-worklogs/
EOF

# Instance 2 setup  
cp WorkJournalMaker ~/work-instance2/
cat > ~/work-instance2/config.yaml << EOF
processing:
  database_path: ./client.db      # Resolves to ~/work-instance2/client.db
  base_path: ~/Documents/client-worklogs/
EOF

# Each instance is completely isolated
~/work-instance1/WorkJournalMaker             # Uses instance1 config
~/work-instance2/WorkJournalMaker             # Uses instance2 config
```

#### Command-Line Syntax
```bash
# CLI tool with explicit database override
python work_journal_summarizer.py --database-path ~/custom/journal.db --start-date 2024-01-01 --end-date 2024-01-31 --summary-type weekly

# Web server with explicit database override  
python server_runner.py --database-path ~/custom/journal.db --host localhost --port-range 8000-8099
```

### 6. Error Handling

#### Invalid Path Scenarios
When specified database path fails (permissions, invalid directory, etc.):

1. **Check for existing default database**
2. **If existing default database found**: 
   - **Stop with detailed error message**
   - **Require explicit user resolution**
   - **Do NOT automatically fallback**

#### Error Message Format
```
ERROR: Database configuration conflict detected.

Specified database path failed: /invalid/path/my_journal.db
  Reason: [Permission denied / Directory does not exist / etc.]
  Source: ./config.yaml (processing.database_path)

Found existing database at default location: ~/.local/share/WorkJournalMaker/journal_index.db
  Contains: 1,247 journal entries (2023-01-15 to 2024-12-27)

Resolution required:
  1. Fix the path in ./config.yaml and retry, OR
  2. Update ./config.yaml to use: database_path: ~/.local/share/WorkJournalMaker/journal_index.db, OR
  3. Remove database_path from ./config.yaml to use default behavior
```

### 7. Migration Policy

#### No Automatic Migration
- **Clean separation**: Each database path is independent
- **No data migration offers**: Users handle data movement manually
- **Fresh start**: New database paths start with empty database
- **Power user responsibility**: Users manage their own data organization

### 8. Configuration File Behavior

#### Example Generation
- **Do NOT include** `database_path` in auto-generated example configs
- **Default behavior**: Regular users get default locations automatically
- **Power user discovery**: Feature discoverable only through documentation or manual config creation

#### Environment Variable Support
Add environment variable override (lowest priority):
```bash
export WJS_DATABASE_PATH="/path/to/custom/journal.db"
```

## Implementation Details

### 1. Configuration Manager Changes (CRITICAL)

#### Executable-Aware Config File Discovery (FIXED)
```python
import sys
from pathlib import Path
from typing import Optional

class ExecutableAwareConfigManager(ConfigManager):
    def __init__(self):
        self.executable_dir = self._get_executable_directory()
        super().__init__()
    
    def _get_executable_directory(self) -> Path:
        """Get directory containing the executable, handling both dev and compiled environments."""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller/cx_Freeze executable
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller
                return Path(sys.executable).parent
            else:
                # cx_Freeze and others
                return Path(sys.executable).parent
        else:
            # Running as Python script in development
            return Path(__file__).parent
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file with executable-aware priority order."""
        
        # PARAMOUNT: Check executable directory FIRST (not CWD)
        exe_locations = [
            self.executable_dir / "config.yaml",
            self.executable_dir / "config.yml",
            self.executable_dir / "config.json"
        ]
        
        for location in exe_locations:
            if location.exists() and location.is_file():
                self.logger.info(f"Using executable directory config: {location}")
                return location
        
        # Then check standard system locations
        for location in self.CONFIG_LOCATIONS:
            expanded_path = location.expanduser()
            if expanded_path.exists() and expanded_path.is_file():
                self.logger.info(f"Using system config: {expanded_path}")
                return expanded_path
        
        self.logger.info("No config file found, using defaults")
        return None
```

#### ProcessingConfig Class
```python
@dataclass
class ProcessingConfig:
    base_path: str = "~/Desktop/worklogs/"
    output_path: str = "~/Desktop/worklogs/summaries/"
    database_path: Optional[str] = None  # NEW FIELD
    max_file_size_mb: int = 50
    batch_size: int = 10
    rate_limit_delay: float = 1.0
```

#### Environment Variable Mapping
```python
env_mappings = {
    # ... existing mappings ...
    'WJS_DATABASE_PATH': ['processing', 'database_path'],
}
```

### 2. Database Manager Changes

#### Constructor Modification
```python
class DatabaseManager:
    def __init__(self, database_path: Optional[str] = None, config: Optional[ProcessingConfig] = None):
        # Priority: explicit path > config path > default logic
        if database_path:
            self.database_path = self._resolve_path(database_path)
        elif config and config.database_path:
            self.database_path = self._resolve_path(config.database_path)
        else:
            self.database_path = self._get_default_database_path()
```

#### Executable-Aware Path Resolution (FIXED)
```python
def _resolve_path(self, path: str, source: str = "config") -> str:
    """Resolve path with executable-aware logic and robust error handling."""
    resolved_path = Path(path).expanduser()
    
    # Handle relative paths - CRITICAL for executable compatibility
    if not resolved_path.is_absolute():
        exe_dir = self._get_executable_directory()
        resolved_path = exe_dir / resolved_path
        self.logger.debug(f"Resolved relative path '{path}' to '{resolved_path}' (exe dir: {exe_dir})")
    
    resolved_path = resolved_path.resolve()
    
    # Create parent directories with proper error handling
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        # Fallback to user data directory for permission issues
        user_data_dir = self._get_user_data_directory()
        fallback_path = user_data_dir / f"fallback_{resolved_path.name}"
        try:
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.warning(
                f"Permission denied for {resolved_path} (source: {source}), "
                f"using fallback: {fallback_path}. Error: {e}"
            )
            return str(fallback_path)
        except Exception as fallback_error:
            raise ValueError(
                f"Cannot create database path {resolved_path} or fallback {fallback_path}. "
                f"Original error: {e}. Fallback error: {fallback_error}"
            )
    
    return str(resolved_path)

def _get_user_data_directory(self) -> Path:
    """Get platform-appropriate user data directory for fallback paths."""
    import platform
    system = platform.system()
    
    if system == "Windows":
        return Path.home() / "AppData" / "Local" / "WorkJournalMaker"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
    else:  # Linux and others
        return Path.home() / ".local" / "share" / "WorkJournalMaker"
```

#### Error Handling
```python
def _validate_database_path(self, path: str, source: str = "config") -> None:
    """Validate database path and handle conflicts."""
    try:
        # Test path accessibility
        test_path = Path(path)
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.touch(exist_ok=True)  # Test write permissions
        test_path.unlink(missing_ok=True)  # Clean up test file
    except Exception as e:
        # Check for existing default database
        default_path = self._get_default_database_path()
        if Path(default_path).exists():
            self._raise_path_conflict_error(path, str(e), default_path, source)
        else:
            raise ValueError(f"Cannot access database path {path}: {e}")
```

### 3. Command-Line Integration

#### CLI Summarizer
```python
parser.add_argument(
    '--database-path',
    type=str,
    help='Path to database file (overrides config file setting)'
)
```

#### Server Runner
```python
parser.add_argument(
    '--database-path',
    type=str,
    help='Path to database file (overrides config file setting)'
)
```

### 4. Application Integration Points

#### Web Application Startup
```python
# In WorkJournalWebApp.startup()
# Config is automatically loaded from executable directory if present
db_path = None
if hasattr(args, 'database_path') and args.database_path:
    db_path = args.database_path

self.db_manager = DatabaseManager(database_path=db_path, config=self.config.processing)
```

#### CLI Application Startup
```python
# In main processing loop
# Config is automatically loaded from executable directory if present
config = ConfigManager().get_config()
db_path = args.database_path if hasattr(args, 'database_path') else None
db_manager = DatabaseManager(database_path=db_path, config=config.processing)
```

## Use Cases

### 1. Regular User (No Change)
- Downloads executable
- Runs executable → Uses default database location
- No configuration needed

### 2. Power User - Multiple Instances
```bash
# Instance 1: Personal work
mkdir ~/work-personal
cd ~/work-personal
cp WorkJournalMaker ./
cat > config.yaml << EOF
processing:
  base_path: ~/Documents/personal-worklogs/
  output_path: ~/Documents/personal-worklogs/summaries/
  database_path: ~/Documents/personal-worklogs/personal.db
EOF
./WorkJournalMaker

# Instance 2: Client work  
mkdir ~/work-client
cd ~/work-client
cp WorkJournalMaker ./
cat > config.yaml << EOF
processing:
  base_path: ~/Documents/client-worklogs/
  output_path: ~/Documents/client-worklogs/summaries/
  database_path: ~/Documents/client-worklogs/client.db
EOF
./WorkJournalMaker
```

### 3. Developer - Project-Specific Configs
```bash
# Each project directory has its own config
cd /projects/projectA
cat > config.yaml << EOF
processing:
  database_path: ./project-data/journal.db
  base_path: ./worklogs/
  output_path: ./reports/
EOF
python /path/to/server_runner.py  # Automatically uses ./config.yaml
```

## Testing Requirements

### 1. Configuration Discovery Tests (EXECUTABLE-AWARE)
- [ ] Executable directory config takes precedence over system config **in both dev and compiled environments**
- [ ] CLI arguments override executable directory config
- [ ] Fallback to system locations when no executable directory config
- [ ] Config file format validation (YAML/JSON)
- [ ] **CRITICAL**: PyInstaller executable finds co-located config files
- [ ] **CRITICAL**: Config discovery works when executable run from different working directory
- [ ] Development environment still works with existing behavior

### 2. Database Path Tests
- [ ] Config file parsing with database_path
- [ ] Environment variable override (lowest priority)
- [ ] Command-line argument override (highest priority)
- [ ] Priority resolution validation

### 3. Path Resolution Tests (EXECUTABLE-SAFE)
- [ ] Tilde expansion works in both dev and compiled environments
- [ ] **CRITICAL**: Relative path resolution relative to executable directory, NOT working directory
- [ ] Absolute path handling unchanged
- [ ] Directory auto-creation with fallback to user data directory
- [ ] Permission error handling with graceful fallback
- [ ] **CRITICAL**: Multi-instance isolation - relative paths resolve to different locations per executable copy
- [ ] Cross-platform path resolution (Windows, macOS, Linux)

### 4. Error Handling Tests
- [ ] Invalid path with existing default database
- [ ] Invalid path without existing default database
- [ ] Permission denied scenarios
- [ ] Non-existent parent directories
- [ ] Clear error source attribution (config file vs CLI)

### 5. Integration Tests (EXECUTABLE-FOCUSED)
- [ ] **CRITICAL**: Multiple executable instances with separate configs work independently
- [ ] CLI tool with executable directory config in PyInstaller environment
- [ ] Web server with executable directory config in PyInstaller environment
- [ ] Config override behavior validation in compiled executables
- [ ] **CRITICAL**: Executable moved to different directory still finds co-located config
- [ ] **CRITICAL**: Working directory changes don't affect config discovery
- [ ] Resource path resolution for templates and static files in executable environment

## Documentation Updates

### 1. Configuration Documentation
- Document executable directory config priority
- Update config file examples
- Document new environment variable
- Explain multi-instance setup patterns

### 2. Command-Line Help
- Add --database-path to both applications
- Include examples in help text

### 3. Multi-Instance Guide
- Document directory-based instance separation
- Provide setup examples for different use cases
- Explain data isolation guarantees

## Security Considerations

### 1. Path Traversal Protection
- Validate resolved paths don't escape intended boundaries
- Log path resolution for audit trail

### 2. Permission Handling
- Graceful handling of permission errors
- Clear error messages for permission issues

### 3. Data Isolation
- Ensure separate instances don't interfere
- No automatic cross-database operations
- Clear config source attribution in errors

## Backward Compatibility

### 1. Existing Installations
- **No breaking changes**: Existing behavior unchanged when no executable directory config
- **Default behavior preserved**: Regular users unaffected
- **Configuration migration**: Existing system configs continue working

### 2. API Compatibility
- **DatabaseManager constructor**: Backward compatible with optional parameters
- **Configuration structure**: Additive changes only

## Success Criteria

### 1. Functional Requirements
- [ ] Config file in executable directory automatically detected and used
- [ ] Power users can run multiple isolated instances
- [ ] Regular users experience no change in behavior
- [ ] Both CLI and web applications support the same config behavior

### 2. Quality Requirements
- [ ] Clear error messages guide problem resolution with config source info
- [ ] Path resolution handles edge cases gracefully
- [ ] No data loss or corruption scenarios
- [ ] Comprehensive test coverage

### 3. User Experience
- [ ] Zero-configuration multi-instance setup for power users
- [ ] Regular users remain completely unaffected
- [ ] Error scenarios provide actionable guidance with clear source attribution
- [ ] Configuration follows intuitive directory-based patterns

## Implementation Phases

### Phase 1: Implement Executable-Aware Configuration Discovery (CRITICAL)
1. **Replace** current CWD-based config discovery with executable directory detection
2. Implement `ExecutableAwareConfigManager` with PyInstaller detection
3. Add comprehensive testing for both development and compiled environments
4. **CRITICAL**: Validate config discovery works when CWD != executable directory

### Phase 2: Database Path Configuration
1. Extend ProcessingConfig with database_path field
2. Add environment variable support
3. Update ConfigManager validation

### Phase 3: Database Manager Updates (EXECUTABLE-AWARE)
1. Modify DatabaseManager constructor to accept executable-aware path resolution
2. **Replace** current path resolution with executable-aware logic
3. Add robust error handling with fallback to user data directories
4. Implement source attribution and detailed error messages

### Phase 4: Command-Line Integration
1. Add --database-path to both applications
2. Integrate with existing argument parsing
3. Wire up to DatabaseManager with proper priority

### Phase 5: Testing and Documentation (EXECUTABLE-FOCUSED)
1. **CRITICAL**: Build and test actual PyInstaller executable with config discovery
2. Comprehensive test suite covering both development and compiled environments
3. Multi-instance testing with actual executable copies
4. Update documentation with executable-specific setup patterns
5. Validate resource path resolution for web assets in executable environment

## Executable Compatibility Summary

This specification has been **completely refactored** to ensure compatibility with PyInstaller and other executable compilation systems. Key changes:

### ✅ **FIXED: Critical Executable Issues**
- **Config Discovery**: Uses `sys.executable` location, not current working directory
- **Path Resolution**: Relative paths resolve against executable directory, not CWD
- **Multi-Instance Support**: Each executable copy operates independently with co-located configs
- **Error Handling**: Graceful fallback to user data directories for permission issues
- **Cross-Platform**: Proper user data directory detection for Windows, macOS, Linux

### 🔧 **Implementation Requirements**
- Must use `ExecutableAwareConfigManager` class with PyInstaller detection
- Must implement executable-aware path resolution for all relative paths
- Must test extensively with actual compiled executables, not just development environment
- Must handle resource paths for web templates and static files in executable context

### 🎯 **Success Criteria (Executable-Validated)**
- Power users can copy executable + config file to create isolated instances
- Config discovery works regardless of working directory when executable is run
- Relative database paths resolve correctly in compiled executable environment
- No "config file not found" errors when config exists next to executable

This specification now ensures the "paramount requirement" of automatic executable directory config detection **will actually work** in compiled executable environments.