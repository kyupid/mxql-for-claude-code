---
name: mxql
description: Complete MXQL (Metrics Query Language) toolkit for generating, analyzing, validating, and testing queries. Supports conversational query generation, automated validation, comprehensive analysis with optimization suggestions, and test query generation with sample data. Use this for all MXQL-related tasks including creating queries, debugging, optimization, and testing.
---

# MXQL Query Toolkit

## Overview

This skill provides a complete toolkit for working with MXQL (Metrics Query Language), WhaTap's query language for metrics monitoring. It combines four key capabilities:

1. **🔧 Query Generation**: Conversational, step-by-step query creation
2. **🔍 Query Analysis**: Syntax validation, semantic checks, performance optimization
3. **✅ Automated Validation**: Python-based syntax validator (no Java required)
4. **🧪 Test Query Generation**: Create testable queries with ADDROW sample data

**Supported Domains**:
- Database monitoring (MySQL, PostgreSQL, Oracle, MongoDB, Redis, etc.)
- Infrastructure monitoring
- APM (Application Performance Monitoring)
- Container and Cloud monitoring

## When to Use This Skill

### For Query Generation
Activate when users:
- Request to "create", "generate", or "make" an MXQL query
- Ask to "query metrics" or "monitor performance"
- Need help selecting categories, fields, or syntax
- Want to find specific metrics (CPU, memory, sessions, etc.)

**Examples**:
- "Create MXQL query for MySQL CPU usage"
- "Generate query to find high memory DB instances"
- "How do I query PostgreSQL active sessions?"

### For Query Analysis
Activate when users:
- Provide an MXQL query and ask "is this correct?"
- Want to "analyze", "review", "debug", or "check" a query
- Ask "why isn't this query working?"
- Request query optimization or performance improvements

**Examples**:
- "Analyze this MXQL query"
- "What's wrong with my query?"
- "Optimize this MXQL"

### For Testing
Activate when users:
- Ask "how can I test this query?"
- Request example data or test scenarios
- Want to validate query results before production

## Core Capabilities

### 1. Query Generation 🔧

**Conversational Approach**: Guide users through query creation step-by-step.

**Quick Start**:
```
1. Understand intent (What, Where, How, When)
2. Clarify product/category if ambiguous
3. Suggest relevant fields and filters
4. Generate query with explanations
5. Offer test query version
```

**Detailed Guide**: See [generating-guide.md](generating-guide.md)

---

### 2. Query Analysis 🔍

**Comprehensive Review**: Syntax, semantics, performance, best practices.

**Quick Start**:
```python
# Step 1: Automated validation
from mxql_validator import MXQLValidator, format_validation_result
validator = MXQLValidator()
is_valid, issues = validator.validate(query)
print(format_validation_result(is_valid, issues))

# Step 2: Manual deep analysis (if needed)
# Step 3: Offer test query generation
```

**Analysis Levels**:
- **Quick Check**: Syntax + critical errors
- **Standard**: + Performance issues + Best practices
- **Deep Dive**: + Optimization alternatives + Security

**Detailed Guide**: See [analyzing-guide.md](analyzing-guide.md)

---

### 3. Automated Validation ✅

**Python Validator** (`mxql_validator.py`): Fast syntax validation without Java.

**Features**:
- Bracket/brace balance checking
- Command order validation
- Semantic error detection (UPDATE without GROUP, etc.)
- Performance issue identification
- Best practice suggestions

**Usage**:
```python
from mxql_validator import MXQLValidator, format_validation_result

validator = MXQLValidator()
is_valid, issues = validator.validate(query_text)
result = format_validation_result(is_valid, issues)
```

**Output**:
```
✅ Query is valid (0 critical, 1 warning, 2 info)

🟡 Warnings:
  Line 5: LIMIT without ORDER - results may be arbitrary
```

---

### 4. Test Query Generation 🧪

**Test Generator** (`test_query_generator.py`): Create testable queries with ADDROW.

