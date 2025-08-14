// ================================================
// 대한정밀 중심 방사형(Star) 네트워크 생성
// ================================================

// 1. 대한정밀과 유사 기업들 연결 (자동차부품업체)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts"
WITH u, r, 
     CASE r.companyName
        WHEN "현대모비스" THEN 0.85
        WHEN "만도" THEN 0.80
        WHEN "현대위아" THEN 0.75
        ELSE 0.70
     END as similarity
MERGE (u)-[s:SIMILAR_TO]->(r)
SET s.similarityScore = similarity
RETURN "유사기업 연결 완료" as 단계1;

// 2. 대한정밀과 거시지표 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
MERGE (u)-[e:IS_EXPOSED_TO]->(m)
SET e.exposureLevel = 
    CASE 
        WHEN m.indicatorName CONTAINS "금리" THEN "HIGH"
        WHEN m.indicatorName CONTAINS "환율" THEN "MEDIUM"
        ELSE "LOW"
    END
RETURN "거시지표 연결 완료" as 단계2;

// 3. 대한정밀과 KB 상품들 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
WITH u, k, 
     CASE 
        WHEN k.productName CONTAINS "고정금리" THEN 0.95
        WHEN k.productName CONTAINS "운전자금" THEN 0.85
        WHEN k.productName CONTAINS "스왑" THEN 0.90
        WHEN k.productType = "대출" THEN 0.80
        ELSE 0.70
     END as score
WHERE score >= 0.70
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(k)
SET el.eligibilityScore = score
RETURN "KB상품 연결 완료" as 단계3;

// 4. 대한정밀과 정책들 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
WHERE p.supportField CONTAINS "제조" OR 
      p.targetBusiness CONTAINS "중소기업" OR
      p.policyName CONTAINS "금리" OR
      p.policyName CONTAINS "이차보전"
WITH u, p
LIMIT 15
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(p)
SET el.eligibilityScore = 0.80
RETURN "정책 연결 완료" as 단계4;

// 5. 뉴스와 대한정밀 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (n:NewsArticle)
WHERE n.category IN ["financial", "manufacturing"] OR
      n.title CONTAINS "금리" OR
      n.title CONTAINS "자동차"
WITH u, n
LIMIT 10
MERGE (n)-[i:HAS_IMPACT_ON]->(u)
SET i.impactScore = 0.6,
    i.impactDirection = "NEGATIVE"
RETURN "뉴스 연결 완료" as 단계5;

// ================================================
// 시각화 쿼리들
// ================================================

// 6. 대한정밀 중심 1단계 연결 (가장 기본)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (u)-[r]-(connected)
RETURN u, r, connected;

// 7. 대한정밀 중심 방사형 네트워크 (노드별 색상 구분)
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[r1:SIMILAR_TO]->(similar:ReferenceCompany)
OPTIONAL MATCH (center)-[r2:IS_EXPOSED_TO]->(risk:MacroIndicator)
OPTIONAL MATCH (center)-[r3:IS_ELIGIBLE_FOR]->(kb:KB_Product)
OPTIONAL MATCH (center)-[r4:IS_ELIGIBLE_FOR]->(policy:Policy)
OPTIONAL MATCH (news:NewsArticle)-[r5:HAS_IMPACT_ON]->(center)
RETURN center, r1, similar, r2, risk, r3, kb, r4, policy, r5, news;

// 8. 대한정밀 중심 확장형 (2단계 연결까지)
MATCH (center:UserCompany {companyName: "대한정밀"})
MATCH (center)-[r1]-(level1)
OPTIONAL MATCH (level1)-[r2]-(level2)
WHERE level2 <> center AND NOT level2:UserCompany
WITH center, r1, level1, r2, level2
LIMIT 50
RETURN center, r1, level1, r2, level2;

// 9. 카테고리별 연결 확인
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (u)-[:SIMILAR_TO]->(similar:ReferenceCompany)
OPTIONAL MATCH (u)-[:IS_EXPOSED_TO]->(risk:MacroIndicator)
OPTIONAL MATCH (u)-[:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (news)-[:HAS_IMPACT_ON]->(u)
RETURN 
    count(DISTINCT similar) as 유사기업수,
    count(DISTINCT risk) as 리스크수,
    count(DISTINCT solution) as 솔루션수,
    count(DISTINCT news) as 관련뉴스수;

// 10. 최종 시각화 (깔끔한 버전)
MATCH (center:UserCompany {companyName: "대한정밀"})
MATCH (center)-[relation]-(connected)
WITH center, relation, connected,
     CASE labels(connected)[0]
        WHEN 'ReferenceCompany' THEN '#4A90E2'
        WHEN 'MacroIndicator' THEN '#F5A623' 
        WHEN 'KB_Product' THEN '#50E3C2'
        WHEN 'Policy' THEN '#B8E986'
        WHEN 'NewsArticle' THEN '#BD10E0'
        ELSE '#9013FE'
     END as node_color
RETURN center, relation, connected, node_color;