---
name: analyzing-mxql-queries
description: Analyzes MXQL (Metrics Query Language) queries for syntax errors, semantic issues, performance problems, and optimization opportunities. Use this when users provide an MXQL query and want it reviewed, debugged, optimized, or explained. Provides detailed analysis with severity levels (Critical, Warning, Info) and actionable recommendations.
---

# MXQL Query Analyzer

## Overview

This skill performs comprehensive analysis of MXQL queries to identify:
- **Syntax errors**: Invalid command structure, missing fields, malformed JSON
- **Semantic issues**: Logical errors, invalid field references, wrong command order
- **Performance problems**: Inefficient patterns, missing indexes, excessive data processing
- **Optimization opportunities**: Better approaches, query simplification, best practices
- **Security concerns**: Potential vulnerabilities or risky patterns

## When to Use This Skill

Activate this skill when users:
- Provide an MXQL query and ask "is this correct?"
- Want to "analyze", "review", "debug", or "check" an MXQL query
- Ask "why isn't this query working?"
- Request "optimize this MXQL query"
- Want explanation of what a query does
- Need help troubleshooting query errors

**Examples of triggering requests**:
- "Analyze this MXQL query"
- "What's wrong with this query?"
- "Can you review my MXQL?"
- "Optimize this query for me"
- "Explain what this MXQL does"
- "Debug this query"

## New Features

### 🔍 Automated Syntax Validation

This skill includes a Python-based MXQL validator (`mxql_validator.py`) that:
- Validates syntax without requiring Java runtime
- Checks bracket/brace balance
- Identifies command order issues
- Detects semantic errors
- Provides best practice suggestions

**When to use**:
- Before running manual analysis for quick syntax check
- When user explicitly asks for validation
- As part of automated query review

**Usage**:
```python
from mxql_validator import MXQLValidator, format_validation_result

validator = MXQLValidator()
is_valid, issues = validator.validate(query_text)
result = format_validation_result(is_valid, issues)
```

### 🧪 Test Query Generation

This skill includes a test query generator (`test_query_generator.py`) that:
- Creates testable queries using ADDROW pattern
- Generates sample data based on query fields
- Provides testing guide with examples
- Explains how to customize test data

**When to use**:
- After analyzing a query, offer to generate test version
- When user asks "how can I test this?"
- When providing query examples or tutorials

**Usage**:
```python
from test_query_generator import TestQueryGenerator

generator = TestQueryGenerator()

# Generate test query with sample data
test_query = generator.generate_simple_test_example(original_query)

# Or generate comprehensive testing guide
guide = generator.generate_test_guide(original_query)
```

## Analysis Workflow

Follow this enhanced 7-step analysis process:

### Step 0: Quick Validation (New!)

Before deep analysis, run automated validation:
```python
validator = MXQLValidator()
is_valid, issues = validator.validate(query)
```

If critical issues found, report them immediately. Otherwise, proceed with manual analysis.

### Step 1: Parse Query Structure

Extract and identify all commands in the query:
- List all commands in order
- Identify data loading commands (CATEGORY, TAGLOAD)
- Identify filtering commands (FILTER, TIMEFILTER)
- Identify aggregation commands (GROUP, UPDATE)
- Identify output commands (ORDER, LIMIT)

**Output Example**:
```
Query Structure:
1. CATEGORY db_mysql_counter
2. TAGLOAD
3. SELECT [oname, cpu(xos)]
4. FILTER {key: "cpu(xos)", cmp: "gt", value: "80"}
5. LIMIT 10
```

### Step 2: Syntax Validation

Check for syntax errors:
- ✅ All braces `{}` and brackets `[]` properly closed
- ✅ Valid JSON structure in parameters
- ✅ Valid command names
- ✅ Required parameters present

**Severity Levels**:
- 🔴 **Critical**: Query will fail to execute
- 🟡 **Warning**: Query may produce unexpected results
- 🔵 **Info**: Minor improvements possible (e.g., readability, best practices)

**Note on Quoting**:
- Field names can be used with or without quotes (both valid)
- However, using quotes (single or double) is recommended for better readability
- This is a best practice suggestion, not a syntax requirement

### Step 3: Semantic Validation

Check for logical errors:
- ✅ CATEGORY specified before data loaders
- ✅ Data loader present (TAGLOAD, FLEX-LOAD, etc.)
- ✅ UPDATE only appears after GROUP
- ✅ Field names valid for the category (if category is known)
- ✅ No conflicting operations
- ✅ Subqueries defined before JOIN

### Step 4: Performance Analysis

Identify performance issues:
- ⚠️ FILTER applied after GROUP (should filter early)
- ⚠️ SELECT * used (select only needed fields)
- ⚠️ No LIMIT for potentially large results
- ⚠️ Excessive time range without filters
- ⚠️ Multiple aggregations without clear purpose

### Step 5: Optimization Opportunities

Suggest improvements:
- 💡 Use ORDER before LIMIT for Top-N queries
- 💡 Combine multiple FILTER into single expr
- 💡 Use CREATE for calculated metrics instead of post-processing
- 💡 Choose appropriate timeunit for GROUP
- 💡 Add early filters to reduce data volume

### Step 6: Generate Report

Provide structured analysis with:
1. **Summary**: Overall assessment (Good / Needs Review / Has Issues)
2. **Issues Found**: Categorized by severity
3. **Optimization Suggestions**: Prioritized recommendations
4. **Corrected Query**: If syntax/semantic errors found
5. **Explanation**: What the query does in plain language

### Step 7: Offer Testing Options (New!)

