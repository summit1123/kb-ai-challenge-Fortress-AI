// KB Fortress AI 지식그래프 전체 구조 확인 Cypher 쿼리

// 1. 📊 전체 노드 현황 (타입별 개수)
MATCH (n)
WITH labels(n) as nodeTypes, count(n) as count
UNWIND nodeTypes as nodeType
WITH nodeType, sum(count) as totalCount
RETURN nodeType, totalCount
ORDER BY totalCount DESC;

// 2. 🔗 전체 관계 현황 (관계별 개수)  
MATCH ()-[r]->()
RETURN type(r) as relationshipType, count(r) as count
ORDER BY count DESC;

// 3. 🏢 제조업 기업 노드들 상세 정보
MATCH (rc:ReferenceCompany)
RETURN rc.companyName as 기업명, 
       rc.sector as 업종,
       rc.revenue as 매출액,
       rc.debtRatio as 부채비율,
       rc.variableRateExposure as 변동금리노출,
       rc.exportRatioPct as 수출비중
ORDER BY rc.revenue DESC
LIMIT 10;

// 4. ⚠️ 금리 리스크 노출 관계 (IS_EXPOSED_TO)
MATCH (rc:ReferenceCompany)-[r:IS_EXPOSED_TO]->(mi:MacroIndicator)
WHERE mi.indicatorName CONTAINS "금리"
RETURN rc.companyName as 기업명,
       mi.indicatorName as 지표명,
       r.exposureLevel as 노출수준,
       r.rationale as 근거
ORDER BY 
  CASE r.exposureLevel 
    WHEN 'HIGH' THEN 3
    WHEN 'MEDIUM' THEN 2 
    WHEN 'LOW' THEN 1
  END DESC;

// 5. 💰 KB 상품 추천 관계 (IS_ELIGIBLE_FOR)
MATCH (rc:ReferenceCompany)-[r:IS_ELIGIBLE_FOR]->(kb:KB_Product)
RETURN rc.companyName as 기업명,
       kb.productName as 상품명,
       kb.productType as 상품유형,
       r.eligibilityScore as 적합도점수,
       r.recommendationReason as 추천사유
ORDER BY r.eligibilityScore DESC
LIMIT 10;

// 6. 📰 뉴스 영향 관계 (HAS_IMPACT_ON)
MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->(target)
RETURN n.title as 뉴스제목,
       n.publisher as 언론사,
       labels(target) as 영향대상타입,
       r.impactScore as 영향점수,
       r.impactDirection as 영향방향,
       r.rationale as 영향근거
ORDER BY r.impactScore DESC
LIMIT 15;

// 7. 🎯 정책 매칭 관계
MATCH (rc:ReferenceCompany)-[r:IS_ELIGIBLE_FOR]->(p:Policy)
RETURN rc.companyName as 기업명,
       p.policyName as 정책명,
       p.issuingOrg as 발표기관,
       r.eligibilityScore as 적합도점수,
       r.matchingConditions as 매칭조건
ORDER BY r.eligibilityScore DESC
LIMIT 10;

// 8. 🔄 기업간 경쟁 관계 (COMPETES_WITH)
MATCH (rc1:ReferenceCompany)-[r:COMPETES_WITH]->(rc2:ReferenceCompany)
RETURN rc1.companyName as 기업A,
       rc2.companyName as 기업B,
       rc1.sector as 업종,
       r.similarityScore as 유사도점수,
       r.competitionType as 경쟁유형,
       r.commonFactors as 공통요소
ORDER BY r.similarityScore DESC;

// 9. 📈 환율 리스크 노출 관계
MATCH (rc:ReferenceCompany)-[r:IS_EXPOSED_TO]->(mi:MacroIndicator)
WHERE mi.indicatorName CONTAINS "환율"
RETURN rc.companyName as 기업명,
       rc.exportRatioPct as 수출비중,
       r.exposureLevel as 환율노출수준,
       r.rationale as 근거
ORDER BY rc.exportRatioPct DESC;

// 10. 🏗️ 전체 그래프 구조 시각화 (노드-관계-노드 패턴)
MATCH (source)-[r]->(target)
RETURN DISTINCT 
       labels(source)[0] as 시작노드타입,
       type(r) as 관계타입,
       labels(target)[0] as 끝노드타입,
       count(*) as 관계수
ORDER BY 관계수 DESC;

// 11. 🎲 랜덤 그래프 샘플 (전체 구조 미리보기)
MATCH path = (n1)-[r1]->(n2)-[r2]->(n3)
WHERE labels(n1)[0] IN ['ReferenceCompany', 'NewsArticle']
RETURN path
LIMIT 5;

// 12. 📊 노드별 연결성 통계 (중요도 분석)
MATCH (n)
OPTIONAL MATCH (n)-[r_out]->()
OPTIONAL MATCH ()-[r_in]->(n)
RETURN labels(n)[0] as 노드타입,
       count(DISTINCT r_out) as 나가는관계수,
       count(DISTINCT r_in) as 들어오는관계수,
       count(DISTINCT r_out) + count(DISTINCT r_in) as 총연결수
ORDER BY 총연결수 DESC;

// 13. 🚨 고위험 기업 식별 (복합 리스크 분석)
MATCH (rc:ReferenceCompany)-[r1:IS_EXPOSED_TO]->(mi:MacroIndicator)
OPTIONAL MATCH (news:NewsArticle)-[r2:HAS_IMPACT_ON]->(rc)
WHERE r1.exposureLevel IN ['HIGH', 'MEDIUM']
RETURN rc.companyName as 기업명,
       rc.sector as 업종,
       rc.debtRatio as 부채비율,
       collect(DISTINCT mi.indicatorName) as 노출지표,
       collect(DISTINCT r1.exposureLevel) as 노출수준,
       count(DISTINCT news) as 관련뉴스수
ORDER BY rc.debtRatio DESC;

// 14. 💡 기회 포착 기업 (정책+상품 매칭)
MATCH (rc:ReferenceCompany)
OPTIONAL MATCH (rc)-[r1:IS_ELIGIBLE_FOR]->(kb:KB_Product)
OPTIONAL MATCH (rc)-[r2:IS_ELIGIBLE_FOR]->(p:Policy)
WHERE r1.eligibilityScore > 0.7 OR r2.eligibilityScore > 0.7
RETURN rc.companyName as 기업명,
       count(DISTINCT kb) as 추천KB상품수,
       count(DISTINCT p) as 적합정책수,
       avg(r1.eligibilityScore) as 평균상품적합도,
       avg(r2.eligibilityScore) as 평균정책적합도
ORDER BY (count(DISTINCT kb) + count(DISTINCT p)) DESC;

// 15. 🌐 전체 그래프 메타 정보
CALL db.schema.visualization();