#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing MXQL skill for Claude Code...${NC}"

# Get the script directory (where this install.sh is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$HOME/.claude/skills"
TARGET_DIR="$SKILLS_DIR/mxql"

# Check if .claude/skills directory exists
if [ ! -d "$SKILLS_DIR" ]; then
    echo -e "${YELLOW}Creating $SKILLS_DIR directory...${NC}"
    mkdir -p "$SKILLS_DIR"
fi

# Remove existing mxql directory or symlink
if [ -e "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Removing existing $TARGET_DIR...${NC}"
    rm -rf "$TARGET_DIR"
fi

# Create symlink
echo -e "${GREEN}Creating symlink: $TARGET_DIR -> $SCRIPT_DIR${NC}"
ln -s "$SCRIPT_DIR" "$TARGET_DIR"

# Verify installation
if [ -L "$TARGET_DIR" ] && [ -e "$TARGET_DIR" ]; then
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo ""
    echo "MXQL skill is now available in Claude Code."
    echo ""
    echo "Try asking:"
    echo "  - \"MySQL CPU 사용량 조회하는 MXQL 만들어줘\""
    echo "  - \"Analyze this MXQL query\""
    echo "  - \"Generate test query with sample data\""
else
    echo -e "${YELLOW}❌ Installation failed. Please check permissions.${NC}"
    exit 1
fi
