#!/bin/bash
# ABOUTME: Test script for safely running the executable without interfering with production WorkJournalMaker
# ABOUTME: Creates isolated test environment with separate config, data, and logs

set -e

echo "🧪 Setting up safe executable test environment..."

# Create test directories
TEST_BASE="$HOME/Desktop/workjournal-executable-test"
mkdir -p "$TEST_BASE"/{worklogs,summaries,logs}

# Create test config in user directory (not in repo)
TEST_CONFIG="$HOME/.config/work-journal-summarizer/test-config.yaml"

cat > "$TEST_CONFIG" << 'EOF'
# Test configuration for executable - isolated from production
llm:
  provider: google_genai

google_genai:
  project: geminijournal-463220
  location: us-central1
  model: gemini-2.0-flash-001

processing:
  base_path: ~/Desktop/workjournal-executable-test/worklogs/
  output_path: ~/Desktop/workjournal-executable-test/summaries/
  max_file_size_mb: 50

logging:
  level: INFO
  console_output: true
  file_output: true
  log_dir: ~/Desktop/workjournal-executable-test/logs/
EOF

echo "✅ Test configuration created at: $TEST_CONFIG"

# Create sample test journal file
SAMPLE_JOURNAL="$TEST_BASE/worklogs/worklogs_2024/worklogs_2024-08/week_ending_2024-08-30/worklog_2024-08-27.txt"
mkdir -p "$(dirname "$SAMPLE_JOURNAL")"

cat > "$SAMPLE_JOURNAL" << 'EOF'
## Tuesday 2024-08-27

### Morning
- Worked on FastAPI desktop app packaging
- Created PyInstaller configuration
- Set up testing environment

### Afternoon  
- Debugged port detection system
- Implemented safety measures for executable testing
- Created isolated test configuration

### End of Day
Successfully created safe testing environment for WorkJournalMaker executable.
EOF

echo "✅ Sample journal created at: $SAMPLE_JOURNAL"

# Show the test setup
echo ""
echo "🎯 Test Environment Ready:"
echo "  Config file: $TEST_CONFIG" 
echo "  Test data: $TEST_BASE"
echo "  Sample journal: $SAMPLE_JOURNAL"
echo ""
echo "🚀 Now you can safely test your executable:"
echo "  1. Run your executable (it will auto-detect port 8100+)"
echo "  2. Your production instance stays on port 8000"
echo "  3. All test data is isolated in separate directories"
echo ""
echo "🧹 To cleanup test environment:"
echo "  rm -rf '$TEST_BASE'"
echo "  rm '$TEST_CONFIG'"