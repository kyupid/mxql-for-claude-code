---
name: generating-mxql-queries
description: Generates MXQL (Metrics Query Language) queries through conversational interaction. Use this when users need to query metrics for database monitoring (MySQL, PostgreSQL, Oracle, etc.), infrastructure monitoring, or APM. Guides users through selecting categories, metrics, filters, and aggregations to create valid, optimized MXQL queries. Includes validation, explanation, and best practice recommendations.
---

# MXQL Query Generator

## Overview

This skill helps generate MXQL (Metrics Query Language) queries through a conversational, step-by-step approach. Instead of requiring users to know exact category names, field names, and syntax, this skill guides them through the query creation process by asking clarifying questions.

**Coverage**: 631 categories across 36+ product types
- Database (44), Application/APM (16), Infrastructure (16), Kubernetes (28)
- Cloud: AWS (107), Azure (147), OCI (48), NCloud (11)
- Container, RUM, URL Monitoring, and more

## When to Use This Skill

Activate this skill when users:
- Request to "create an MXQL query" or "generate MXQL"
- Ask to "query database metrics" or "monitor DB performance"
- Want to find specific metrics (e.g., "show CPU usage", "find high sessions")
- Need help with categories or field selection
- Ask "how do I query [metric] for [product]?"

**Examples of triggering requests**:
- "Create MXQL query for MySQL CPU usage"
- "How do I check PostgreSQL active sessions?"
- "Generate a query to find DB instances with high memory"
- "Make a test MXQL for Oracle performance monitoring"

## Conversational Workflow

Follow this 5-step conversational process to generate accurate queries:

### Step 1: Understand User Intent

Parse the user's request to identify:
- **What**: Which metric? (CPU, memory, sessions, I/O, etc.)
- **Where**: Which product/category? (MySQL, PostgreSQL, Oracle, etc.)
- **How**: What type of analysis? (Simple view, Top-N, threshold alert, time-series)
- **When**: Time range? (last 5m, 1h, 1d, etc.)

**Example**:
```
User: "DB 제품에서 CPU 사용량 조회하는 테스트 MXQL 만들어줘"

Intent Analysis:
- What: CPU usage (cpu metric)
- Where: DB product (need to clarify which one)
- How: Simple monitoring query
- When: Not specified (use current data)
```

### Step 2: Discover and Select Category

If the category is not specified or ambiguous, use `category_finder.py` to find relevant categories:

**Option A: Search by keyword**
```python
from category_finder import CategoryFinder, format_category_list

finder = CategoryFinder()
results = finder.search("postgresql")  # or "kubernetes", "aws ec2", etc.
print(format_category_list(results, include_details=True))
```

**Option B: Recommend based on user intent**
```python
recommendations = finder.recommend("monitor kubernetes pod CPU usage")
# Returns relevant categories with explanations
```

**Present options to user using AskUserQuestion**:
- Show 2-4 most relevant categories
- Include category title and platforms
- Let user select the best match

**Example**:
```
Found these categories for "postgresql monitoring":
1. db_postgresql_counter - General PostgreSQL metrics (5s intervals)
2. db_postgresql_stat - Database statistics
3. db_postgresql_table_bloating - Table bloat monitoring
4. db_postgresql_vacuum_candidate - Vacuum candidates

Which category fits your needs?
```

**Get category metadata after selection**:
```python
category_info = finder.get_category_info("db_postgresql_counter", language="ko")
# Returns full metadata: tags, fields, intervals, etc.
```

### Step 3: Select Metrics

Use the category metadata (from Step 2) to identify available fields:

```python
category_info = finder.get_category_info("db_postgresql_counter")

# Extract available fields
for field in category_info['fields']:
    print(f"- {field['fieldName']}: {field.get('description', '')}")
    print(f"  Unit: {field.get('unit', 'N/A')}, Type: {field.get('type', 'N/A')}")
```

**Match user intent to available fields**:
- User wants "CPU usage" → Look for fields with "cpu" in name
- User wants "memory" → Look for "mem", "memory" in name
- User wants "sessions" → Look for "session", "connection" in name

**Example for db_postgresql_counter**:
```
Available CPU metrics:
- cpu(xos) - Total CPU utilization (%, Number)
- cpu_user(xos) - User mode CPU (%, Number)
- cpu_sys(xos) - System mode CPU (%, Number)
- cpu_iowait(xos) - I/O wait (%, Number)

Available memory metrics:
- mem_total(xos) - Total memory (byte, Number)
- mem_used(xos) - Used memory (byte, Number)
- mem_pct - Memory usage percentage (pct, Number)
```

**Best practice**: Include related fields for context
- If CPU requested → Also include mem_pct for holistic view
- If query time requested → Include lock_wait_time for debugging

### Step 4: Define Filters and Conditions

Ask if the user needs:
- **Threshold filtering**: Show only instances where CPU > 80%
- **OID filtering**: Specific database instances
- **Time filtering**: Specific time range
- **Top-N**: Top 10 by usage
- **Aggregation**: Group by time (5m, 1h) or dimension (service, host)

