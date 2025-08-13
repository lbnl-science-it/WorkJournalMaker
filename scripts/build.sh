#!/bin/bash

# ABOUTME: Shell wrapper for Python build scripts
# ABOUTME: Provides quick command-line access to build functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build     - Standard build (default)"
    echo "  quick     - Quick build for development"
    echo "  clean     - Clean build with full validation"
    echo "  test      - Test existing executable"
    echo "  help      - Show this help"
    echo ""
    echo "Options (passed to Python scripts):"
    echo "  --clean   - Clean before building"
    echo "  --debug   - Enable debug mode"
    echo "  --verbose - Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                    # Standard build"
    echo "  $0 quick              # Quick development build"
    echo "  $0 build --clean      # Clean standard build"
    echo "  $0 clean              # Full clean build"
    echo "  $0 test               # Test existing executable"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 not found${NC}"
        exit 1
    fi
}

run_build() {
    echo -e "${BLUE}Running standard build...${NC}"
    python3 "$SCRIPT_DIR/build.py" "$@"
}

run_quick() {
    echo -e "${YELLOW}Running quick build...${NC}"
    python3 "$SCRIPT_DIR/build_quick.py" "$@"
}

run_clean() {
    echo -e "${GREEN}Running clean build...${NC}"
    python3 "$SCRIPT_DIR/build_clean.py" "$@"
}

run_test() {
    echo -e "${BLUE}Testing executable...${NC}"
    python3 "$SCRIPT_DIR/build_test.py" "$@"
}

main() {
    check_python
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Handle command
    case "${1:-build}" in
        build)
            shift
            run_build "$@"
            ;;
        quick)
            shift
            run_quick "$@"
            ;;
        clean)
            shift
            run_clean "$@"
            ;;
        test)
            shift
            run_test "$@"
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

main "$@"