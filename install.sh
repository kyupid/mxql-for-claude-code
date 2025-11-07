#!/bin/bash

# MXQL Skill for Claude Code - Installation Script
# This script installs the skill to your personal Claude skills directory

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎯 MXQL Skill for Claude Code - Installer"
echo "=============================================="
echo ""

# Create skills directory if it doesn't exist
if [ ! -d "$SKILLS_DIR" ]; then
    echo "📁 Creating Claude skills directory at $SKILLS_DIR"
    mkdir -p "$SKILLS_DIR"
else
    echo "✓ Claude skills directory exists"
fi

echo ""
echo "📦 Installing skill..."
echo ""

# Install mxql skill
if [ -d "$SKILLS_DIR/mxql" ]; then
    echo "⚠️  mxql skill already exists"
    read -p "   Overwrite? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$SKILLS_DIR/mxql"
        ln -s "$SCRIPT_DIR/mxql" "$SKILLS_DIR/mxql"
        echo "   ✓ Updated mxql skill"
    else
        echo "   ⏭️  Skipped mxql skill"
    fi
else
    ln -s "$SCRIPT_DIR/mxql" "$SKILLS_DIR/mxql"
    echo "✓ Installed mxql skill"
fi

echo ""
echo "=============================================="
echo "✅ Installation complete!"
echo ""
echo "Skill installed to: $SKILLS_DIR"
echo ""
echo "📚 Available skill:"
echo "  - mxql: 🌟 Complete MXQL toolkit (generate + analyze + test)"
echo ""
echo "🚀 Usage:"
echo "  Open Claude Code and start using the skill!"
echo ""
echo "  🔧 Query Generation:"
echo "    'MySQL CPU 사용량 조회하는 MXQL 만들어줘'"
echo "    'Create MXQL for PostgreSQL high memory instances'"
echo ""
echo "  🔍 Query Analysis:"
echo "    'Analyze this MXQL query'"
echo "    '내 쿼리 최적화해줘'"
echo ""
echo "  🧪 Testing:"
echo "    'Generate test query with sample data'"
echo "    '이 쿼리 테스트할 수 있게 만들어줘'"
echo ""
echo "📖 See README.md for more information"
echo ""
