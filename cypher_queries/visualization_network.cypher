// ================================================
// 그래프 시각화용 네트워크 쿼리 모음
// Neo4j Browser에서 바로 시각화 가능
// ================================================

// ========================================
// 1. 🌟 대한정밀 중심 전체 네트워크
// ========================================
// 대한정밀과 모든 연결 관계 시각화
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH path1 = (u)-[r1]-(connected1)
OPTIONAL MATCH path2 = (connected1)-[r2]-(connected2)
WHERE connected2 <> u
RETURN path1, path2
LIMIT 50;

// ========================================
// 2. 🔴 리스크 전파 네트워크
// ========================================
// 금리 변동이 어떻게 전파되는지 시각화
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
MATCH path = (m)<-[:IS_EXPOSED_TO]-(company)
OPTIONAL MATCH extension = (company)-[:IS_ELIGIBLE_FOR]->(solution)
RETURN path, extension
LIMIT 30;

// ========================================
// 3. 🎯 자동차부품 업종 클러스터
// ========================================
// 자동차부품업체들 간의 관계망
MATCH (c1:ReferenceCompany {sector: "automotive_parts"})
MATCH (c2:ReferenceCompany {sector: "automotive_parts"})
WHERE c1 <> c2
OPTIONAL MATCH path = (c1)-[*1..2]-(c2)
RETURN path
LIMIT 40;

// ========================================
// 4. 💰 KB 상품 추천 네트워크
// ========================================
// KB 상품과 적합한 기업들의 매칭
MATCH (k:KB_Product)
MATCH (company)-[r:IS_ELIGIBLE_FOR]->(k)
WHERE r.eligibilityScore > 0.7
RETURN k, r, company
LIMIT 50;

// ========================================
// 5. 📋 정책 활용 네트워크
// ========================================
// 정부 정책과 기업들의 매칭 관계
MATCH (p:Policy)
MATCH (company)-[r:IS_ELIGIBLE_FOR]->(p)
WHERE company:ReferenceCompany OR company:UserCompany
WITH p, collect({company: company, score: r.eligibilityScore}) as matches
WHERE size(matches) > 3
UNWIND matches as match
RETURN p, match.company, match.score
LIMIT 60;

// ========================================
// 6. 📰 뉴스 영향 네트워크
// ========================================
// 뉴스가 기업/지표에 미치는 영향
MATCH (n:NewsArticle)
WHERE n.publishDate > datetime() - duration({days: 30})
MATCH (n)-[r:HAS_IMPACT_ON]->(target)
RETURN n, r, target
LIMIT 40;

// ========================================
// 7. 🔄 순환 영향 네트워크
// ========================================
// 뉴스 → 지표 → 기업 → 솔루션의 순환 구조
MATCH path = (n:NewsArticle)-[:HAS_IMPACT_ON]->(m:MacroIndicator)<-[:IS_EXPOSED_TO]-(c)-[:IS_ELIGIBLE_FOR]->(s)
WHERE n.category = "financial"
RETURN path
LIMIT 20;

// ========================================
// 8. 🌐 다층 네트워크 (대한정밀 중심)
// ========================================
// 1단계, 2단계, 3단계 연결 모두 표시
MATCH (u:UserCompany {companyName: "대한정밀"})
// 1단계 연결
MATCH (u)-[r1]-(level1)
// 2단계 연결
OPTIONAL MATCH (level1)-[r2]-(level2)
WHERE level2 <> u AND NOT level2:UserCompany
WITH u, r1, level1, r2, level2 LIMIT 30
RETURN u, r1, level1, r2, level2;

// ========================================
// 9. 🎨 색상별 노드 타입 네트워크
// ========================================
// 각 노드 타입별로 구분해서 시각화
MATCH (company)
WHERE company:ReferenceCompany OR company:UserCompany
MATCH (policy:Policy)
MATCH (product:KB_Product)  
MATCH (indicator:MacroIndicator)
MATCH (news:NewsArticle)
WITH company, policy, product, indicator, news LIMIT 5
OPTIONAL MATCH path1 = (company)-[]-(policy)
OPTIONAL MATCH path2 = (company)-[]-(product)
OPTIONAL MATCH path3 = (company)-[]-(indicator)
OPTIONAL MATCH path4 = (news)-[]-(company)
RETURN path1, path2, path3, path4
LIMIT 50;

// ========================================
// 10. 🏆 고가치 연결 네트워크
// ========================================
// 높은 점수의 관계만 시각화 (핵심 연결)
MATCH (source)-[r]-(target)
WHERE (r.eligibilityScore > 0.8 OR 
       r.similarityScore > 0.8 OR 
       r.impactScore > 0.8 OR
       r.exposureLevel = "HIGH")
RETURN source, r, target
LIMIT 60;

