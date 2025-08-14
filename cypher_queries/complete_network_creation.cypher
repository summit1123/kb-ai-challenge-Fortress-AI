// ================================================
// 전체 데이터 연결관계 생성 및 시각화
// ================================================

// 0. 현재 데이터 확인
MATCH (n)
RETURN labels(n)[0] as 노드타입, count(n) as 개수
ORDER BY 개수 DESC;

// 1. 대한정밀과 모든 KB 상품 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(k)
SET el.eligibilityScore = 
    CASE 
        WHEN k.productName CONTAINS "고정금리" THEN 0.95
        WHEN k.productName CONTAINS "운전자금" THEN 0.90
        WHEN k.productName CONTAINS "스왑" THEN 0.85
        WHEN k.productName CONTAINS "대출" THEN 0.80
        WHEN k.productType = "대출" THEN 0.75
        ELSE 0.70
    END,
    el.urgency = "MEDIUM"
RETURN count(*) as KB상품_연결수;

// 2. 대한정밀과 모든 정책 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
MERGE (u)-[el:IS_ELIGIBLE_FOR]->(p)
SET el.eligibilityScore = 
    CASE 
        WHEN p.policyName CONTAINS "이차보전" THEN 0.90
        WHEN p.policyName CONTAINS "금리" THEN 0.85
        WHEN p.supportField CONTAINS "제조" THEN 0.80
        WHEN p.targetBusiness CONTAINS "중소기업" THEN 0.75
        ELSE 0.70
    END,
    el.matchingReason = "중소 제조업체 적격"
RETURN count(*) as 정책_연결수;

// 3. 모든 뉴스와 대한정밀 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (n:NewsArticle)
MERGE (n)-[i:HAS_IMPACT_ON]->(u)
SET i.impactScore = 
    CASE 
        WHEN n.title CONTAINS "금리" AND n.title CONTAINS "인상" THEN 0.90
        WHEN n.title CONTAINS "자동차" AND n.title CONTAINS "부품" THEN 0.85
        WHEN n.title CONTAINS "제조업" THEN 0.80
        WHEN n.category = "financial" THEN 0.75
        WHEN n.category = "manufacturing" THEN 0.70
        ELSE 0.60
    END,
    i.impactDirection = 
    CASE 
        WHEN n.title CONTAINS "인상" OR n.title CONTAINS "감소" THEN "NEGATIVE"
        WHEN n.title CONTAINS "지원" OR n.title CONTAINS "확대" THEN "POSITIVE"
        ELSE "NEUTRAL"
    END
RETURN count(*) as 뉴스_연결수;

// 4. 대한정밀과 모든 거시지표 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
MERGE (u)-[e:IS_EXPOSED_TO]->(m)
SET e.exposureLevel = 
    CASE 
        WHEN m.indicatorName CONTAINS "금리" THEN "HIGH"
        WHEN m.indicatorName CONTAINS "환율" THEN "MEDIUM"
        ELSE "LOW"
    END,
    e.rationale = 
    CASE 
        WHEN m.indicatorName CONTAINS "금리" THEN "변동금리 대출 80억원 보유"
        WHEN m.indicatorName CONTAINS "환율" THEN "수출 비중 20%"
        ELSE "일반적 노출"
    END
RETURN count(*) as 거시지표_연결수;

// 5. 대한정밀과 유사 기업들 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts" OR 
      r.companyName CONTAINS "자동차" OR
      r.companyName CONTAINS "부품" OR
      r.companyName IN ["현대모비스", "만도", "현대위아"]
MERGE (u)-[s:SIMILAR_TO]->(r)
SET s.similarityScore = 
    CASE 
        WHEN r.companyName = "현대모비스" THEN 0.85
        WHEN r.companyName = "만도" THEN 0.80
        WHEN r.sector = "automotive_parts" THEN 0.75
        ELSE 0.65
    END,
    s.matchingFactors = ["자동차부품업", "제조업", "중소기업"]
RETURN count(*) as 유사기업_연결수;

