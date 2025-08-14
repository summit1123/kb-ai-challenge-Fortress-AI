// ================================================
// 깔끔한 시각화용 쿼리 (주석 제거)
// ================================================

// 1. 대한정밀 중심 네트워크
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH path1 = (u)-[r1]-(connected1)
OPTIONAL MATCH path2 = (connected1)-[r2]-(connected2)
WHERE connected2 <> u
RETURN path1, path2
LIMIT 50;

// 2. 금리 리스크 전파 네트워크
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
MATCH path = (m)<-[:IS_EXPOSED_TO]-(company)
OPTIONAL MATCH extension = (company)-[:IS_ELIGIBLE_FOR]->(solution)
RETURN path, extension
LIMIT 30;

// 3. 고가치 연결 네트워크
MATCH (source)-[r]-(target)
WHERE r.eligibilityScore > 0.8 OR 
      r.similarityScore > 0.8 OR 
      r.impactScore > 0.8 OR
      r.exposureLevel = "HIGH"
RETURN source, r, target
LIMIT 60;

// 4. 자동차부품 업종 클러스터
MATCH (c1:ReferenceCompany {sector: "automotive_parts"})
MATCH (c2:ReferenceCompany {sector: "automotive_parts"})
WHERE c1 <> c2
OPTIONAL MATCH path = (c1)-[*1..2]-(c2)
RETURN path
LIMIT 40;

// 5. KB 상품 추천 네트워크
MATCH (k:KB_Product)
MATCH (company)-[r:IS_ELIGIBLE_FOR]->(k)
WHERE r.eligibilityScore > 0.7
RETURN k, r, company
LIMIT 50;

// 6. 정책 활용 네트워크
MATCH (p:Policy)
MATCH (company)-[r:IS_ELIGIBLE_FOR]->(p)
WHERE company:ReferenceCompany OR company:UserCompany
WITH p, count(company) as usage_count
WHERE usage_count > 2
MATCH (p)<-[r:IS_ELIGIBLE_FOR]-(company)
RETURN p, r, company
LIMIT 60;

// 7. 뉴스 영향 네트워크
MATCH (n:NewsArticle)
WHERE n.publishDate > datetime() - duration({days: 30})
MATCH (n)-[r:HAS_IMPACT_ON]->(target)
RETURN n, r, target
LIMIT 40;

// 8. 위험 기업 클러스터
MATCH (company)-[exp:IS_EXPOSED_TO]->(risk:MacroIndicator)
WHERE exp.exposureLevel = "HIGH"
OPTIONAL MATCH (company)-[sol:IS_ELIGIBLE_FOR]->(solution)
WHERE sol.eligibilityScore > 0.7
RETURN company, exp, risk, sol, solution
LIMIT 40;

// 9. 대한정밀 맞춤 추천 네트워크
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (similar:ReferenceCompany {sector: "automotive_parts"})
MATCH (similar)-[r:IS_ELIGIBLE_FOR]->(solution)
WHERE r.eligibilityScore > 0.7
RETURN u, similar, r, solution
LIMIT 30;

// 10. 최근 뉴스 영향 네트워크
MATCH (recent:NewsArticle)
WHERE recent.publishDate > datetime() - duration({days: 7})
MATCH (recent)-[impact:HAS_IMPACT_ON]->(affected)
OPTIONAL MATCH (affected)-[response:IS_ELIGIBLE_FOR]->(countermeasure)
RETURN recent, impact, affected, response, countermeasure
LIMIT 35;