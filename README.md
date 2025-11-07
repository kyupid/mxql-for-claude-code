# MXQL for Claude Code

Claude Code skill for MXQL (Metrics Query Language) - WhaTap's query language for monitoring metrics.

## What is this?

A complete toolkit for working with MXQL queries in Claude Code:
- 🔧 **Query Generation** - Conversational query creation with smart category recommendations
- 🔍 **Query Analysis** - Syntax validation and optimization
- ✅ **Auto Validation** - Python-based validator (no Java required)
- 🧪 **Test Generation** - Create testable queries with sample data
- 🔎 **Category Discovery** - Search and recommend from 631 categories across 36+ product types

**Supported Products**: Database (44), Application/APM (16), Infrastructure (16), Kubernetes (28), AWS (107), Azure (147), OCI (48), NCloud (11), Container, RUM, and more.

## Installation

```bash
./install.sh
```

The installer will:
- Create `~/.claude/skills` directory if it doesn't exist
- Link the mxql skill to your Claude Code skills directory
- Make the skill available globally across all your projects

**What's included:**
- MXQL skill files (SKILL.md, guides, utilities)
- 631 category metadata files covering 36+ product types
- Auto-generated search index (category-index.json)
- Python utilities (validator, test generator, category finder)

## Example Questions

### Database Monitoring
```
"PostgreSQL에서 CPU 80% 이상이고 active session 10개 넘는 인스턴스 찾는 MXQL 만들어줘"

"MySQL 슬로우 쿼리 중에 실행 횟수 많은 top 20개 쿼리 분석하는 쿼리 만들어줘"

"Oracle DMA에서 wait class별 대기 시간 합계 구하는 쿼리 생성해줘"
```

### Kubernetes Monitoring
```
"Pod CPU 사용률 90% 이상인 것들 namespace별로 그룹핑해서 보여줘"

"메모리 부족으로 OOM 발생한 Pod 리스트 최근 1시간 조회하는 MXQL 만들어줘"

"CronJob 실패 이력을 최근 24시간 기준으로 집계하는 쿼리"
```

### Cloud Monitoring
```
"AWS Lambda 함수 중에 에러율 5% 이상이고 invocation 1000회 넘는 함수 찾아줘"

"Azure VM 디스크 IOPS 높은 순으로 top 10 조회하는 쿼리"

"NCloud LoadBalancer의 5분간 평균 응답시간과 에러 카운트 조회"
```

### Infrastructure
```
"서버 디스크 사용률 85% 이상이고 inode 사용률도 높은 서버 찾기"

"네트워크 트래픽 1Gbps 이상인 서버를 대역폭 사용률 순으로 정렬"
```

### Application Performance
```
"Java 애플리케이션 GC 시간이 1초 이상 걸린 인스턴스 조회"

"트랜잭션 응답시간 3초 이상이고 에러율 1% 이상인 서비스 찾기"
```

### Query Analysis & Optimization
```
"이 PostgreSQL sqlstat 쿼리 분석해주고 성능 개선 방법 알려줘"

"JOIN 쿼리 최적화해줘 - 과거 데이터랑 현재 데이터 비교하는 쿼리인데 느려"
```

### Testing & Validation
```
"Kubernetes Pod 모니터링 쿼리 만들고 ADDROW로 테스트 데이터 3개 넣어서 검증해줘"

"이 MXQL이 문법적으로 맞는지 검증하고 문제 있으면 수정해줘"
```

## Features

- **Smart Category Discovery**: Search and recommend from 631 categories across 36+ product types
- **No Java Required**: Python-based validation works standalone
- **ADDROW Pattern**: Test queries without real data sources
- **Best Practices**: Follows MXQL optimization patterns
- **Multi-language Support**: Category metadata in English, Korean, Japanese
- **Comprehensive**: Generation + Analysis + Testing + Discovery in one skill

## Structure

```
mxql/
├── SKILL.md                    # Main skill definition
├── category_finder.py          # Category search & recommendation engine
├── mxql_validator.py           # Python validator
├── test_query_generator.py     # Test query generator
├── categories/                 # 631 category metadata files
│   ├── category-index.json     # Auto-generated search index
│   ├── db_*.meta              # Database categories
│   ├── kube_*.meta            # Kubernetes categories
│   ├── aws_*.meta             # AWS categories
│   ├── azure_*.meta           # Azure categories
│   └── ...                    # More categories
├── generating-guide.md         # Query generation guide
├── analyzing-guide.md          # Analysis guide
├── analysis-checklist.md       # Validation rules
├── optimization-patterns.md    # Performance patterns
└── common-issues.md           # Troubleshooting
```

## License

MIT
