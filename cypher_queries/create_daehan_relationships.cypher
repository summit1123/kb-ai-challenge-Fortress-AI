// ================================================
// 대한정밀 관계 생성 후 시각화
// ================================================

// 1. 먼저 대한정밀과 유사 기업 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts" OR 
      r.companyName IN ["현대모비스", "만도", "현대위아"]
WITH u, r,
     CASE 
        WHEN r.companyName = "현대모비스" THEN 0.75
        WHEN r.companyName = "만도" THEN 0.80
        WHEN r.companyName = "현대위아" THEN 0.70
        WHEN r.sector = "automotive_parts" THEN 0.65
        ELSE 0.5
     END as similarity
WHERE similarity > 0.6
MERGE (u)-[s:SIMILAR_TO]->(r)
SET s.similarityScore = similarity,
    s.matchingFactors = ["automotive_parts", "manufacturing"]
RETURN u.companyName, r.companyName, s.similarityScore;

// 2. 대한정밀과 금리 리스크 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
MERGE (u)-[e:IS_EXPOSED_TO]->(m)
SET e.exposureLevel = "HIGH",
    e.rationale = "변동금리 대출 80억원 보유",
    e.riskType = "interest_rate"
RETURN u.companyName, m.indicatorName, e.exposureLevel;

// 3. 대한정밀과 KB 상품 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
WHERE k.productName CONTAINS "고정금리" OR 
      k.productName CONTAINS "금리스왑" OR 
      k.productName CONTAINS "운전자금"
WITH u, k,
     CASE 
        WHEN k.productName CONTAINS "고정금리" THEN 0.95
        WHEN k.productName CONTAINS "금리스왑" THEN 0.90
        WHEN k.productName CONTAINS "운전자금" THEN 0.80
        ELSE 0.70
     END as eligibility
WHERE eligibility > 0.75
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(k)
SET el.eligibilityScore = eligibility,
    el.urgency = "HIGH",
    el.expectedBenefit = "월 이자 절감"
RETURN u.companyName, k.productName, el.eligibilityScore;

// 4. 대한정밀과 정책 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
WHERE p.supportField CONTAINS "제조" OR 
      p.targetBusiness CONTAINS "중소기업" OR
      p.policyName CONTAINS "이차보전" OR
      p.policyName CONTAINS "금리"
WITH u, p LIMIT 10
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(p)
SET el.eligibilityScore = 0.85,
    el.actionRequired = "신청 검토"
RETURN u.companyName, p.policyName, el.eligibilityScore;

// 5. 확인: 대한정밀의 모든 관계
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (u)-[r]-(connected)
RETURN type(r) as 관계타입, count(*) as 개수;

// 6. 이제 시각화 가능한 쿼리
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (u)-[r]-(connected)
RETURN u, r, connected;