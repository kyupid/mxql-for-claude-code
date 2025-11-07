# MXQL Analysis Checklist

Comprehensive validation rules for MXQL query analysis. Use this checklist to systematically verify query correctness.

## Table of Contents

1. [General Query Structure](#general-query-structure)
2. [Command-Specific Validation](#command-specific-validation)
3. [Syntax Validation Rules](#syntax-validation-rules)
4. [Semantic Validation Rules](#semantic-validation-rules)
5. [Performance Validation Rules](#performance-validation-rules)
6. [Security Validation Rules](#security-validation-rules)

---

## General Query Structure

### Overall Structure Checks

- [ ] Query has at least one command
- [ ] Query starts with data loading (CATEGORY + TAGLOAD or similar)
- [ ] Commands are in logical execution order
- [ ] No duplicate commands (unless intentional, e.g., multiple FILTER)
- [ ] All opened blocks (SUB...END) are properly closed
- [ ] No circular dependencies in subqueries

### Required Elements

- [ ] **Data Source**: CATEGORY command present
- [ ] **Data Loader**: At least one of: TAGLOAD, FLEX-LOAD, KV-LOAD, etc.
- [ ] **Optional but common**: SELECT, FILTER, GROUP, ORDER, LIMIT

### Execution Flow Validation

```
Valid Order:
CATEGORY → Data Loader → FILTER → SELECT → GROUP → UPDATE → ORDER → LIMIT

Check:
- CATEGORY before data loaders? ✓
- UPDATE only after GROUP? ✓
- ORDER before LIMIT (for Top-N)? ✓
- FILTER before GROUP (for performance)? ✓
```

---

## Command-Specific Validation

### CATEGORY

**Syntax**:
```mxql
CATEGORY <category_name>
CATEGORY $PARAM_NAME
```

**Checks**:
- [ ] Category name is present (not empty)
- [ ] Category name is valid identifier or parameter
- [ ] If parameter: starts with $ and valid format
- [ ] Category appears before data loaders (best practice)

**Common Issues**:
- Missing category name: `CATEGORY`
- Typo in category name: `CATEGORY db_mysqll_counter`
- Missing CATEGORY entirely

### TAGLOAD

**Syntax**:
```mxql
TAGLOAD
TAGLOAD {options}
```

**Checks**:
- [ ] Appears after CATEGORY
- [ ] If options provided: valid JSON object
- [ ] Valid options: backward, oid, okind, onode
- [ ] Option values are correct types (boolean, array)

**Common Issues**:
- Missing TAGLOAD: Query has CATEGORY but no data loader
- Invalid options: `TAGLOAD {invalid_option: true}`

### SELECT

**Syntax**:
```mxql
SELECT [field1, field2, ...]
SELECT [*]
SELECT [pattern*]
```

**Checks**:
- [ ] Wrapped in brackets `[...]`
- [ ] Field names are strings or patterns
- [ ] No trailing commas in list
- [ ] Pattern syntax valid (`*`, `field*`, `*field`, `-field`)
- [ ] At least one field specified (unless `[*]`)

**Common Issues**:
- Missing brackets: `SELECT oname, cpu`
- Empty SELECT: `SELECT []`
- Trailing comma: `SELECT [oname, cpu,]`

### FILTER

**Syntax Forms**:
```mxql
# Equality
FILTER {key: "field", value: "value"}
FILTER {key: "field", value: ["v1", "v2"]}

# Comparison
FILTER {key: "field", cmp: "operator", value: "value"}

# Expression
FILTER {expr: "expression"}

# Pattern
FILTER {key: "field", like: "pattern"}

# Exclusion
FILTER {key: "field", exclude: "value"}

# Existence
FILTER {key: "field", exist: true/false}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has required fields based on filter type
- [ ] Comparison operators are valid: eq, ne, gt, gte, lt, lte
- [ ] Expression syntax is valid (if using expr)
- [ ] No conflicting parameters (e.g., value and expr together)

**Best Practice**:
- [ ] Field names are quoted for better readability (optional but recommended)

**Required Field Combinations**:
- Equality filter: `key` + `value` (required)
- Comparison filter: `key` + `cmp` + `value` (required)
- Expression filter: `expr` (required)
- Pattern filter: `key` + `like` (required)
- Exclusion filter: `key` + `exclude` (required)
- Existence filter: `key` + `exist` (required)

**Common Issues**:
- Wrong operator: `FILTER {key: "cpu", operator: ">", value: "80"}` (use 'cmp' not 'operator')
- Conflicting parameters: `FILTER {key: "cpu", value: "80", expr: "cpu > 80"}`

**Best Practice**:
- Use quotes for field names: `FILTER {key: "field", value: "value"}` (better readability)
- Both quoted and unquoted field names are valid: `FILTER {key: field, value: value}` ✓

### GROUP

**Syntax**:
```mxql
GROUP {pk: "field"}
GROUP {pk: ["field1", "field2"]}
GROUP {timeunit: "5m"}
GROUP {timeunit: "1h", pk: "service"}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has at least one of: `pk`, `timeunit`
- [ ] `timeunit` value is valid: Xs, Xm, Xh, Xd format
- [ ] `pk` is string or array of strings
- [ ] Optional parameters valid: first, last, listup, merge, quantile, rank, rows
- [ ] If `quantile` specified: `rank` array should be present

**Common Issues**:
- Invalid timeunit: `GROUP {timeunit: "5minutes"}`
- Missing pk or timeunit: `GROUP {}`
- Invalid rank values: `GROUP {quantile: "latency", rank: [1.5]}`

### UPDATE

**Syntax**:
```mxql
UPDATE {key: "field", value: "function"}   # Apply to specific field
UPDATE {value: "function"}                  # Apply to all numeric fields
```

**Checks**:
- [ ] Appears AFTER GROUP command
- [ ] Wrapped in braces `{...}`
- [ ] Has required field: `value`
- [ ] Has optional field: `key` (if omitted, applies to all numeric fields)
- [ ] Function is valid: sum, avg, max, min, count, first, last
- [ ] Field name is quoted string (if key is provided)

**Critical Rule**:
- ❌ UPDATE without GROUP = Error
- ✓ GROUP then UPDATE = Correct

**Common Issues**:
- UPDATE before GROUP: Major semantic error
- Invalid function: `UPDATE {key: "count", value: "total"}`
- Missing UPDATE after GROUP: Aggregation not applied

### ORDER

**Syntax**:
```mxql
ORDER {key: [field], sort: "asc"}
ORDER {key: [field1, field2], sort: "desc"}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has required fields: `key`, `sort`
- [ ] `key` is array of strings
- [ ] `sort` is either "asc" or "desc"
- [ ] Fields in `key` exist (if known)

**Common Issues**:
- Missing brackets around key: `ORDER {key: field, sort: "desc"}`
- Invalid sort direction: `ORDER {key: [count], sort: "descending"}`
- Missing ORDER before LIMIT (for Top-N)

### LIMIT

**Syntax**:
```mxql
LIMIT 100
LIMIT $MAX_ROWS
```

**Checks**:
- [ ] Value is positive integer or parameter
- [ ] If used for Top-N: ORDER command precedes it
- [ ] Reasonable limit value (not too large)

**Best Practice**:
- Always use ORDER before LIMIT for Top-N queries
- Without ORDER, LIMIT gives arbitrary N results

**Common Issues**:
- LIMIT without ORDER for Top-N intent
- Excessive limit: `LIMIT 1000000`

### CREATE

**Syntax**:
```mxql
CREATE {key: "new_field", expr: "expression"}
CREATE {key: "new_field", from: "old_field"}
CREATE {key: "new_field", value: "constant"}
CREATE {key: "new_field", sum: ["field1", "field2"]}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has `key` parameter (required)
- [ ] Has one of: expr, from, value, sum, concat, avg
- [ ] Expression syntax is valid (if using expr)
- [ ] Referenced fields exist (if known)
- [ ] New field name doesn't conflict with existing fields

**Common Issues**:
- Invalid expression: `CREATE {key: "rate", expr: "count /"}`
- Missing source: `CREATE {key: "new_field"}`

### DELETE

**Syntax**:
```mxql
DELETE [field1, field2]
```

**Checks**:
- [ ] Wrapped in brackets `[...]`
- [ ] Fields are strings
- [ ] At least one field specified

### RENAME

**Syntax**:
```mxql
RENAME {src: "old_name", dst: "new_name"}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has both `src` and `dst` parameters
- [ ] Both are quoted strings
- [ ] `src` field exists (if known)
- [ ] `dst` doesn't conflict with existing fields

### DELTA

**Syntax**:
```mxql
DELTA {key: "field"}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has `key` parameter
- [ ] Field exists (if known)
- [ ] Makes sense in context (numeric field, time-series data)

### QUANTILE

**Syntax**:
```mxql
QUANTILE {key: "field", rank: [0.5, 0.95, 0.99]}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has `key` and `rank` parameters
- [ ] `rank` is array of numbers
- [ ] Rank values are between 0 and 1
- [ ] Field is numeric

### SUB...END

**Syntax**:
```mxql
SUB subquery_name
  <commands>
END
```

**Checks**:
- [ ] SUB has subquery name
- [ ] Contains valid MXQL commands
- [ ] Properly closed with END
- [ ] Subquery name is valid identifier
- [ ] Defined before being used in JOIN

**Common Issues**:
- Missing END: Unclosed subquery
- Using subquery before defining it
- Invalid commands inside subquery

### JOIN

**Syntax**:
```mxql
JOIN {query: "subquery_name", pk: ["field"]}
JOIN {query: "name", pk: ["field"], type: "inner"}
```

**Checks**:
- [ ] Wrapped in braces `{...}`
- [ ] Has required parameters: `query`, `pk`
- [ ] Referenced subquery is defined
- [ ] `pk` is array of strings
- [ ] `type` (if present) is valid: inner, left, right, outer
- [ ] Join fields exist in both queries (if known)

**Common Issues**:
- Undefined subquery: `JOIN {query: "undefined", pk: ["oid"]}`
- Invalid join type: `JOIN {query: "sub", pk: ["oid"], type: "full"}`

---

## Syntax Validation Rules

### JSON Format Rules

- [ ] All object parameters wrapped in `{...}`
- [ ] All array parameters wrapped in `[...]`
- [ ] No trailing commas
- [ ] Proper key-value separator: `:`
- [ ] Proper list separator: `,`

**Note**: Field names can be quoted or unquoted. Quotes are recommended for readability but not required.

### String Quoting

**Recommended (Best Practice)**:
- Field names: `{key: "field"}` ✓ (better readability)
- String values: `{value: "active"}` ✓ (clearer intent)
- Field names in arrays: `["oname", "cpu"]` ✓ (consistent style)

**Also Valid (without quotes)**:
- Field names: `{key: field}` ✓ (valid but less readable)
- Field names in arrays: `[oname, cpu]` ✓ (valid)

**Note**: Both quoted and unquoted field names are syntactically valid. However, using quotes (single `'` or double `"`) is recommended for better code readability and maintainability.

**Always unquoted**:
- Numbers: `{value: 80}` ✓
- Booleans: `{backward: true}` ✓
- Parameters: `$PARAM_NAME` ✓

### Bracket/Brace Balance

Check each command:
```
Opening: { [
Closing: } ]

Count must match!
```

**Example Check**:
```mxql
FILTER {key: "cpu", cmp: "gt", value: "80"}
       ^                                   ^
       Opening {                    Closing }
       Count: 1 opening, 1 closing ✓
```

### Common Syntax Patterns

**Valid**:
```mxql
FILTER {key: "field", value: "value"}
SELECT [field1, field2]
GROUP {timeunit: "5m", pk: ["service"]}
```

**Invalid**:
```mxql
SELECT field1, field2                     # Missing brackets
GROUP {timeunit: 5m, pk: [service]}      # Unquoted timeunit value (should be "5m")
```

**Valid but not recommended** (better with quotes for readability):
```mxql
FILTER {key: field, value: value}        # Valid but quotes are better
SELECT [field1, field2]                   # Valid but ["field1", "field2"] is clearer
```

---

## Semantic Validation Rules

### Command Order Rules

**Rule 1**: Data loading must come first
```mxql
# Correct
CATEGORY app_counter
TAGLOAD
<other commands>

# Incorrect - No data loader
CATEGORY app_counter
FILTER {key: "oid", value: "1001"}
```

**Rule 2**: UPDATE requires GROUP
```mxql
# Correct
GROUP {timeunit: "5m"}
UPDATE {key: "count", value: "sum"}

# Incorrect
UPDATE {key: "count", value: "sum"}  # No GROUP
```

**Rule 3**: ORDER before LIMIT for Top-N
```mxql
# Correct (Top-N by CPU)
ORDER {key: [cpu], sort: "desc"}
LIMIT 10

# Incorrect (arbitrary 10)
LIMIT 10
ORDER {key: [cpu], sort: "desc"}  # Too late!
```

**Rule 4**: JOIN requires SUB definition
```mxql
# Correct
SUB agents
  CATEGORY agent_list
  TAGLOAD
END

CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"]}

# Incorrect - No SUB defined
CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"]}
```

### Field Reference Validation

If category is known:
- [ ] All fields in SELECT exist in category
- [ ] All fields in FILTER exist in category
- [ ] All fields in GROUP pk exist in category
- [ ] All fields in UPDATE exist in category
- [ ] All fields in ORDER exist in category

If category is unknown:
- Note: Cannot validate field existence
- Warn user to verify field names

### Logical Consistency

- [ ] No conflicting filters (e.g., cpu > 80 AND cpu < 50)
- [ ] Created fields don't overwrite existing fields (unless intentional)
- [ ] Aggregation functions appropriate for field types
- [ ] Time range is reasonable
- [ ] Parameter usage is consistent

---

## Performance Validation Rules

### Filter Placement

**Rule**: Filter as early as possible

```mxql
# Bad - Late filtering
CATEGORY db_mysql_counter
TAGLOAD
SELECT [*]
GROUP {timeunit: "5m"}
FILTER {key: "oid", value: ["1001"]}  # Too late!

# Good - Early filtering
CATEGORY db_mysql_counter
TAGLOAD
FILTER {key: "oid", value: ["1001"]}  # Early!
SELECT [oname, cpu(xos)]
GROUP {timeunit: "5m"}
```

**Check**:
- [ ] FILTER appears before GROUP (when possible)
- [ ] FILTER appears before SELECT (when possible)
- [ ] OID/instance filters are applied early (OID command can be before or after TAGLOAD)

### Field Selection

**Rule**: Select only needed fields

```mxql
# Bad
SELECT [*]

# Good
SELECT [oname, cpu(xos), mem_pct]
```

**Check**:
- [ ] Avoid SELECT [*] unless truly all fields needed
- [ ] No redundant fields in SELECT
- [ ] Fields match what's used in later commands

### Result Limiting

**Rule**: Always limit results for large datasets

```mxql
# Missing LIMIT - Could return millions of rows
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]

# With LIMIT
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
ORDER {key: [tx_count], sort: "desc"}
LIMIT 100
```

**Check**:
- [ ] LIMIT present for queries that could return many results
- [ ] LIMIT value is reasonable (not too large)
- [ ] ORDER + LIMIT used together for Top-N

### Aggregation Efficiency

**Check**:
- [ ] GROUP timeunit is appropriate (not too granular)
- [ ] Not grouping unnecessarily
- [ ] UPDATE functions appropriate for metric types
- [ ] No redundant aggregations

### Time Range

**Check**:
- [ ] Time range is specified (TIMEFILTER) or reasonable default
- [ ] Not querying excessive historical data
- [ ] Timeunit in GROUP matches time range (5m for recent, 1h for daily, etc.)

---

## Security Validation Rules

### Injection Risks

**Check**:
- [ ] Expression filters don't use user input directly (use parameters)
- [ ] No obvious SQL injection patterns (should be safe in MXQL)
- [ ] Parameter names follow expected patterns

### Data Access

**Check**:
- [ ] Query doesn't attempt to access restricted categories (if known)
- [ ] OID filtering appropriately restricts scope
- [ ] No attempts to bypass access controls

### Resource Usage

**Check**:
- [ ] Query has reasonable resource usage expectations
- [ ] No potential for denial of service (e.g., no LIMIT)
- [ ] Aggregation timeunit not excessively granular

---

## Analysis Priority

When analyzing, check in this order:

### Priority 1: Critical Syntax Errors
These prevent query execution:
- Unclosed brackets/braces
- Invalid JSON structure
- Unknown commands
- Missing required parameters

### Priority 2: Semantic Errors
These cause incorrect behavior:
- UPDATE without GROUP
- Missing data loader
- Undefined subquery reference
- Invalid field references (if known)

### Priority 3: Performance Issues
These cause slow execution:
- Late filtering
- SELECT *
- Missing LIMIT
- Excessive time range

### Priority 4: Best Practice Violations
These are sub-optimal but work:
- Unquoted field names (valid but reduces readability)
- LIMIT without ORDER (when Top-N intended)
- Redundant commands
- Sub-optimal aggregation

### Priority 5: Optimization Opportunities
These are nice-to-have improvements:
- Use CREATE for calculations
- Combine multiple FILTER into expr
- Simplify complex expressions

---

## Validation Output Template

Use this template for structured validation:

```
## Validation Results

### Syntax: [PASS / FAIL]
[List any syntax errors]

### Semantics: [PASS / FAIL]
[List any semantic errors]

### Performance: [OPTIMAL / ACCEPTABLE / NEEDS IMPROVEMENT]
[List performance issues]

### Best Practices: [FOLLOWED / MINOR ISSUES / MAJOR ISSUES]
[List best practice violations]

### Summary
- Critical Issues: X
- Warnings: Y
- Info: Z

### Recommendation: [READY TO USE / NEEDS FIXES / NEEDS OPTIMIZATION]
```

---

## Quick Validation Checklist

For rapid analysis, check these essential items:

**Must Have**:
- [ ] CATEGORY command
- [ ] Data loader (TAGLOAD, etc.)
- [ ] All brackets/braces closed
- [ ] Valid JSON structure
- [ ] UPDATE only after GROUP

**Should Have**:
- [ ] Early FILTER (before GROUP)
- [ ] Specific SELECT (not *)
- [ ] ORDER before LIMIT (if Top-N)
- [ ] Reasonable LIMIT

**Nice to Have (Best Practices)**:
- [ ] Quoted field names for readability (both quoted and unquoted are valid)
- [ ] CREATE for calculations
- [ ] Appropriate timeunit
- [ ] Clear query structure
- [ ] Comments (if complex)

---

## Next Steps

After checklist validation:
1. Categorize issues by severity
2. Prioritize fixes (critical → warning → info)
3. Provide corrected query
4. Suggest optimizations
5. Explain what the query does

This checklist ensures comprehensive and systematic MXQL query analysis.
