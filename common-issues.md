# Common MXQL Issues and Solutions

Frequently encountered problems in MXQL queries with solutions and explanations.

## Table of Contents

1. [Syntax Errors](#syntax-errors)
2. [Semantic Errors](#semantic-errors)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [Logic Errors](#logic-errors)
6. [Common Misunderstandings](#common-misunderstandings)

---

## Syntax Errors

### Issue 1: Unquoted Strings in JSON

**Error**:
```mxql
FILTER {key: status, value: active}
```

**Problem**: JSON requires strings to be quoted

**Symptoms**:
- Parse error
- Query fails immediately
- Error message about invalid JSON

**Solution**:
```mxql
FILTER {key: "status", value: "active"}
```

**How to prevent**: Always quote string keys and values in JSON objects

---

### Issue 2: Missing Brackets Around SELECT Fields

**Error**:
```mxql
SELECT oname, cpu(xos), memory
```

**Problem**: SELECT requires array syntax

**Symptoms**:
- Parse error
- "Expected array" error message

**Solution**:
```mxql
SELECT [oname, cpu(xos), memory]
```

**Common variant**: Forgetting brackets in ORDER as well
```mxql
ORDER {key: field, sort: "desc"}  ❌
ORDER {key: [field], sort: "desc"}  ✅
```

---

### Issue 3: Unclosed Brackets/Braces

**Error**:
```mxql
FILTER {key: "cpu", cmp: "gt", value: "80"
SELECT [oname, cpu(xos)]
```

**Problem**: Missing closing brace `}` on FILTER

**Symptoms**:
- Parse error
- "Unexpected token" error
- May report error on wrong line (next command)

**Solution**:
```mxql
FILTER {key: "cpu", cmp: "gt", value: "80"}
SELECT [oname, cpu(xos)]
```

**How to find**: Count opening `{[` and closing `}]` for each command

---

### Issue 4: Wrong Parameter Name

**Error**:
```mxql
FILTER {key: "cpu", operator: "gt", value: "80"}
```

**Problem**: MXQL uses `cmp` not `operator`

**Symptoms**:
- Parse error or ignored parameter
- Filter doesn't work as expected

**Solution**:
```mxql
FILTER {key: "cpu", cmp: "gt", value: "80"}
```

**Common mistakes**:
- `operator` instead of `cmp`
- `field` instead of `key`
- `order` instead of `sort`

---

### Issue 5: Invalid Comparison Operator

**Error**:
```mxql
FILTER {key: "cpu", cmp: ">", value: "80"}
```

**Problem**: Use operator names, not symbols

**Symptoms**:
- Parse error
- "Invalid comparison operator" error

**Solution**:
```mxql
FILTER {key: "cpu", cmp: "gt", value: "80"}
```

**Valid operators**: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`

---

### Issue 6: Trailing Commas

**Error**:
```mxql
SELECT [oname, cpu(xos), memory,]
```

**Problem**: Trailing comma in array

**Symptoms**:
- Parse error (some parsers)
- May work but bad practice

**Solution**:
```mxql
SELECT [oname, cpu(xos), memory]
```

---

## Semantic Errors

### Issue 7: UPDATE Without GROUP

**Error**:
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
UPDATE {key: "tx_count", value: "sum"}
```

**Problem**: UPDATE requires GROUP to exist first

**Symptoms**:
- Runtime error: "UPDATE requires GROUP"
- Query fails during execution

**Solution**:
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
GROUP {timeunit: "5m", pk: "service"}  ← Add GROUP
UPDATE {key: "tx_count", value: "sum"}
```

**Note on UPDATE key parameter**:
- `UPDATE {key: "tx_count", value: "sum"}` - applies to specific field
- `UPDATE {value: "sum"}` - applies to ALL numeric fields (key is optional)
- When key is omitted, aggregation applies to all applicable fields

**Why**: UPDATE applies aggregation function, which requires grouping context

---

### Issue 8: Missing Data Loader

**Error**:
```mxql
CATEGORY db_mysql_counter
SELECT [oname, cpu(xos)]
FILTER {key: "cpu(xos)", cmp: "gt", value: "80"}
```

**Problem**: No TAGLOAD or other data loader

**Symptoms**:
- No data returned
- "No data source" error
- Empty result set

**Solution**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD  ← Add data loader
SELECT [oname, cpu(xos)]
FILTER {key: "cpu(xos)", cmp: "gt", value: "80"}
```

---

### Issue 9: JOIN Without Subquery Definition

**Error**:
```mxql
CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"]}
```

**Problem**: Subquery "agents" is not defined

**Symptoms**:
- Runtime error: "Undefined subquery"
- "Query 'agents' not found"

**Solution**:
```mxql
SUB agents  ← Define subquery first
  CATEGORY agent_list
  TAGLOAD
  FILTER {key: "status", value: "active"}
END

CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"]}
```

---

### Issue 10: Invalid Field Name

**Error**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu_usage]  ← Wrong field name
```

**Problem**: Field `cpu_usage` doesn't exist in category

**Symptoms**:
- Field not in results
- May return null/empty for that field
- "Unknown field" error (if validation enabled)

**Solution**: Check category metadata for correct field names
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]  ← Correct field name
```

**How to check**: Read category meta file or use generator skill

---

### Issue 11: Wrong Command Order

**Error**:
```mxql
CATEGORY db_postgresql_counter
FILTER {key: "oid", value: ["1001"]}  ← Before TAGLOAD
TAGLOAD
SELECT [oname, cpu(xos)]
```

**Problem**: FILTER before TAGLOAD may not work as expected

**Symptoms**:
- Filter not applied
- Unexpected results
- May cause error

**Solution**: Standard order is CATEGORY → TAGLOAD → FILTER
```mxql
CATEGORY db_postgresql_counter
TAGLOAD
FILTER {key: "oid", value: ["1001"]}  ← After TAGLOAD
SELECT [oname, cpu(xos)]
```

---

## Runtime Errors

### Issue 12: Division by Zero

**Error**:
```mxql
CREATE {key: "rate", expr: "count / time"}
```

**Problem**: If `time` is zero, division fails

**Symptoms**:
- Runtime error: "Division by zero"
- Result is null/NaN
- Query stops processing

**Solution**: Add safeguard
```mxql
CREATE {key: "rate", expr: "time > 0 ? count / time : 0"}
```

Or filter out zero values first:
```mxql
FILTER {key: "time", cmp: "gt", value: "0"}
CREATE {key: "rate", expr: "count / time"}
```

---

### Issue 13: Type Mismatch

**Error**:
```mxql
FILTER {key: "status_code", cmp: "gt", value: "500"}
```

**Problem**: Comparing string field as number

**Symptoms**:
- Comparison doesn't work correctly
- String comparison instead of numeric
- Unexpected filter results

**Solution**: Ensure field is numeric type or cast
```mxql
TYPECAST {key: "status_code", type: "int"}
FILTER {key: "status_code", cmp: "gt", value: "500"}
```

Or use numeric values directly if field is numeric:
```mxql
FILTER {key: "status_code", cmp: "gt", value: 500}
```

---

### Issue 14: Out of Memory

**Error**: (No specific MXQL error, but system-level)

**Problem**: Query returns too much data

**Symptoms**:
- Query hangs
- Server runs out of memory
- Client crashes
- Very slow response

**Common causes**:
```mxql
# No LIMIT
CATEGORY app_counter
TAGLOAD
SELECT [*]  ← All fields
# Could return millions of rows!
```

**Solutions**:
1. Add LIMIT:
```mxql
LIMIT 1000
```

2. Add time filter:
```mxql
TIMEFILTER {from: "now-1h", to: "now"}
```

3. Add selective filters:
```mxql
FILTER {key: "oid", value: [$OID_LIST]}
```

4. Use GROUP to aggregate:
```mxql
GROUP {timeunit: "5m"}
UPDATE {key: "count", value: "sum"}
```

---

### Issue 15: Timeout

**Error**: "Query timeout" or "Execution timeout"

**Problem**: Query takes too long

**Common causes**:
- No filters on large dataset
- Excessive time range
- Complex aggregations on too much data
- Missing indexes (system-level)

**Solutions**:
```mxql
# Add time constraint
TIMEFILTER {from: "now-1h", to: "now"}

# Add selective filters
FILTER {key: "oid", value: ["1001", "1002"]}

# Use coarser aggregation
GROUP {timeunit: "5m"}  # Instead of 5s

# Limit results
LIMIT 100
```

---

## Performance Issues

### Issue 16: Slow Query - Late Filtering

**Symptom**: Query is slow even with filters

**Problem**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [*]  ← All fields
GROUP {timeunit: "1m"}  ← Aggregating all instances
UPDATE {key: "cpu(xos)", value: "avg"}
FILTER {key: "oid", value: ["1001"]}  ← Filter AFTER aggregation!
```

**Analysis**: Processing all data, then filtering to one instance

**Solution**: Filter early
```mxql
CATEGORY db_mysql_counter
TAGLOAD
FILTER {key: "oid", value: ["1001"]}  ← Early filter!
SELECT [oname, cpu(xos)]  ← Specific fields
GROUP {timeunit: "1m"}
UPDATE {key: "cpu(xos)", value: "avg"}
```

**Performance gain**: 50-90% faster (depending on selectivity)

---

### Issue 17: Slow Query - Excessive Granularity

**Symptom**: Query times out or is very slow

**Problem**:
```mxql
# Analyzing last 30 days at 5-second intervals
TIMEFILTER {from: "now-30d", to: "now"}
GROUP {timeunit: "5s"}  ← Way too granular!
```

**Analysis**: 30 days × 24 hours × 3600 sec / 5 = 518,400 data points

**Solution**: Match timeunit to analysis period
```mxql
TIMEFILTER {from: "now-30d", to: "now"}
GROUP {timeunit: "1h"}  ← Appropriate for 30-day view
```

**Result**: 30 × 24 = 720 data points (720x reduction!)

---

### Issue 18: Slow Query - SELECT *

**Symptom**: Query uses a lot of memory and is slow

**Problem**:
```mxql
CATEGORY db_postgresql_counter
TAGLOAD
SELECT [*]  ← Returns 100+ fields
```

**Analysis**: Processing and transferring unnecessary data

**Solution**: Select only needed fields
```mxql
CATEGORY db_postgresql_counter
TAGLOAD
SELECT [oname, cpu(xos), mem_pct, active_sessions]  ← Just 4 fields
```

---

## Logic Errors

### Issue 19: Wrong Results - LIMIT Without ORDER

**Symptom**: Top-N query returns different results each time

**Problem**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
LIMIT 10  ← Which 10?
```

**Analysis**: Without ORDER, LIMIT returns arbitrary 10 results

**Solution**: Add ORDER
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
ORDER {key: [cpu(xos)], sort: "desc"}  ← Deterministic!
LIMIT 10
```

---

### Issue 20: Unexpected Results - Filter on Wrong Field

**Symptom**: Filter doesn't seem to work

**Problem**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
FILTER {key: "cpu", value: "80"}  ← Looking for exact match
```

**Analysis**:
- Looking for `cpu == "80"` (exact value)
- Should be `cpu > 80` (threshold)
- Field name might be wrong (`cpu` vs `cpu(xos)`)

**Solution**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
FILTER {key: "cpu(xos)", cmp: "gt", value: "80"}  ← Correct field and comparison
```

---

### Issue 21: Missing Data - Aggregation Without UPDATE

**Symptom**: After GROUP, fields disappear

**Problem**:
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
GROUP {timeunit: "5m", pk: "service"}
# Missing UPDATE!
ORDER {key: [tx_count], sort: "desc"}  ← Field may be lost
```

**Analysis**: GROUP changes data structure, need UPDATE to aggregate values

**Solution**:
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
GROUP {timeunit: "5m", pk: "service"}
UPDATE {key: "tx_count", value: "sum"}  ← Aggregate the metric!
ORDER {key: [tx_count], sort: "desc"}
```

---

### Issue 22: Wrong Aggregation Function

**Symptom**: Results don't make sense

**Problem**:
```mxql
GROUP {timeunit: "1h"}
UPDATE {key: "active_sessions", value: "sum"}  ← Sum of sessions?
```

**Analysis**: Summing sessions across time doesn't make sense (double-counting)

**Solution**: Use appropriate aggregation
```mxql
GROUP {timeunit: "1h"}
UPDATE {key: "active_sessions", value: "avg"}  ← Average sessions
```

**Guidelines**:
- **Counters** (tx_count, request_count): `sum`
- **Gauges** (cpu, memory, sessions): `avg` or `max`
- **Rates** (ops_per_sec): `avg`
- **Latencies** (response_time): `avg` or percentiles

---

## Common Misunderstandings

### Misunderstanding 1: SELECT Filters Data

**Wrong assumption**: "SELECT [cpu(xos)] will filter to only rows with CPU data"

**Reality**: SELECT chooses columns, not rows

**Correct approach**: Use FILTER to filter rows
```mxql
# Wrong assumption
SELECT [cpu(xos)]  # Just selects CPU column

# Correct filtering
FILTER {key: "cpu(xos)", exist: true}  # Filters rows with CPU data
SELECT [oname, cpu(xos)]
```

---

### Misunderstanding 2: LIMIT Is Per Group

**Wrong assumption**: "LIMIT 10 with GROUP will give me top 10 per group"

**Reality**: LIMIT applies to final result set

**Example**:
```mxql
GROUP {timeunit: "5m", pk: "service"}
UPDATE {key: "count", value: "sum"}
LIMIT 10  # Top 10 overall, not per service!
```

**For top-N per group**: Need application-level processing or specialized commands

---

### Misunderstanding 3: Multiple FILTER Means OR

**Wrong assumption**: "Multiple FILTER commands create OR condition"

**Reality**: Multiple FILTER commands create AND condition (all must match)

**Example**:
```mxql
FILTER {key: "type", value: "A"}
FILTER {key: "status", value: "active"}
# Result: type=A AND status=active (not OR!)
```

**For OR**: Use expression
```mxql
FILTER {expr: "type == 'A' || type == 'B'"}
```

---

### Misunderstanding 4: GROUP Changes Time Range

**Wrong assumption**: "GROUP {timeunit: '5m'} only shows last 5 minutes"

**Reality**: GROUP aggregates data into time buckets, doesn't filter time range

**Example**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD  # Gets all available data in default range
GROUP {timeunit: "5m"}  # Aggregates into 5-minute buckets
# Still processes full default time range!
```

**To limit time**: Use TIMEFILTER
```mxql
TIMEFILTER {from: "now-1h", to: "now"}  # Limit to last hour
GROUP {timeunit: "5m"}  # Then aggregate
```

---

### Misunderstanding 5: ORDER Reduces Data

**Wrong assumption**: "ORDER will make query faster by organizing data"

**Reality**: ORDER adds processing cost

**Truth**:
- ORDER doesn't reduce data volume
- ORDER is necessary for meaningful Top-N (with LIMIT)
- ORDER adds CPU cost for sorting
- Use ORDER only when needed

---

## Debugging Workflow

When query doesn't work as expected:

### Step 1: Check Syntax
- [ ] All strings quoted?
- [ ] All brackets/braces closed?
- [ ] Valid command names?
- [ ] Valid parameter names?

### Step 2: Check Semantics
- [ ] CATEGORY present?
- [ ] Data loader present?
- [ ] UPDATE only after GROUP?
- [ ] Subqueries defined before JOIN?

### Step 3: Check Field Names
- [ ] Field names match category metadata?
- [ ] Correct field name format (e.g., `cpu(xos)` not `cpu`)?

### Step 4: Check Logic
- [ ] Filters make sense?
- [ ] Aggregation function appropriate?
- [ ] ORDER before LIMIT (if Top-N)?

### Step 5: Simplify
- Remove commands one by one
- Find which command causes issue
- Test with minimal query first

### Step 6: Check Data
- Does data exist for filters?
- Is time range correct?
- Are there actually values in fields?

---

## Quick Fixes Reference

| Symptom | Likely Issue | Quick Fix |
|---------|-------------|-----------|
| Parse error | Syntax error | Check quotes, brackets |
| "UPDATE requires GROUP" | Missing GROUP | Add GROUP before UPDATE |
| No data returned | Missing TAGLOAD | Add TAGLOAD after CATEGORY |
| Query times out | Too much data | Add FILTER, LIMIT, TIMEFILTER |
| Random Top-N results | No ORDER | Add ORDER before LIMIT |
| Fields disappear | Missing UPDATE | Add UPDATE after GROUP |
| Wrong comparison | Invalid operator | Use gt/gte/lt/lte/eq/ne |
| Undefined subquery | JOIN before SUB | Define SUB before using |
| Type error | Field type mismatch | Use TYPECAST or fix comparison |
| Slow query | Late filtering | Move FILTER earlier |

---

## Prevention Checklist

To avoid common issues:

**Before writing query**:
- [ ] Identify exact category and fields needed
- [ ] Plan filter strategy (what, where)
- [ ] Choose appropriate aggregation
- [ ] Decide result size (LIMIT)

**While writing query**:
- [ ] Quote all strings
- [ ] Close all brackets/braces
- [ ] Use correct command/parameter names
- [ ] Follow command order rules

**Before running query**:
- [ ] Validate syntax (quotes, brackets)
- [ ] Check command order
- [ ] Verify field names
- [ ] Estimate result size

**After getting results**:
- [ ] Verify result count is reasonable
- [ ] Check if results match expectations
- [ ] Review performance
- [ ] Consider optimizations

---

## Getting Help

If still stuck:
1. **Isolate the issue**: Remove commands until query works, then add back
2. **Check examples**: Look at similar working queries
3. **Read error messages carefully**: They often point to exact issue
4. **Test with simple data**: Use known-good filter (specific OID)
5. **Use analyzer skill**: Let skill analyze the query

Remember: Most issues are simple syntax or semantic errors that are easy to fix once identified!
