// ================================================
// KB Fortress AI 시각화를 위한 Cypher 쿼리 모음
// ================================================

// ========================================
// 1. 🌟 전체 그래프 구조 한눈에 보기 (LIMIT 사용)
// ========================================
// 각 타입별로 샘플 노드와 모든 관계 표시
MATCH (c:ReferenceCompany) WITH c LIMIT 5
MATCH (k:KB_Product) WITH c, k LIMIT 5
MATCH (p:Policy) WITH c, k, p LIMIT 10
MATCH (n:NewsArticle) WITH c, k, p, n LIMIT 10
MATCH (m:MacroIndicator)
MATCH path = (c)-[*1..2]-(connected)
RETURN path
UNION
MATCH path = (k)-[*1..2]-(connected)
RETURN path
UNION
MATCH path = (p)-[*1..2]-(connected)
RETURN path
UNION
MATCH path = (n)-[*1..2]-(connected)
RETURN path
UNION
MATCH path = (m)-[*1..2]-(connected)
RETURN path;

// ========================================
// 2. 💰 기업 중심 리스크 네트워크
// ========================================
// 특정 기업의 모든 연결 관계 (현대모비스 예시)
MATCH (c:ReferenceCompany {companyName: "현대모비스"})
OPTIONAL MATCH (c)-[r1:IS_EXPOSED_TO]->(m:MacroIndicator)
OPTIONAL MATCH (c)-[r2:IS_ELIGIBLE_FOR]->(p:Policy)
OPTIONAL MATCH (c)-[r3:IS_ELIGIBLE_FOR]->(k:KB_Product)
OPTIONAL MATCH (c)-[r4:COMPETES_WITH]-(c2:ReferenceCompany)
OPTIONAL MATCH (n:NewsArticle)-[r5:HAS_IMPACT_ON]->(c)
RETURN c, r1, m, r2, p, r3, k, r4, c2, r5, n;

