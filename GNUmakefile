# Convenience Makefile wrapper for McRogueFace
# This delegates to CMake build in the build directory

.PHONY: all build clean run test dist help

# Default target
all: build

# Build the project
build:
	@./build.sh

# Clean build artifacts  
clean:
	@./clean.sh

# Run the game
run: build
	@cd build && ./mcrogueface

# Run in Python mode
python: build
	@cd build && ./mcrogueface -i

# Test basic functionality
test: build
	@echo "Testing McRogueFace..."
	@cd build && ./mcrogueface -V
	@cd build && ./mcrogueface -c "print('Test passed')"
	@cd build && ./mcrogueface --headless -c "import mcrfpy; print('mcrfpy imported successfully')"

# Create distribution archive
dist: build
	@echo "Creating distribution archive..."
	@cd build && zip -r ../McRogueFace-$$(date +%Y%m%d).zip . -x "*.o" "CMakeFiles/*" "Makefile" "*.cmake"
	@echo "Distribution archive created: McRogueFace-$$(date +%Y%m%d).zip"

# Show help
help:
	@echo "McRogueFace Build System"
	@echo "======================="
	@echo ""
	@echo "Available targets:"
	@echo "  make          - Build the project (default)"
	@echo "  make build    - Build the project"
	@echo "  make clean    - Remove all build artifacts"
	@echo "  make run      - Build and run the game"
	@echo "  make python   - Build and run in Python interactive mode"
	@echo "  make test     - Run basic tests"
	@echo "  make dist     - Create distribution archive"
	@echo "  make help     - Show this help message"
	@echo ""
	@echo "Build output goes to: ./build/"
	@echo "Distribution archives are created in project root"