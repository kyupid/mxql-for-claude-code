---
name: generating-mxql-queries
description: Generates MXQL (Metrics Query Language) queries through conversational interaction. Use this when users need to query metrics for database monitoring (MySQL, PostgreSQL, Oracle, etc.), infrastructure monitoring, or APM. Guides users through selecting categories, metrics, filters, and aggregations to create valid, optimized MXQL queries. Includes validation, explanation, and best practice recommendations.
---

# MXQL Query Generator

## Overview

This skill helps generate MXQL (Metrics Query Language) queries through a conversational, step-by-step approach. Instead of requiring users to know exact category names, field names, and syntax, this skill guides them through the query creation process by asking clarifying questions.

**Current Support**: Database monitoring (15 DB products)
**Expandable to**: Infrastructure, APM, Container, and Cloud monitoring

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

### Step 2: Clarify Product/Category

If the product is not specified or ambiguous, ask the user to select:

```
Which DB product are you monitoring?
1. MySQL / MariaDB
2. PostgreSQL
3. Oracle
4. Microsoft SQL Server
5. MongoDB
6. Redis
7. Other (specify)
```

Map the product to the correct category:
- MySQL → `db_mysql_counter`
- PostgreSQL → `db_postgresql_counter`
- Oracle → `db_oracle_counter`
- MSSQL → `db_mssql_counter`
- MongoDB → `db_mongodb_counter`
- Redis → `db_redis_counter`

For complete category mappings, refer to `db-categories.md`.

### Step 3: Select Metrics

Based on the user's intent, identify relevant metrics. If uncertain, consult `metrics-guide.md` or read the category's meta file.

**Common metric groups**:
- **CPU**: cpu(xos), cpu_user(xos), cpu_sys(xos), cpu_iowait(xos)
- **Memory**: mem_total(xos), mem_used(xos), mem_free(xos), mem_pct
- **Sessions**: active_sessions, lock_wait_sessions, total_sessions
- **I/O**: disk_read(xos), disk_write(xos), iops

For CPU example, include:
- `cpu(xos)` - Total CPU utilization (%)
- `cpu_user(xos)` - User mode CPU
- `cpu_sys(xos)` - System mode CPU
- `cpu_iowait(xos)` - I/O wait (indicates disk bottleneck)

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

## Best Practices

### Do:
- ✅ Filter early (before GROUP) to reduce data volume
- ✅ Use ORDER before LIMIT for Top-N queries
- ✅ Include oname (object name) to identify instances
- ✅ Use appropriate timeunit for GROUP (5m for real-time, 1h for trends)
- ✅ Explain metrics and their units to users
- ✅ Validate queries before returning

### Don't:
- ❌ Use LIMIT without ORDER (results are arbitrary)
- ❌ Use UPDATE without GROUP (will error)
- ❌ Select unnecessary fields (wastes resources)
- ❌ Forget to quote string values in JSON
- ❌ Assume field names without checking meta

## Troubleshooting

### User doesn't know which DB product
→ Ask them to specify or list options

### Metric name unclear
→ Check `metrics-guide.md` or read category meta file
