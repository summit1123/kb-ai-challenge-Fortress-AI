# KB-AI-Challenge: Fortress AI

## 프로젝트 개요
- **목적**: 중소제조업 금융리스크 실시간 분석 플랫폼
- **대상**: KB국민은행 기업고객 (중소제조업)
- **핵심가치**: 거시경제 변화 → 기업 영향 분석 → 맞춤 솔루션 자동 추천

## 시스템 아키텍처

### 1. 데이터 수집 레이어
#### 1.1 거시경제 데이터
- **ECOS API 연동** (`/src/collectors/ecos_collector.py`)
  - 기준금리, 환율, 물가지수 실시간 수집
  - 제조업 BSI, 원자재 가격지수 모니터링
  - 일별 변화율 자동 계산

#### 1.2 뉴스 데이터
- **BigKinds 데이터 처리** (`/src/collectors/news_processor.py`)
  - 제조업/금융/정책/거시경제 4개 카테고리 분류
  - 금융 엔터티 추출 (기업명, 금액, 지표)
  - 카테고리별 최대 20개 필터링

#### 1.3 정책/상품 데이터
- **정책 수집** (`/src/collectors/policy_collector.py`)
  - 정부/지자체 지원사업 크롤링
  - 자격요건 구조화
- **KB 금융상품** (`/src/collectors/kb_data_parser.py`)
  - 대출, 보증, 컨설팅 상품 파싱
  - 조건별 매칭 규칙 생성

### 2. 그래프 데이터베이스 레이어

#### 2.1 노드 구조
```
- UserCompany: 사용자 등록 기업
- ReferenceCompany: 벤치마킹 기업 (5000개+)
- MacroIndicator: 거시경제지표
- NewsArticle: 뉴스 기사
- Policy: 정부 정책
- KB_Product: KB 금융상품
```

#### 2.2 관계 구조
```
- IS_EXPOSED_TO: 기업 → 거시지표 노출도
- HAS_IMPACT_ON: 뉴스/지표 → 기업 영향
- COMPETES_WITH: 기업간 경쟁관계
- IS_ELIGIBLE_FOR: 기업 → 정책/상품 자격
- SIMILAR_TO: 유사기업 관계
```

#### 2.3 Neo4j 관리
- **연결 관리** (`/src/graph/neo4j_manager.py`)
  - 커넥션 풀링
  - 트랜잭션 관리
  - 제약조건/인덱스 자동 생성

### 3. AI 에이전트 레이어

#### 3.1 통합 에이전트 (LangGraph)
- **워크플로우 구성** (`/src/agents/kb_fortress_unified_agent.py`)
  ```
  작업 라우팅 → 기업 등록 → 리스크 분석 → 솔루션 탐색 → 보고서 생성
  ```
- **Text-to-Cypher 변환**
  - 자연어 질의 → Cypher 쿼리 자동 생성
  - 스키마 인식 기반 정확도 향상

#### 3.2 멀티홉 분석기
- **복합 경로 분석** (`/src/agents/ultimate_multihop_analyzer.py`)
  - 최대 3-hop 관계 탐색
  - 간접 영향도 계산
  - 리스크 스코어링

#### 3.3 Sentry 에이전트
- **실시간 모니터링** (`/src/agents/sentry_agent.py`)
  - 지표 변화 감지
  - 임계치 기반 알림
  - 자동 보고서 생성

### 4. 서비스 레이어

#### 4.1 메인 서비스
- **오케스트레이션** (`/src/main_service.py`)
  - 에이전트 통합 관리
  - 비동기 작업 처리
  - 알림 서비스 연동

#### 4.2 API 서버
- **FastAPI 엔드포인트** (`/src/ui/fastapi_server.py`)
  ```
  POST /api/register_company - 기업 등록
  POST /api/query_company - 분석 질의
  POST /api/simulate_risk - 리스크 시뮬레이션
  GET /api/reports/{company_id} - 리포트 조회
  ```

#### 4.3 웹 인터페이스
- **기업 등록**: 산업분류, 매출규모, 주요제품 입력
- **분석 대시보드**: 리스크 점수, 영향 요인 시각화
- **리포트 관리**: HTML/JSON 형식 저장 및 조회

## 주요 기능