**Features**:
- Automatic sample data generation
- Field extraction from query
- Comprehensive testing guide
- Customization instructions

**Usage**:
```python
from test_query_generator import TestQueryGenerator

generator = TestQueryGenerator()

# Generate test query with sample data
test_query = generator.generate_simple_test_example(original_query)

# Or comprehensive testing guide
guide = generator.generate_test_guide(original_query)
```

**Output Example**:
```mxql
SUB {id: test_data}
ADDROW {'time':1700000000000, 'oid':1000, 'oname':'server-1', 'cpu':50}
ADDROW {'time':1700000060000, 'oid':1001, 'oname':'server-2', 'cpu':75}
END

CATEGORY db_mysql_counter
TAGLOAD
APPEND {query: test_data}
SELECT [oname, cpu]
ORDER {key: [cpu], sort: "desc"}
LIMIT 10
```

## Workflow Examples

### Workflow 1: Generate + Validate + Test

```
User: "Create MXQL query for MySQL high CPU instances"
Claude: [Activates mxql skill - Generation mode]

Step 1: Understanding intent
- What: CPU usage
- Where: MySQL
- How: Find high CPU instances (Top-N query)
- When: Current

Step 2: Generate query
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos), mem_pct]
FILTER {key: "cpu(xos)", cmp: "gt", value: "70"}
ORDER {key: [cpu(xos)], sort: "desc"}
LIMIT 10
```

Step 3: Validate automatically
✅ Query is valid!

Step 4: Offer test query
"Would you like a test version with sample data?"
```

### Workflow 2: Analyze + Fix + Test

```
User: "Analyze this query: [pastes MXQL with errors]"

Claude: [Activates mxql skill - Analysis mode]

Step 1: Automated validation
❌ Query has critical issues (2 critical, 1 warning)

🔴 Critical Issues:
  Line 3: UPDATE without preceding GROUP

Step 2: Provide corrected query
Step 3: Generate test version of corrected query
```

### Workflow 3: Test Query Generation Only

```
User: "Generate test query for this MXQL"

Claude: [Uses test_query_generator.py]
[Provides comprehensive testing guide with ADDROW examples]
```

## Reference Files

For detailed documentation:

- **[generating-guide.md](generating-guide.md)** - Complete query generation guide
  - Conversational workflow
  - Category and field selection
  - Common patterns and examples
  
- **[analyzing-guide.md](analyzing-guide.md)** - Complete analysis guide
  - Validation rules
  - Performance optimization patterns
  - Common issues and solutions

- **[analysis-checklist.md](analysis-checklist.md)** - Validation checklist
- **[optimization-patterns.md](optimization-patterns.md)** - Performance patterns
- **[common-issues.md](common-issues.md)** - Troubleshooting guide

## Python Utilities

- **`mxql_validator.py`** - Automated syntax validator
- **`test_query_generator.py`** - Test query generator

## Best Practices

### When Generating Queries
1. Always clarify ambiguous requirements
2. Suggest relevant fields based on intent
3. Include explanatory comments in generated queries
4. Offer test query version
5. Validate generated query before providing

### When Analyzing Queries
1. Run automated validation first
2. Report issues by severity (Critical → Warning → Info)
3. Provide corrected/optimized versions
4. Explain trade-offs in optimizations
5. Always offer test query generation

### When Testing
1. Generate realistic sample data
2. Provide customization examples
3. Include expected results
4. Give troubleshooting tips

## Quick Commands

```
# Validate query
python mxql_validator.py < query.mxql

# Generate test query
python test_query_generator.py < query.mxql
```

## Integration

This skill integrates all MXQL operations:
- **Generate** → Auto-validate → Offer test version
- **Analyze** → Auto-validate → Fix → Offer test version  
- **Test** → Generate ADDROW patterns → Provide guide

The goal is to provide end-to-end support for MXQL query development, from creation to testing.