### Step 5: Generate and Validate Query

Generate the MXQL query following these rules:

**Mandatory patterns**:
1. Start with `CATEGORY` + data loader (`TAGLOAD`)
2. Apply filters early (before GROUP)
3. Use `SELECT` to choose fields
4. Use `GROUP` before aggregation (`UPDATE`)
5. Use `ORDER` before `LIMIT` for Top-N

**Validation checklist**:
- [ ] CATEGORY specified
- [ ] Data loader present (TAGLOAD)
- [ ] Field names valid for category
- [ ] UPDATE only after GROUP
- [ ] ORDER before LIMIT (if Top-N)
- [ ] All braces/brackets closed
- [ ] String values quoted

After generating, explain:
- What each command does
- What the metrics mean
- How to interpret results
- Any performance considerations

## Quick Start Examples

### Example 1: Basic CPU Monitoring

**User Request**: "MySQL CPU 사용량 조회"

**Generated Query**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos), cpu_user(xos), cpu_sys(xos), cpu_iowait(xos)]
ORDER {key: [cpu(xos)], sort: "desc"}
```

**Explanation**:
- `CATEGORY db_mysql_counter`: Sets data source to MySQL metrics
- `TAGLOAD`: Loads the time-series tag data
- `SELECT`: Chooses instance name (oname) and CPU metrics
- `ORDER`: Sorts by total CPU usage (highest first)

**Metric Meanings**:
- `cpu(xos)`: Total CPU % (user + sys + iowait)
- `cpu_user(xos)`: Application CPU usage
- `cpu_sys(xos)`: Kernel/system CPU usage
- `cpu_iowait(xos)`: CPU waiting for disk I/O (high value = disk bottleneck)

### Example 2: Threshold Alert

**User Request**: "CPU 80% 넘는 인스턴스 찾기"

**Clarification**: Which DB product? → "MySQL"

**Generated Query**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, okindName, cpu(xos), cpu_user(xos), cpu_iowait(xos)]
FILTER {key: "cpu(xos)", cmp: "gt", value: "80"}
ORDER {key: [cpu(xos)], sort: "desc"}
```

**Explanation**:
- `FILTER {cmp: "gt", value: "80"}`: Shows only instances with CPU > 80%
- Includes okindName to identify which DB type/group

### Example 3: Top-N Analysis

**User Request**: "CPU 사용량 상위 10개 조회"

**Generated Query**:
```mxql
CATEGORY db_postgresql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
ORDER {key: [cpu(xos)], sort: "desc"}
LIMIT 10
```

**Explanation**:
- `ORDER` before `LIMIT`: Ensures top 10 by CPU (not arbitrary 10)
- `sort: "desc"`: Highest to lowest

### Example 4: Time-Series Aggregation

**User Request**: "시간대별 평균 CPU 추이"