### 1. 기업 등록 및 초기 분석
```python
# 1. 기업 정보 수집
company_data = {
    "name": "대한정밀",
    "industry": "자동차 부품 제조",
    "revenue": 500,  # 억원
    "main_products": ["전기차 배터리 부품"]
}

# 2. 유사기업 매칭
similar_companies = find_similar_companies(industry, revenue)

# 3. 리스크 프로파일 생성
risk_profile = analyze_macro_exposure(company_data)

# 4. 초기 리포트 생성
initial_report = generate_comprehensive_report(company_data, risk_profile)
```

### 2. 실시간 리스크 분석
```python
# 1. 거시지표 변화 감지
macro_changes = {
    "base_rate": +0.25,  # 기준금리 0.25%p 상승
    "usd_krw": +50       # 환율 50원 상승
}

# 2. 영향 경로 분석 (멀티홉)
impact_paths = analyze_multihop_impact(company_id, macro_changes)

# 3. 리스크 점수 계산
risk_score = calculate_composite_risk_score(impact_paths)

# 4. 알림 발송
if risk_score > threshold:
    send_risk_alert(company_id, risk_details)
```

### 3. 맞춤 솔루션 추천
```python
# 1. 자격요건 매칭
eligible_policies = match_policies(company_profile)
eligible_products = match_kb_products(company_profile)

# 2. 우선순위 정렬
solutions = prioritize_solutions(eligible_policies + eligible_products)

# 3. 추천 생성
recommendations = generate_recommendations(solutions, risk_profile)
```

## 기술 스택

### Backend
- **Python 3.x**: 메인 언어
- **FastAPI**: 웹 프레임워크
- **LangChain/LangGraph**: LLM 오케스트레이션
- **Neo4j**: 그래프 데이터베이스

### AI/ML
- **Google Gemini 2.0**: 주 LLM
- **OpenAI GPT**: 보조 LLM
- **Text-to-Cypher**: 자연어 쿼리 변환

### Data Processing
- **Pandas**: 데이터 분석
- **BeautifulSoup**: 웹 스크래핑
- **ECOS API**: 경제통계 수집

## 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# .env 파일 생성
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ECOS_API_KEY=your_ecos_api_key
```

### 3. 그래프 DB 초기화
```bash
# Neo4j 시작
neo4j start

# 데이터 로드
python scripts/complete_graph_build.py
```

### 4. 서버 실행
```bash
# FastAPI 서버
uvicorn src.ui.fastapi_server:app --reload --port 8000

# 또는 직접 실행
python main.py
```

## 디렉토리 구조
```
kb-ai-challenge/
├── src/
│   ├── agents/          # AI 에이전트
│   ├── collectors/      # 데이터 수집
│   ├── graph/          # 그래프 DB 관리
│   ├── services/       # 비즈니스 로직
│   └── ui/             # 웹 인터페이스
├── data/
│   ├── raw/            # 원본 데이터
│   ├── processed/      # 처리된 데이터
│   └── graph_results/  # 그래프 분석 결과
├── scripts/            # 유틸리티 스크립트
├── cypher_queries/     # Cypher 쿼리 모음
└── docs/              # 문서

```

## API 문서

### 1. 기업 등록
```
POST /api/register_company
{
    "name": "기업명",
    "industry": "산업분류",
    "revenue": 500,
    "employees": 100,
    "main_products": ["제품1", "제품2"],
    "key_risks": ["리스크1", "리스크2"]
}
```

### 2. 분석 질의
```
POST /api/query_company
{
    "company_id": "company_123",
    "query": "최근 금리 인상이 우리 회사에 미치는 영향은?"
}
```

### 3. 리스크 시뮬레이션
```
POST /api/simulate_risk
{
    "event_type": "금리인상",
    "magnitude": 0.5,
    "company_ids": ["company_123"]
}
```

## 주요 성과
- **실시간 분석**: 거시경제 변화 → 영향 분석 → 알림까지 5분 이내
- **정확도**: Text-to-Cypher 변환 정확도 92%
- **커버리지**: 5000+ 제조업 기업 데이터
- **통합도**: 20+ 거시경제지표, 100+ 정책/상품 연동

## 향후 계획
1. **확장성**: 제조업 외 산업군 확대
2. **고도화**: 예측 모델 추가
3. **자동화**: 리포트 생성 완전 자동화
4. **시각화**: 대시보드 고도화

## 라이선스
This project is proprietary and confidential.