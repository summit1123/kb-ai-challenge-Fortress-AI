// KB Fortress AI 그래프 완전성 검증 쿼리

// ========================================
// 1. 📊 전체 노드 수 확인 (169개 데이터 → 181개 노드)
// ========================================
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC;

// ========================================
// 2. 🏢 기업 노드 상세 확인 (원본 16개)
// ========================================
MATCH (c:ReferenceCompany)
RETURN c.companyName as 기업명, 
       c.sector as 업종,
       c.nodeId as ID
ORDER BY c.companyName;

// 기업 중복 확인
MATCH (c:ReferenceCompany)
WITH c.companyName as name, count(*) as cnt
WHERE cnt > 1
RETURN name as 중복기업, cnt as 중복수;

// ========================================
// 3. 📋 정책 노드 검증 (정확히 71개여야 함)
// ========================================
MATCH (p:Policy)
RETURN count(p) as 총_정책수;

// 정책 샘플 확인
MATCH (p:Policy)
RETURN p.policyName as 정책명,
       p.issuingOrg as 발행기관,
       p.nodeId as ID
ORDER BY p.nodeId
LIMIT 10;

// ========================================
// 4. 📰 뉴스 노드 검증 (정확히 61개여야 함)
// ========================================
MATCH (n:NewsArticle)
RETURN count(n) as 총_뉴스수;

// 뉴스 카테고리별 분포
MATCH (n:NewsArticle)
RETURN n.category as 카테고리, count(n) as 개수
ORDER BY 개수 DESC;

// 뉴스 샘플 확인
MATCH (n:NewsArticle)
RETURN n.title as 제목,
       n.publisher as 언론사,
       n.publishDate as 날짜
ORDER BY n.publishDate DESC
LIMIT 10;

// ========================================
// 5. 💰 KB상품 노드 검증 (원본 19개)
// ========================================
MATCH (k:KB_Product)
RETURN count(k) as 총_KB상품수;

// KB상품 타입별 분포
MATCH (k:KB_Product)
RETURN k.productType as 상품유형, count(k) as 개수;

// ========================================
// 6. 📈 거시지표 노드 검증 (원본 2개)
// ========================================
MATCH (m:MacroIndicator)
RETURN m.indicatorName as 지표명,
       m.value as 현재값,
       m.unit as 단위;

// ========================================
// 7. 🔗 관계 완전성 검증
// ========================================
// 전체 관계 통계
MATCH ()-[r]->()
RETURN type(r) as 관계타입, count(r) as 개수
ORDER BY 개수 DESC;

// 기업-정책 매칭 확인
MATCH (c:ReferenceCompany)-[r:IS_ELIGIBLE_FOR]->(p:Policy)
RETURN count(r) as 기업_정책_매칭수;

// 뉴스-기업 영향 확인
MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->(c:ReferenceCompany)
RETURN count(r) as 뉴스_기업_영향수;

// 뉴스-거시지표 영향 확인
MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->(m:MacroIndicator)
RETURN count(r) as 뉴스_거시지표_영향수;

// ========================================
// 8. 🎯 원본 데이터 대비 검증
// ========================================
// 예상: 기업 16, KB상품 19, 정책 71, 뉴스 61, 거시지표 2 = 총 169
WITH {
  '기업_원본': 16,
  '기업_실제': 0,
  'KB상품_원본': 19,
  'KB상품_실제': 0,
  '정책_원본': 71,
  '정책_실제': 0,
  '뉴스_원본': 61,
  '뉴스_실제': 0,
  '거시지표_원본': 2,
  '거시지표_실제': 0
} as stats
MATCH (c:ReferenceCompany)
WITH stats, count(c) as companyCount
MATCH (k:KB_Product)
WITH stats, companyCount, count(k) as kbCount
MATCH (p:Policy)
WITH stats, companyCount, kbCount, count(p) as policyCount
MATCH (n:NewsArticle)
WITH stats, companyCount, kbCount, policyCount, count(n) as newsCount
MATCH (m:MacroIndicator)
WITH stats, companyCount, kbCount, policyCount, newsCount, count(m) as macroCount
RETURN 
  stats['기업_원본'] as 기업_원본,
  companyCount as 기업_실제,
  stats['KB상품_원본'] as KB상품_원본,
  kbCount as KB상품_실제,
  stats['정책_원본'] as 정책_원본,
  policyCount as 정책_실제,
  stats['뉴스_원본'] as 뉴스_원본,
  newsCount as 뉴스_실제,
  stats['거시지표_원본'] as 거시지표_원본,
  macroCount as 거시지표_실제,
  (companyCount + kbCount + policyCount + newsCount + macroCount) as 총_노드수;

// ========================================
// 9. 🚨 데이터 무결성 검증
// ========================================
// nodeId가 없는 노드 찾기
MATCH (n)
WHERE n.nodeId IS NULL
RETURN labels(n) as 타입, count(n) as nodeId_없는_노드수;

// 고아 노드 찾기 (관계가 없는 노드)
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n)[0] as 타입, count(n) as 고아노드수;

// ========================================
// 10. 💡 핵심 비즈니스 패턴 검증
// ========================================
// 가장 많은 정책 매칭을 받은 기업
MATCH (c:ReferenceCompany)-[r:IS_ELIGIBLE_FOR]->(p:Policy)
WITH c, count(p) as policyCount
ORDER BY policyCount DESC
LIMIT 5
RETURN c.companyName as 기업명, policyCount as 매칭_정책수;

// 가장 영향력 있는 뉴스
MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->()
WITH n, count(r) as impactCount
ORDER BY impactCount DESC
LIMIT 5
RETURN n.title as 뉴스제목, impactCount as 영향_대상수;