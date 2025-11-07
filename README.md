# MXQL for Claude Code

Claude Code skill for MXQL (Metrics Query Language) - WhaTap's query language for monitoring metrics.

## What is this?

A complete toolkit for working with MXQL queries in Claude Code:
- 🔧 **Query Generation** - Conversational query creation
- 🔍 **Query Analysis** - Syntax validation and optimization
- ✅ **Auto Validation** - Python-based validator (no Java required)
- 🧪 **Test Generation** - Create testable queries with sample data

## Installation

```bash
./install.sh
```

This will create a symlink from `~/.claude/skills/mxql` to this directory.

## Example Questions

### Query Generation
1. "MySQL CPU 사용량 조회하는 MXQL 만들어줘"
2. "PostgreSQL에서 active session이 많은 인스턴스 찾는 쿼리 생성해줘"
3. "Create MXQL query for high memory DB instances"

### Query Analysis
4. "이 MXQL 쿼리 분석해줘"
5. "내 쿼리에 문제가 있는지 체크해줘"
6. "Optimize this MXQL query for better performance"

### Testing
7. "이 쿼리 테스트할 수 있는 버전 만들어줘"
8. "Generate test query with sample data"

### Combined
9. "DB CPU 높은 거 찾는 쿼리 만들고 테스트 버전도 같이 만들어줘"
10. "MXQL query for Oracle top 10 by memory usage, with validation"

## Features

- **No Java Required**: Python-based validation works standalone
- **ADDROW Pattern**: Test queries without real data sources
- **Best Practices**: Follows MXQL optimization patterns
- **Comprehensive**: Generation + Analysis + Testing in one skill

## Structure

```
mxql/
├── SKILL.md                    # Main skill definition
├── mxql_validator.py           # Python validator
├── test_query_generator.py     # Test query generator
├── generating-guide.md         # Query generation guide
├── analyzing-guide.md          # Analysis guide
├── analysis-checklist.md       # Validation rules
├── optimization-patterns.md    # Performance patterns
└── common-issues.md           # Troubleshooting
```

## License

MIT