**Generated Query**:
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [time, cpu(xos), cpu_user(xos), cpu_sys(xos)]
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
UPDATE {key: "cpu_user(xos)", value: "avg"}
UPDATE {key: "cpu_sys(xos)", value: "avg"}
ORDER {key: [time], sort: "asc"}
```

**Explanation**:
- `GROUP {timeunit: "5m"}`: Aggregates data into 5-minute buckets
- `UPDATE {value: "avg"}`: Calculates average for each time bucket
- Results show CPU trend over time

## Supported Products

### Currently Supported: Database Products (15)

| Product | Category | Key Metrics |
|---------|----------|-------------|
| MySQL / MariaDB | db_mysql_counter | cpu(xos), mem_used(xos), active_sessions |
| PostgreSQL | db_postgresql_counter | cpu(xos), mem_used(xos), active_sessions |
| Oracle | db_oracle_counter | cpu(xos), mem_used(xos), active_sessions |
| MS SQL Server | db_mssql_counter | cpu(xos), mem_used(xos), active_sessions |
| MongoDB | db_mongodb_counter | cpu(xos), connections, operations |
| Redis | db_redis_counter | cpu(xos), mem_used_rss, connected_clients |
| CUBRID | db_cubrid_counter | cpu(xos), mem_used(xos), active_sessions |
| Altibase | db_altibase_counter | cpu(xos), mem_used(xos), sessions |
| Tibero | db_tibero_counter | cpu(xos), mem_used(xos), active_sessions |
| SAP ASE | db_sap_ase_counter | cpu(xos), mem_used(xos), connections |
| IBM DB2 | db_db2_counter | cpu(xos), mem_used(xos), connections |
| Oracle DMA | db_oracle_dma_counter | cpu(xos), mem_used(xos), sessions |
| Oracle v2 | db_oracle2_counter | cpu(xos), mem_used(xos), sessions |
| Oracle Realtime | oracle_db_real_counter | Real-time Oracle metrics |
| PostgreSQL Realtime | postgre_db_real_counter | Real-time PostgreSQL metrics |

For detailed metric lists per category, see `db-categories.md`.

### Future Expansion

The skill structure supports adding:
- **Infrastructure monitoring**: infra_cpu, infra_mem, infra_disk, infra_network
- **APM monitoring**: app_counter, app_host_resource
- **Container monitoring**: container, kube_pod
- **Cloud monitoring**: aws_*, azure_*, oci_*

## Query Patterns Library

For common query patterns and templates, refer to `query-patterns.md`:
- **Performance Monitoring**: Basic metric queries
- **Problem Detection**: Threshold-based alerts
- **Top-N Analysis**: Ranking and comparison
- **Time-Series Analysis**: Trends and growth rates

## Metric Selection Guide

For detailed guidance on choosing the right metrics, see `metrics-guide.md`:
- When to use cpu(xos) vs cpu_user vs cpu_sys
- Memory metrics interpretation
- Session and connection metrics
- I/O and disk metrics
- XOS (eXtended OS) metric explanation

## MXQL Syntax Reference

For MXQL syntax details, operators, and common mistakes, see `mxql-syntax-quick-ref.md`.

## Progressive Disclosure Strategy

To keep this skill token-efficient, detailed information is in separate files:

1. **Start here** (SKILL.md): Conversational workflow and quick examples
2. **Need category info?** → Read `db-categories.md`
3. **Need pattern templates?** → Read `query-patterns.md`
4. **Need metric details?** → Read `metrics-guide.md`
5. **Need syntax help?** → Read `mxql-syntax-quick-ref.md`
6. **Need exact field list?** → Read category meta file at:
   `/Users/kyw/git/claude-workspace/repos/whatap/collector-server/whatap.server.meta/TagCount_meta_file/db_{product}_counter_en.meta`

## CRITICAL: GROUP vs UPDATE Syntax

**This is a common mistake - read carefully!**

### GROUP Syntax (Grouping/Aggregation Configuration)

GROUP uses special keywords, NOT key-value pairs:

```mxql
# ✅ CORRECT GROUP syntax
GROUP {pk: "service"}                    # Group by single field
GROUP {pk: ["service", "host"]}          # Group by multiple fields
GROUP {timeunit: "5m"}                   # Time-based grouping
GROUP {timeunit: "5m", pk: "service"}    # Both time and field grouping

# GROUP special keywords:
# - pk: Primary key(s) to group by
# - timeunit: Time unit for aggregation ("5s", "1m", "5m", "1h", "1d")
# - first: Fields to keep first value
# - last: Fields to keep last value
# - listup: Fields to list unique values
# - merge: Field to merge metric values
# - quantile: Field for quantile calculation
# - rank: Percentile ranks (e.g., [0.5, 0.95, 0.99])
# - rows: Max rows per group
```

### UPDATE Syntax (Aggregation Function)

UPDATE uses key-value pairs:

```mxql
# ✅ CORRECT UPDATE syntax (must come AFTER GROUP)
UPDATE {key: "cpu", value: "avg"}
UPDATE {key: "count", value: "sum"}
UPDATE {value: "sum"}  # Apply to all numeric fields (key is optional)
```

### ❌ COMMON MISTAKE - DO NOT DO THIS:

```mxql
# ❌ WRONG - This is NOT valid MXQL!
GROUP {key: "service", value: "sum"}
GROUP {key: ["field1"], value: ["sum"]}

# This confusion comes from SQL's GROUP BY or other languages
# MXQL uses different syntax!
```

### Correct Pattern for Aggregation:

```mxql
# Example: Sum transaction count by service
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
GROUP {pk: "service"}              # ✅ Use pk, not key
UPDATE {key: "tx_count", value: "sum"}  # ✅ UPDATE comes after GROUP

# Example: Average CPU over time
CATEGORY db_mysql_counter
TAGLOAD
SELECT [time, cpu]
GROUP {timeunit: "5m"}             # ✅ Time-based grouping
UPDATE {key: "cpu", value: "avg"}  # ✅ Then aggregate
```

## Best Practices

### Do:
- ✅ Filter early (before GROUP) to reduce data volume
- ✅ Use ORDER before LIMIT for Top-N queries
- ✅ Include oname (object name) to identify instances
- ✅ Use appropriate timeunit for GROUP (5m for real-time, 1h for trends)
- ✅ Explain metrics and their units to users
- ✅ Validate queries before returning
- ✅ Use `pk` keyword in GROUP, not `key`
- ✅ Always use GROUP before UPDATE

### Don't:
- ❌ Use LIMIT without ORDER (results are arbitrary)
- ❌ Use UPDATE without GROUP (will error)
- ❌ Select unnecessary fields (wastes resources)
- ❌ Forget to quote string values in JSON
- ❌ Assume field names without checking meta
- ❌ Use `GROUP {key: ..., value: ...}` - this is WRONG syntax!
- ❌ Confuse GROUP (grouping config) with UPDATE (aggregation function)

## Troubleshooting

### User doesn't know which DB product
→ Ask them to specify or list options

### Metric name unclear
→ Check `metrics-guide.md` or read category meta file
