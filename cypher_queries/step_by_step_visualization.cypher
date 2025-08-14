// ================================================
// 단계별 그래프 시각화 생성 및 확인
// ================================================

// 1단계: KB 상품과 연결 + 즉시 시각화
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(k)
SET el.eligibilityScore = 
    CASE 
        WHEN k.productName CONTAINS "고정금리" THEN 0.95
        WHEN k.productName CONTAINS "운전자금" THEN 0.90
        WHEN k.productName CONTAINS "스왑" THEN 0.85
        ELSE 0.80
    END
WITH u, count(k) as kb_count
// 1단계 시각화: 대한정밀 + KB상품들
MATCH (u)-[r:IS_ELIGIBLE_FOR]->(kb:KB_Product)
RETURN u, r, kb;

// 2단계: 정책과 연결 + 시각화 (KB상품 + 정책)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(p)
SET el.eligibilityScore = 
    CASE 
        WHEN p.policyName CONTAINS "이차보전" THEN 0.90
        WHEN p.policyName CONTAINS "금리" THEN 0.85
        WHEN p.supportField CONTAINS "제조" THEN 0.80
        ELSE 0.75
    END
WITH u, count(p) as policy_count
// 2단계 시각화: 대한정밀 + KB상품 + 정책
MATCH (u)-[r:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product OR solution:Policy
RETURN u, r, solution;

// 3단계: 뉴스와 연결 + 시각화 (KB상품 + 정책 + 뉴스)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (n:NewsArticle)
MERGE (n)-[i:HAS_IMPACT_ON]->(u)
SET i.impactScore = 
    CASE 
        WHEN n.title CONTAINS "금리" THEN 0.85
        WHEN n.title CONTAINS "자동차" THEN 0.80
        WHEN n.category = "financial" THEN 0.75
        ELSE 0.70
    END
WITH u, count(n) as news_count
// 3단계 시각화: 대한정밀 + KB상품 + 정책 + 뉴스
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[r1:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (news:NewsArticle)-[r2:HAS_IMPACT_ON]->(center)
RETURN center, r1, solution, r2, news;

// 4단계: 거시지표와 연결 + 시각화 (KB상품 + 정책 + 뉴스 + 거시지표)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
MERGE (u)-[e:IS_EXPOSED_TO]->(m)
SET e.exposureLevel = 
    CASE 
        WHEN m.indicatorName CONTAINS "금리" THEN "HIGH"
        WHEN m.indicatorName CONTAINS "환율" THEN "MEDIUM"
        ELSE "LOW"
    END
WITH u, count(m) as macro_count
// 4단계 시각화: 대한정밀 + KB상품 + 정책 + 뉴스 + 거시지표
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[r1:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (news:NewsArticle)-[r2:HAS_IMPACT_ON]->(center)
OPTIONAL MATCH (center)-[r3:IS_EXPOSED_TO]->(macro:MacroIndicator)
RETURN center, r1, solution, r2, news, r3, macro;

// 5단계: 유사기업과 연결 + 최종 전체 시각화
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts"
MERGE (u)-[s:SIMILAR_TO]->(r)
SET s.similarityScore = 
    CASE 
        WHEN r.companyName = "현대모비스" THEN 0.85
        WHEN r.companyName = "만도" THEN 0.80
        ELSE 0.75
    END
WITH u, count(r) as similar_count
// 최종 전체 시각화: 모든 연결
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[r1:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (news:NewsArticle)-[r2:HAS_IMPACT_ON]->(center)
OPTIONAL MATCH (center)-[r3:IS_EXPOSED_TO]->(macro:MacroIndicator)
OPTIONAL MATCH (center)-[r4:SIMILAR_TO]->(similar:ReferenceCompany)
RETURN center, r1, solution, r2, news, r3, macro, r4, similar;