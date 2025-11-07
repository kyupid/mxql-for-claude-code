# MXQL Optimization Patterns

This guide provides optimization patterns and anti-patterns for MXQL queries, helping identify and fix performance issues.

## Table of Contents

1. [Filter Optimization](#filter-optimization)
2. [Field Selection Optimization](#field-selection-optimization)
3. [Aggregation Optimization](#aggregation-optimization)
4. [Result Limiting Optimization](#result-limiting-optimization)
5. [Expression Optimization](#expression-optimization)
6. [Subquery Optimization](#subquery-optimization)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Filter Optimization

### Pattern 1: Early Filtering

**Anti-Pattern**: Late filtering (after GROUP)
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos), mem_pct]
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
FILTER {key: "oname", value: ["prod-db-01", "prod-db-02"]}  ❌ Too late!
```

**Optimized Pattern**: Filter immediately after data loading
```mxql
CATEGORY db_mysql_counter
TAGLOAD
FILTER {key: "oname", value: ["prod-db-01", "prod-db-02"]}  ✅ Early!
SELECT [oname, cpu(xos), mem_pct]
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
```

**Impact**:
- Reduces data volume early in pipeline
- Less memory usage
- Faster aggregation
- Can improve execution time by 50-90% for selective filters

**When to apply**: Always, unless filter condition depends on aggregated values

---

### Pattern 2: Combined Filters

**Anti-Pattern**: Multiple separate filters
```mxql
FILTER {key: "cpu(xos)", cmp: "gt", value: "50"}
FILTER {key: "mem_pct", cmp: "gt", value: "75"}
FILTER {key: "status", value: "active"}
```

**Optimized Pattern**: Single expression filter
```mxql
FILTER {expr: "cpu(xos) > 50 && mem_pct > 75 && status == 'active'"}
```

**Impact**:
- Single pass through data
- Cleaner query structure
- Slightly better performance

**When to apply**: When multiple conditions on same dataset

**Trade-off**: Expression filters are less readable for complex conditions

---

### Pattern 3: OID/Instance Filtering

**Best Practice**: Filter by OID/instance as early as possible

**Note**: OID command can be placed before or after TAGLOAD - both are valid
```mxql
# Option 1: OID before TAGLOAD
CATEGORY db_postgresql_counter
OID [$OID_LIST]
TAGLOAD
SELECT [oname, cpu(xos)]
...

# Option 2: OID after TAGLOAD (also valid)
CATEGORY db_postgresql_counter
TAGLOAD
OID [$OID_LIST]
SELECT [oname, cpu(xos)]
...

# Option 3: Using FILTER (after TAGLOAD)
CATEGORY db_postgresql_counter
TAGLOAD
FILTER {key: "oid", value: [$OID_LIST]}  ✅ Early filtering!
SELECT [oname, cpu(xos)]
...
```

**Why**: OID filtering reduces data volume most effectively
- Filters at source
- Reduces network transfer
- Most selective filter type

---

## Field Selection Optimization

### Pattern 4: Specific Field Selection

**Anti-Pattern**: Select all fields
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [*]  ❌ Wasteful!
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
```

**Optimized Pattern**: Select only needed fields
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, time, cpu(xos)]  ✅ Specific!
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
```

**Impact**:
- Reduced memory usage
- Faster processing
- Less network bandwidth
- Can improve performance by 30-70% depending on field count

**When to apply**: Always, unless truly all fields are needed

---

### Pattern 5: Avoid Redundant SELECT

**Anti-Pattern**: Multiple SELECT commands
```mxql
CATEGORY db_oracle_counter
TAGLOAD
SELECT [oid, oname, cpu(xos), mem_pct, disk_io, network]
SELECT [oid, oname, cpu(xos)]  ❌ Redundant!
```

**Optimized Pattern**: Single SELECT with needed fields
```mxql
CATEGORY db_oracle_counter
TAGLOAD
SELECT [oid, oname, cpu(xos)]  ✅ Direct!
```

**Impact**:
- Cleaner query
- Avoids confusion
- Minimal performance gain but better maintainability

---

## Aggregation Optimization

### Pattern 6: Appropriate Time Units

**Anti-Pattern**: Too granular aggregation
```mxql
# For 7-day trend analysis
GROUP {timeunit: "5s"}  ❌ Way too granular!
# Results in: 7 days × 24 hours × 3600 sec / 5 = 120,960 data points!
```

**Optimized Pattern**: Match timeunit to analysis need
```mxql
# For 7-day trend
GROUP {timeunit: "1h"}  ✅ Appropriate!
# Results in: 7 × 24 = 168 data points
```

**Guidelines**:
- Real-time dashboards: 5s, 10s, 1m
- Short-term monitoring (< 1 hour): 1m, 5m
- Medium-term analysis (hours to days): 5m, 10m, 1h
- Long-term trends (weeks to months): 1h, 1d

**Impact**:
- Massive reduction in result size
- Faster aggregation
- Less memory usage
- Better visualization performance

---

### Pattern 7: Necessary Aggregation Only

**Anti-Pattern**: Unnecessary GROUP
```mxql
# Query just needs current values
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
GROUP {pk: "oname"}  ❌ Unnecessary!
UPDATE {key: "cpu(xos)", value: "avg"}
```

**Optimized Pattern**: Skip aggregation if not needed
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]  ✅ Direct values!
```

**When to aggregate**:
- Time-series analysis (need timeunit)
- Multiple values per key (need to aggregate)
- Calculating statistics (avg, sum, max, etc.)

**When not to aggregate**:
- Just need current/latest values
- Already one value per key
- LAST-ONLY or FIRST-ONLY would work

---

### Pattern 8: Minimize UPDATE Commands

**Anti-Pattern**: Separate UPDATE for each field
```mxql
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}
UPDATE {key: "mem_pct", value: "avg"}
UPDATE {key: "disk_io", value: "avg"}
UPDATE {key: "network", value: "avg"}
UPDATE {key: "sessions", value: "avg"}  ❌ Many UPDATEs
```

**Optimized Pattern**: Use GROUP options when possible
```mxql
GROUP {
  timeunit: "5m",
  merge: "all_metrics"  ✅ Single aggregation spec
}
```

**Or**: Only UPDATE fields that need it
```mxql
GROUP {timeunit: "5m"}
UPDATE {key: "cpu(xos)", value: "avg"}  ✅ Only if needed
```

**Impact**:
- Cleaner query
- Slightly better performance
- Better maintainability

---

## Result Limiting Optimization

### Pattern 9: Always Use LIMIT

**Anti-Pattern**: No LIMIT on potentially large results
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]  ❌ Could return millions!
```

**Optimized Pattern**: Add appropriate LIMIT
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
ORDER {key: [tx_count], sort: "desc"}
LIMIT 100  ✅ Bounded results
```

**Guidelines**:
- Dashboards: LIMIT 10-50
- Tables: LIMIT 100-500
- Reports: LIMIT 1000-5000
- Exports: Consider if LIMIT needed

**Impact**:
- Prevents memory exhaustion
- Faster result transfer
- Better UI performance

---

### Pattern 10: ORDER with LIMIT

**Anti-Pattern**: LIMIT without ORDER (for Top-N intent)
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
LIMIT 10  ❌ Arbitrary 10 instances!
```

**Optimized Pattern**: ORDER before LIMIT
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, cpu(xos)]
ORDER {key: [cpu(xos)], sort: "desc"}  ✅ Top 10 by CPU!
LIMIT 10
```

**Impact**:
- Deterministic results
- Meaningful Top-N queries
- Results match user intent

**Exception**: When order doesn't matter (e.g., sampling)

---

## Expression Optimization

### Pattern 11: CREATE for Calculated Metrics

**Anti-Pattern**: Calculate in application after query
```mxql
# Query
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, Threads_connected, max_connections]

# Then calculate in app:
# connection_pct = (Threads_connected / max_connections) * 100
```

**Optimized Pattern**: Calculate in query with CREATE
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [oname, Threads_connected, max_connections]
CREATE {key: "connection_pct",
        expr: "Threads_connected * 100.0 / max_connections"}  ✅
FILTER {key: "connection_pct", cmp: "gt", value: "80"}
```

**Benefits**:
- Filter on calculated values
- ORDER on calculated values
- Consistent calculation across use cases
- Less application code

---

### Pattern 12: Efficient Expressions

**Anti-Pattern**: Complex redundant expressions
```mxql
CREATE {key: "score1", expr: "(cpu * 0.3 + mem * 0.3 + disk * 0.4)"}
CREATE {key: "score2", expr: "(cpu * 0.3 + mem * 0.3 + disk * 0.4) * 100"}
```

**Optimized Pattern**: Reuse calculated values
```mxql
CREATE {key: "base_score", expr: "cpu * 0.3 + mem * 0.3 + disk * 0.4"}
CREATE {key: "score_pct", expr: "base_score * 100"}  ✅ Reuse!
```

**Impact**:
- Avoid duplicate calculations
- More maintainable
- Clearer intent

---

## Subquery Optimization

### Pattern 13: Efficient Subqueries

**Anti-Pattern**: Subquery returns too much data
```mxql
SUB all_agents
  CATEGORY agent_list
  TAGLOAD
  SELECT [*]  ❌ All fields from all agents!
END

CATEGORY metrics
TAGLOAD
JOIN {query: "all_agents", pk: ["oid"]}
```

**Optimized Pattern**: Filter and select in subquery
```mxql
SUB active_agents
  CATEGORY agent_list
  TAGLOAD
  FILTER {key: "status", value: "active"}  ✅ Filter in sub!
  SELECT [oid, agent_name]  ✅ Only needed fields!
END

CATEGORY metrics
TAGLOAD
JOIN {query: "active_agents", pk: ["oid"]}
```

**Impact**:
- Smaller join tables
- Faster join operation
- Less memory usage

---

### Pattern 14: JOIN Field Selection

**Anti-Pattern**: Join brings all fields
```mxql
SUB agents
  CATEGORY agent_list
  TAGLOAD
  SELECT [oid, agent_name, host, ip, version, ...]
END

CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"]}  ❌ All agent fields joined!
```

**Optimized Pattern**: Specify needed fields
```mxql
SUB agents
  CATEGORY agent_list
  TAGLOAD
  SELECT [oid, agent_name]  ✅ Only needed fields!
END

CATEGORY metrics
TAGLOAD
JOIN {query: "agents", pk: ["oid"], field: ["agent_name"]}  ✅ Explicit!
```

**Impact**:
- Reduced result size
- Clearer data flow
- Better performance

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Kitchen Sink Query

**Problem**: Query does everything, returns everything
```mxql
CATEGORY db_mysql_counter
TAGLOAD
SELECT [*]
CREATE {key: "calc1", expr: "..."}
CREATE {key: "calc2", expr: "..."}
CREATE {key: "calc3", expr: "..."}
GROUP {timeunit: "1m"}
UPDATE {key: "field1", value: "avg"}
UPDATE {key: "field2", value: "sum"}
# ... many more commands
```

**Solution**: Break into focused queries
- One query per analysis purpose
- Combine in application if needed
- Simpler, more maintainable

---

### Anti-Pattern 2: Death by Thousand Filters

**Problem**: Too many individual FILTER commands
```mxql
FILTER {key: "status", value: "active"}
FILTER {key: "type", value: "production"}
FILTER {key: "region", value: "us-east"}
FILTER {key: "version", cmp: "gte", value: "2.0"}
FILTER {key: "cpu", cmp: "gt", value: "10"}
...
```

**Solution**: Use expr or rethink filtering strategy
```mxql
FILTER {expr: "status == 'active' && type == 'production' && region == 'us-east' && version >= '2.0' && cpu > 10"}
```

---

### Anti-Pattern 3: Premature Aggregation

**Problem**: Aggregate before filtering
```mxql
CATEGORY app_counter
TAGLOAD
SELECT [service, tx_count]
GROUP {timeunit: "5m", pk: "service"}
UPDATE {key: "tx_count", value: "sum"}
FILTER {key: "service", value: ["service-a", "service-b"]}  ❌ Late!
```

**Solution**: Filter first, then aggregate
```mxql
CATEGORY app_counter
TAGLOAD
FILTER {key: "service", value: ["service-a", "service-b"]}  ✅ Early!
SELECT [service, tx_count]
GROUP {timeunit: "5m", pk: "service"}
UPDATE {key: "tx_count", value: "sum"}
```

---

### Anti-Pattern 4: Sorting Twice

**Problem**: ORDER appears multiple times
```mxql
ORDER {key: [field1], sort: "desc"}
GROUP {timeunit: "5m"}
ORDER {key: [field2], sort: "asc"}  ❌ Confusing!
```

**Solution**: One ORDER at end
```mxql
GROUP {timeunit: "5m"}
ORDER {key: [field2], sort: "asc"}  ✅ Clear intent!
```

---

### Anti-Pattern 5: Magic Number Limits

**Problem**: Unexplained LIMIT values
```mxql
LIMIT 73  ❌ Why 73?
```

**Solution**: Use meaningful limits
```mxql
LIMIT 10   # Top 10 for dashboard
LIMIT 100  # Standard table view
LIMIT 1000 # Report export
```

Or use parameters:
```mxql
LIMIT $PAGE_SIZE
```

---

## Optimization Decision Tree

```
Query is slow?
├─ Check: Is data volume high?
│  ├─ YES: Add early FILTER (Pattern 1)
│  │       Use specific SELECT (Pattern 4)
│  │       Add LIMIT (Pattern 9)
│  └─ NO: Continue
│
├─ Check: Is aggregation slow?
│  ├─ YES: Use appropriate timeunit (Pattern 6)
│  │       Remove unnecessary GROUP (Pattern 7)
│  └─ NO: Continue
│
├─ Check: Are results too large?
│  ├─ YES: Add LIMIT (Pattern 9)
│  │       Filter more aggressively
│  └─ NO: Continue
│
└─ Check: Is query complex?
   ├─ YES: Simplify expressions (Pattern 12)
   │       Optimize subqueries (Pattern 13)
   └─ NO: May be acceptable
```

---

## Performance Scoring

Grade queries based on optimization level:

### Score 10/10: Perfectly Optimized
- ✅ Early, selective filtering
- ✅ Specific field selection
- ✅ Appropriate aggregation
- ✅ ORDER + LIMIT for Top-N
- ✅ Efficient expressions
- ✅ Clear, maintainable structure

### Score 7-9/10: Well Optimized
- ✅ Most optimizations applied
- ⚠️ Minor improvements possible
- Generally good performance

### Score 4-6/10: Needs Improvement
- ⚠️ Some inefficiencies present
- ⚠️ Missing key optimizations
- May have performance issues at scale

### Score 1-3/10: Poor Performance
- ❌ Multiple anti-patterns
- ❌ Major inefficiencies
- Likely slow or resource-heavy

### Score 0/10: Will Fail or Crash
- ❌ Syntax/semantic errors
- ❌ Will not execute

---

## Optimization Checklist

Before finalizing a query, verify:

**Data Volume**:
- [ ] Early FILTER applied (especially OID/instance)
- [ ] Specific SELECT (no SELECT *)
- [ ] LIMIT present (if large result set possible)

**Aggregation**:
- [ ] Appropriate GROUP timeunit
- [ ] Only necessary aggregations
- [ ] UPDATE only after GROUP

**Structure**:
- [ ] ORDER before LIMIT (if Top-N)
- [ ] Calculated metrics use CREATE
- [ ] Filters combined where reasonable

**Clarity**:
- [ ] Query purpose is clear
- [ ] Commands in logical order
- [ ] No redundant operations

**Performance**:
- [ ] Expected result size is reasonable
- [ ] Time range is appropriate
- [ ] No obvious bottlenecks

---

## Next Steps

After optimization:
1. Test query with realistic data volume
2. Verify results match expectations
3. Monitor query performance
4. Iterate based on actual usage patterns

Remember: **Premature optimization is the root of all evil**, but **obvious inefficiencies should be fixed**.

Balance optimization with:
- Readability
- Maintainability
- Actual performance needs
- Development time

Not every query needs to be perfect—focus on queries that:
- Run frequently
- Process large datasets
- Have user-facing latency requirements
- Consume significant resources