// 6. 연결 상태 확인
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (u)-[r1:IS_ELIGIBLE_FOR]->(kb:KB_Product)
OPTIONAL MATCH (u)-[r2:IS_ELIGIBLE_FOR]->(policy:Policy)  
OPTIONAL MATCH (news:NewsArticle)-[r3:HAS_IMPACT_ON]->(u)
OPTIONAL MATCH (u)-[r4:IS_EXPOSED_TO]->(macro:MacroIndicator)
OPTIONAL MATCH (u)-[r5:SIMILAR_TO]->(similar:ReferenceCompany)
RETURN 
    count(DISTINCT kb) as KB상품수,
    count(DISTINCT policy) as 정책수,
    count(DISTINCT news) as 뉴스수,
    count(DISTINCT macro) as 거시지표수,
    count(DISTINCT similar) as 유사기업수,
    count(DISTINCT r1) + count(DISTINCT r2) + count(DISTINCT r3) + count(DISTINCT r4) + count(DISTINCT r5) as 총연결수;

// ================================================
// 시각화 쿼리들
// ================================================

// 7. 전체 연결 확인 (기본)
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (u)-[r]-(connected)
RETURN u, r, connected;

// 8. 카테고리별 분리 시각화
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[kb_rel:IS_ELIGIBLE_FOR]->(kb:KB_Product)
OPTIONAL MATCH (center)-[policy_rel:IS_ELIGIBLE_FOR]->(policy:Policy)
OPTIONAL MATCH (news:NewsArticle)-[news_rel:HAS_IMPACT_ON]->(center)
OPTIONAL MATCH (center)-[macro_rel:IS_EXPOSED_TO]->(macro:MacroIndicator)
OPTIONAL MATCH (center)-[sim_rel:SIMILAR_TO]->(similar:ReferenceCompany)
RETURN center, 
       kb_rel, kb, 
       policy_rel, policy,
       news_rel, news,
       macro_rel, macro,
       sim_rel, similar;

// 9. 스코어 기반 필터링 시각화 (중요한 연결만)
MATCH (center:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (center)-[r1:IS_ELIGIBLE_FOR]->(solution)
WHERE r1.eligibilityScore > 0.8
OPTIONAL MATCH (news:NewsArticle)-[r2:HAS_IMPACT_ON]->(center)
WHERE r2.impactScore > 0.8
OPTIONAL MATCH (center)-[r3:IS_EXPOSED_TO]->(risk:MacroIndicator)
WHERE r3.exposureLevel = "HIGH"
OPTIONAL MATCH (center)-[r4:SIMILAR_TO]->(similar:ReferenceCompany)
WHERE r4.similarityScore > 0.75
RETURN center, r1, solution, r2, news, r3, risk, r4, similar;

// 10. 2단계 확장 네트워크
MATCH (center:UserCompany {companyName: "대한정밀"})
MATCH (center)-[r1]-(level1)
OPTIONAL MATCH (level1)-[r2]-(level2)
WHERE level2 <> center 
WITH center, r1, level1, r2, level2
LIMIT 100
RETURN center, r1, level1, r2, level2;

// 11. 색상 구분 전체 네트워크
MATCH (center:UserCompany {companyName: "대한정밀"})
MATCH (center)-[relation]-(connected)
RETURN center, relation, connected,
       labels(connected)[0] as node_type,
       CASE labels(connected)[0]
           WHEN 'KB_Product' THEN '#00FF00'      // 초록색
           WHEN 'Policy' THEN '#FF8C00'          // 주황색  
           WHEN 'NewsArticle' THEN '#8A2BE2'     // 보라색
           WHEN 'MacroIndicator' THEN '#FFD700'  // 금색
           WHEN 'ReferenceCompany' THEN '#1E90FF' // 파란색
           ELSE '#808080'                        // 회색
       END as color;

// 12. 관계 타입별 카운트
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (u)-[r]-(connected)
RETURN type(r) as 관계타입, 
       labels(connected)[0] as 연결노드타입, 
       count(*) as 개수
ORDER BY 개수 DESC;