// ========================================
// 3. 🚨 고위험 기업 네트워크
// ========================================
// 변동금리 노출이 높은 기업들과 그들의 리스크 관계
MATCH (c:ReferenceCompany)-[r:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE r.exposureLevel = "HIGH"
OPTIONAL MATCH (c)-[r2:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product OR solution:Policy
RETURN c, r, m, r2, solution
LIMIT 50;

// ========================================
// 4. 📰 뉴스 영향 네트워크
// ========================================
// 가장 영향력 있는 뉴스와 영향받는 대상들
MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->(target)
WITH n, count(r) as impactCount
ORDER BY impactCount DESC
LIMIT 10
MATCH (n)-[r:HAS_IMPACT_ON]->(target)
RETURN n, r, target;

// ========================================
// 5. 🎯 정책-기업 매칭 네트워크
// ========================================
// 가장 많은 정책 혜택을 받을 수 있는 기업들
MATCH (c:ReferenceCompany)-[r:IS_ELIGIBLE_FOR]->(p:Policy)
WITH c, count(p) as policyCount
WHERE policyCount > 3
MATCH (c)-[r:IS_ELIGIBLE_FOR]->(p:Policy)
OPTIONAL MATCH (c)-[r2:IS_EXPOSED_TO]->(m:MacroIndicator)
RETURN c, r, p, r2, m;

// ========================================
// 6. 🏭 업종별 경쟁 관계 네트워크
// ========================================
// 같은 업종 내 경쟁 관계와 리스크 노출
MATCH (c1:ReferenceCompany)-[comp:COMPETES_WITH]-(c2:ReferenceCompany)
WHERE c1.sector = c2.sector
OPTIONAL MATCH (c1)-[r1:IS_EXPOSED_TO]->(m1:MacroIndicator)
OPTIONAL MATCH (c2)-[r2:IS_EXPOSED_TO]->(m2:MacroIndicator)
RETURN c1, comp, c2, r1, m1, r2, m2;

// ========================================
// 7. 💡 KB 금융상품 추천 네트워크
// ========================================
// KB 상품과 적합한 기업들의 매칭
MATCH (k:KB_Product)-[r:IS_ELIGIBLE_FOR]-(c:ReferenceCompany)
WHERE r.eligibilityScore > 0.7
OPTIONAL MATCH (c)-[r2:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE r2.exposureLevel IN ["HIGH", "MEDIUM"]
RETURN k, r, c, r2, m;

// ========================================
// 8. 🌐 금리 리스크 전파 네트워크
// ========================================
// 기준금리 변동이 미치는 영향 네트워크
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
MATCH (m)<-[r1:IS_EXPOSED_TO]-(c:ReferenceCompany)
WHERE r1.exposureLevel IN ["HIGH", "MEDIUM"]
OPTIONAL MATCH (n:NewsArticle)-[r2:HAS_IMPACT_ON]->(m)
OPTIONAL MATCH (c)-[r3:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product AND solution.productName CONTAINS "금리"
RETURN m, r1, c, r2, n, r3, solution;

// ========================================
// 9. 🔄 순환 영향 관계 (복잡한 네트워크)
// ========================================
// 뉴스 → 거시지표 → 기업 → 정책의 순환 구조
MATCH path = (n:NewsArticle)-[:HAS_IMPACT_ON]->(m:MacroIndicator)<-[:IS_EXPOSED_TO]-(c:ReferenceCompany)-[:IS_ELIGIBLE_FOR]->(p:Policy)
RETURN path
LIMIT 20;

// ========================================
// 10. 📊 대시보드용 핵심 지표 네트워크
// ========================================
// 주요 노드만 선별하여 깔끔한 시각화
MATCH (c:ReferenceCompany)
WHERE c.variableRateExposure > 0.6
WITH c LIMIT 5
MATCH (m:MacroIndicator)
WITH c, m
MATCH (k:KB_Product)
WHERE k.productType = "운전자금"
WITH c, m, k LIMIT 3
MATCH (p:Policy)
WHERE p.supportField CONTAINS "제조업"
WITH c, m, k, p LIMIT 5
MATCH path = (c)-[*1..2]-(connected)
WHERE connected = m OR connected = k OR connected = p
RETURN path;

// ========================================
// 11. 🎨 프레젠테이션용 임팩트 있는 시각화
// ========================================
// 중소기업 금융 리스크 관리의 전체 그림
MATCH (company:ReferenceCompany)
WHERE company.companyName IN ["현대모비스", "만도", "포스코홀딩스", "대한정밀"]
MATCH (indicator:MacroIndicator)
MATCH (news:NewsArticle) WITH company, indicator, news LIMIT 5
MATCH (policy:Policy) WITH company, indicator, news, policy LIMIT 5
MATCH (product:KB_Product) WITH company, indicator, news, policy, product LIMIT 3
MATCH path = (company)-[*1..2]-(connected)
WHERE connected IN [indicator, news, policy, product]
RETURN path;

// ========================================
// 12. 🌟 3D 네트워크 시각화용 (Neo4j Bloom 추천)
// ========================================
// 전체 그래프의 핵심 구조
MATCH (n)
WHERE n:ReferenceCompany OR n:MacroIndicator OR 
      (n:KB_Product AND n.productType = "운전자금") OR
      (n:Policy AND n.supportField CONTAINS "제조업") OR
      (n:NewsArticle AND n.category = "financial")
WITH n LIMIT 100
MATCH (n)-[r]-(m)
RETURN n, r, m;

// ========================================
// 시각화 팁:
// 1. Neo4j Browser에서 실행 후 좌측 하단 설정에서 노드 색상/크기 조정
// 2. 노드 라벨 표시: 기업명, 정책명, 뉴스 제목 등
// 3. 관계 두께: eligibilityScore, impactScore 값에 따라 조정
// 4. 레이아웃: Force-directed layout 사용 권장
// ========================================