After analysis, always offer testing guidance:

**For Valid Queries**:
```python
generator = TestQueryGenerator()
test_guide = generator.generate_test_guide(query)
```

Provide:
1. Test query with ADDROW sample data
2. Instructions on how to customize test data
3. Expected results based on the query
4. Troubleshooting tips

**For Corrected Queries**:
1. Show corrected query
2. Generate test version of corrected query
3. Explain what changed and why
4. Provide testing instructions

**Example Output**:
```
Would you like me to generate a test query? I can create an MXQL query
with ADDROW that includes sample data, so you can test this query without
needing access to real data sources.
```

## Analysis Categories

### 1. Syntax Analysis

**What to check**:
- Braces and brackets balance
- String quoting
- JSON validity
- Command name spelling
- Parameter completeness

**Common Syntax Errors**:
```mxql
# Error: Missing bracket
SELECT oname, cpu(xos)
# Fix:
SELECT [oname, cpu(xos)]

# Error: Unclosed brace
FILTER {key: "cpu", cmp: "gt", value: "80"
# Fix:
FILTER {key: "cpu", cmp: "gt", value: "80"}

# Error: Wrong command name
FILTER {key: "cpu", operator: "gt", value: "80"}
# Fix (use 'cmp' not 'operator'):
FILTER {key: "cpu", cmp: "gt", value: "80"}

# Note: Field names and quotes
FILTER {key: status, value: "active"}  # Valid (no quotes)
FILTER {key: "status", value: "active"}  # Better (with quotes - recommended for readability)
FILTER {key: 'status', value: 'active'}  # Also valid (single quotes)
```

### 2. Semantic Analysis

**What to check**:
- Command execution order
- Dependencies between commands
- Field existence (if category known)
- Parameter value validity
- Logical consistency

**Common Semantic Errors**:
```mxql
# Error: UPDATE without GROUP
CATEGORY app_counter
TAGLOAD
UPDATE {key: "count", value: "sum"}

# Fix: Add GROUP first
CATEGORY app_counter
TAGLOAD
GROUP {timeunit: "5m"}
UPDATE {key: "count", value: "sum"}

# Note: UPDATE key parameter is optional
UPDATE {value: "sum"}  # Valid - applies sum to all numeric fields
UPDATE {key: "count", value: "sum"}  # Also valid - applies sum to specific field

# Error: No data loader
CATEGORY app_counter
FILTER {key: "oid", value: "1001"}

# Fix: Add TAGLOAD
CATEGORY app_counter
TAGLOAD
FILTER {key: "oid", value: "1001"}

# Error: JOIN without SUB definition
CATEGORY metrics
TAGLOAD
JOIN {query: "services", pk: ["oid"]}

# Fix: Define SUB first
SUB services
  CATEGORY service_list
  TAGLOAD
END

CATEGORY metrics
TAGLOAD
JOIN {query: "services", pk: ["oid"]}
```

### 3. Performance Analysis

**What to check**:
- Filter placement (early vs late)
- Field selection (specific vs all)
- Result limiting
- Time range appropriateness
- Aggregation efficiency

**Performance Issues**:
```mxql
# Issue: Late filtering (processes more data)
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos), memory, disk, network, ...]
GROUP {timeunit: "5m"}
FILTER {key: "oid", value: ["1001"]}

# Better: Early filtering
CATEGORY db_mysql_counter
TAGLOAD
FILTER {key: "oid", value: ["1001"]}
SELECT [oname, cpu(xos)]
GROUP {timeunit: "5m"}

# Issue: No LIMIT for Top-N
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
ORDER {key: [tx_count], sort: "desc"}

# Better: Add LIMIT
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
ORDER {key: [tx_count], sort: "desc"}
LIMIT 10

# Issue: SELECT * (unnecessary fields)
CATEGORY db_postgresql_counter
TAGLOAD
SELECT [*]
GROUP {timeunit: "1h"}

# Better: Select only needed fields
CATEGORY db_postgresql_counter
TAGLOAD
SELECT [oname, cpu(xos), mem_pct]
GROUP {timeunit: "1h"}
```

### 4. Best Practices Validation

**What to check**:
- ORDER before LIMIT for Top-N
- Meaningful GROUP timeunit
- Appropriate field selection
- Calculated metrics using CREATE
- Clear query structure

**Best Practice Violations**:
```mxql
# Issue: LIMIT without ORDER (arbitrary results)
CATEGORY db_oracle_counter
TAGLOAD
SELECT [oname, cpu(xos)]
LIMIT 10

# Better: Add ORDER
CATEGORY db_oracle_counter
TAGLOAD
SELECT [oname, cpu(xos)]
ORDER {key: [cpu(xos)], sort: "desc"}
LIMIT 10

# Issue: Multiple redundant SELECT
CATEGORY metrics
TAGLOAD
SELECT [oid, time, cpu, memory, disk]
SELECT [oid, cpu]

# Better: Single SELECT
CATEGORY metrics
TAGLOAD
SELECT [oid, cpu]
```

## Output Format

Provide analysis in this structured format:

```
## MXQL Query Analysis

### Summary
[Good / Needs Review / Has Critical Issues]

### Query Structure
[List of commands]

### Issues Found

#### 🔴 Critical Issues (Must Fix)
1. [Issue description]
   - Location: [Command or line]
   - Problem: [What's wrong]
   - Fix: [How to fix]

#### 🟡 Warnings (Should Fix)
1. [Issue description]
   - Impact: [Performance/correctness impact]
   - Suggestion: [How to improve]