// ========================================
// 11. 🔥 위험 기업 클러스터
// ========================================
// 높은 리스크를 가진 기업들과 그들의 대응책
MATCH (company)-[exp:IS_EXPOSED_TO]->(risk:MacroIndicator)
WHERE exp.exposureLevel = "HIGH"
OPTIONAL MATCH (company)-[sol:IS_ELIGIBLE_FOR]->(solution)
WHERE sol.eligibilityScore > 0.7
RETURN company, exp, risk, sol, solution
LIMIT 40;

// ========================================
// 12. 💡 솔루션 허브 네트워크
// ========================================
// 많은 기업이 활용하는 인기 솔루션들
MATCH (solution)<-[r:IS_ELIGIBLE_FOR]-(company)
WHERE solution:KB_Product OR solution:Policy
WITH solution, count(company) as popularity, collect(company)[0..5] as companies
WHERE popularity > 3
UNWIND companies as company
RETURN solution, company, popularity
LIMIT 50;

// ========================================
// 13. 🎯 대한정밀 맞춤 추천 네트워크
// ========================================
// 대한정밀과 유사한 기업들이 사용하는 솔루션
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (similar:ReferenceCompany {sector: "automotive_parts"})
MATCH (similar)-[r:IS_ELIGIBLE_FOR]->(solution)
WHERE r.eligibilityScore > 0.7
RETURN u, similar, r, solution
LIMIT 30;

// ========================================
// 14. 📊 시간별 영향 네트워크
// ========================================
// 최근 뉴스가 실시간으로 미치는 영향
MATCH (recent:NewsArticle)
WHERE recent.publishDate > datetime() - duration({days: 7})
MATCH (recent)-[impact:HAS_IMPACT_ON]->(affected)
OPTIONAL MATCH (affected)-[response:IS_ELIGIBLE_FOR]->(countermeasure)
RETURN recent, impact, affected, response, countermeasure
LIMIT 35;

// ========================================
// 15. 🌟 3D 시각화용 전체 네트워크
// ========================================
// Neo4j Bloom이나 3D 도구용 데이터
MATCH (n1)-[r]-(n2)
WHERE (n1:UserCompany OR n1:ReferenceCompany OR 
       n1:KB_Product OR n1:Policy OR n1:MacroIndicator) AND
      (n2:UserCompany OR n2:ReferenceCompany OR 
       n2:KB_Product OR n2:Policy OR n2:MacroIndicator)
WITH n1, r, n2,
     CASE labels(n1)[0]
       WHEN 'UserCompany' THEN '#FF4444'
       WHEN 'ReferenceCompany' THEN '#4444FF' 
       WHEN 'KB_Product' THEN '#44FF44'
       WHEN 'Policy' THEN '#FFAA44'
       WHEN 'MacroIndicator' THEN '#AA44FF'
       ELSE '#CCCCCC'
     END as n1_color,
     CASE labels(n2)[0]
       WHEN 'UserCompany' THEN '#FF4444'
       WHEN 'ReferenceCompany' THEN '#4444FF'
       WHEN 'KB_Product' THEN '#44FF44' 
       WHEN 'Policy' THEN '#FFAA44'
       WHEN 'MacroIndicator' THEN '#AA44FF'
       ELSE '#CCCCCC'
     END as n2_color
RETURN n1, r, n2, n1_color, n2_color
LIMIT 100;

// ========================================
// 16. 🎮 인터랙티브 탐색용
// ========================================
// 클릭해서 확장 가능한 중심 노드들
MATCH (center)
WHERE (center:UserCompany AND center.companyName = "대한정밀") OR
      (center:MacroIndicator AND center.indicatorName CONTAINS "금리") OR
      (center:KB_Product AND center.productName CONTAINS "고정금리")
MATCH (center)-[r1]-(level1)
OPTIONAL MATCH (level1)-[r2]-(level2)
WHERE level2 <> center
WITH center, r1, level1, r2, level2,
     size((center)-[]->()) as out_degree,
     size((center)<-[]-()) as in_degree
RETURN center, r1, level1, r2, level2, (out_degree + in_degree) as total_degree
ORDER BY total_degree DESC
LIMIT 60;

// ========================================
// 시각화 설정 가이드:
// 
// Neo4j Browser에서 실행 후:
// 1. 좌측 하단 톱니바퀴 → 스타일 설정
// 2. 노드 색상:
//    - UserCompany: 빨간색 (#FF4444) 
//    - ReferenceCompany: 파란색 (#4444FF)
//    - KB_Product: 초록색 (#44FF44)
//    - Policy: 주황색 (#FFAA44)
//    - MacroIndicator: 보라색 (#AA44FF)
// 3. 노드 크기: revenue, eligibilityScore 기준
// 4. 관계 두께: score 값 기준
// 5. 레이아웃: Force-directed 추천
// ========================================