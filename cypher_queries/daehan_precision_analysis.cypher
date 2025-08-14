// ================================================
// 대한정밀 맞춤형 분석 쿼리 모음
// 금리 민감 자동차부품 제조업체를 위한 실시간 분석
// ================================================

// ========================================
// 1. 🚨 대한정밀 현재 상태 대시보드
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (u)-[exp:IS_EXPOSED_TO]->(m:MacroIndicator)
OPTIONAL MATCH (u)-[sim:SIMILAR_TO]->(r:ReferenceCompany)
OPTIONAL MATCH (u)-[el:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:Policy OR solution:KB_Product
RETURN 
  u.companyName as 기업명,
  u.variableRateDebt as 변동금리부채,
  u.revenue as 연매출,
  collect(DISTINCT {
    지표: m.indicatorName, 
    현재값: m.value,
    노출도: exp.exposureLevel
  }) as 리스크노출,
  collect(DISTINCT {
    유사기업: r.companyName,
    유사도: sim.similarityScore
  }) as 유사기업,
  collect(DISTINCT {
    솔루션: coalesce(solution.policyName, solution.productName),
    타입: labels(solution)[0],
    적합도: el.eligibilityScore
  }) as 추천솔루션;

// ========================================
// 2. 💸 금리 변동 시뮬레이션 (대한정밀 특화)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
WITH u, m, u.variableRateDebt as 부채금액
RETURN 
  u.companyName as 기업명,
  부채금액 as 변동금리부채,
  m.value as 현재기준금리,
  부채금액 * 0.04 / 12 as 현재_월이자,
  부채금액 * 0.0425 / 12 as "0.25%인상시_월이자",
  부채금액 * 0.045 / 12 as "0.5%인상시_월이자",
  부채금액 * 0.0475 / 12 as "0.75%인상시_월이자",
  부채금액 * 0.05 / 12 as "1%인상시_월이자",
  (부채금액 * 0.045 / 12) - (부채금액 * 0.04 / 12) as "0.5%인상시_월추가부담";

// ========================================
// 3. 🎯 유사 기업 벤치마킹 (자동차부품업체)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts" OR r.companyName CONTAINS "모비스" OR r.companyName CONTAINS "만도"
OPTIONAL MATCH (r)-[re:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
OPTIONAL MATCH (r)-[el:IS_ELIGIBLE_FOR]->(k:KB_Product)
WHERE k.productName CONTAINS "금리"
RETURN 
  r.companyName as 벤치마킹기업,
  r.revenue as 매출규모,
  r.debtRatio as 부채비율,
  re.exposureLevel as 금리리스크노출도,
  collect(DISTINCT k.productName) as 활용중인_KB상품
ORDER BY r.revenue DESC;

// ========================================
// 4. 💡 긴급 추천 솔루션 (금리 헤지 중심)
// ========================================
// KB 금리 헤지 상품 매칭
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
WHERE k.productName CONTAINS "금리" OR 
      k.productName CONTAINS "스왑" OR 
      k.productName CONTAINS "고정"
WITH u, k
MERGE (u)-[r:IS_ELIGIBLE_FOR]->(k)
SET r.eligibilityScore = CASE 
    WHEN k.productName CONTAINS "스왑" THEN 0.95
    WHEN k.productName CONTAINS "고정금리" THEN 0.9
    ELSE 0.7
  END,
  r.urgency = "HIGH",
  r.recommendationReason = "변동금리 100% 노출로 긴급 헤지 필요"
RETURN 
  k.productName as 추천상품,
  k.productType as 상품유형,
  r.eligibilityScore as 적합도,
  k.description as 상품설명
ORDER BY r.eligibilityScore DESC;

// ========================================
// 5. 📋 정부 지원정책 매칭 (제조업 + 금리지원)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
WHERE (p.supportField CONTAINS "제조" OR 
       p.targetBusiness CONTAINS "자동차" OR
       p.eligibilityText CONTAINS "금리") AND
      (p.policyName CONTAINS "금리" OR 
       p.policyName CONTAINS "이차" OR 
       p.policyName CONTAINS "대출")
WITH u, p
MERGE (u)-[r:IS_ELIGIBLE_FOR]->(p)
SET r.eligibilityScore = 0.85,
    r.matchingConditions = ["제조업", "중소기업", "금리부담"],
    r.actionRequired = "신청기한 확인 필요"
RETURN 
  p.policyName as 정책명,
  p.issuingOrg as 주관기관,
  p.supportField as 지원분야,
  r.eligibilityScore as 적합도
ORDER BY r.eligibilityScore DESC
LIMIT 10;

// ========================================
// 6. 📰 관련 뉴스 영향도 분석
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (n:NewsArticle)
WHERE n.title CONTAINS "금리" OR 
      n.title CONTAINS "자동차" OR 
      n.title CONTAINS "부품"
WITH u, n
ORDER BY n.publishDate DESC
LIMIT 10
MERGE (n)-[r:HAS_IMPACT_ON]->(u)
SET r.impactScore = CASE
    WHEN n.title CONTAINS "금리" AND n.title CONTAINS "인상" THEN 0.9
    WHEN n.title CONTAINS "자동차" AND n.title CONTAINS "감소" THEN 0.8
    ELSE 0.5
  END,
  r.impactDirection = CASE
    WHEN n.title CONTAINS "인상" THEN "NEGATIVE"
    WHEN n.title CONTAINS "감소" THEN "NEGATIVE"
    ELSE "NEUTRAL"
  END
RETURN 
  n.title as 뉴스제목,
  n.publishDate as 발행일,
  r.impactScore as 영향도,
  r.impactDirection as 영향방향
ORDER BY r.impactScore DESC;

// ========================================
// 7. 🔄 실시간 알림용 모니터링 쿼리
// ========================================
// 금리 변동 감지 시 즉시 실행
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리" AND 
      m.lastUpdated > datetime() - duration({days: 1})
MATCH (u)-[:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product AND solution.productName CONTAINS "금리"
RETURN 
  "🚨 긴급 알림" as 알림타입,
  m.indicatorName as 변동지표,
  m.changeRate as 변동률,
  u.variableRateDebt * (m.changeRate / 100) / 12 as 월_추가부담,
  collect(solution.productName)[0..3] as 즉시활용가능_상품;

// ========================================
// 8. 📊 경영진 보고용 종합 분석
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
// 리스크 집계
OPTIONAL MATCH (u)-[exp:IS_EXPOSED_TO]->(risk:MacroIndicator)
WITH u, 
     count(DISTINCT risk) as 총리스크수,
     sum(CASE WHEN exp.exposureLevel = "HIGH" THEN 1 ELSE 0 END) as 고위험리스크수
// 솔루션 집계
OPTIONAL MATCH (u)-[el:IS_ELIGIBLE_FOR]->(solution)
WHERE el.eligibilityScore > 0.7
WITH u, 총리스크수, 고위험리스크수,
     count(DISTINCT CASE WHEN solution:KB_Product THEN solution END) as KB상품수,
     count(DISTINCT CASE WHEN solution:Policy THEN solution END) as 정책지원수
// 예상 손실/이익
RETURN 
  u.companyName as 기업명,
  "금리 민감 제조업" as 리스크프로필,
  총리스크수,
  고위험리스크수,
  KB상품수 + 정책지원수 as 활용가능_솔루션수,
  u.variableRateDebt * 0.005 / 12 as "금리0.5%인상시_월추가비용",
  u.variableRateDebt * 0.005 as "금리0.5%인상시_연간추가비용",
  "즉시 고정금리 전환 검토 필요" as 핵심제언;

// ========================================
// 9. 🎨 시각화용 네트워크 (대한정밀 중심)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH path1 = (u)-[:SIMILAR_TO]->(similar:ReferenceCompany)
OPTIONAL MATCH path2 = (u)-[:IS_EXPOSED_TO]->(risk:MacroIndicator)
OPTIONAL MATCH path3 = (u)-[:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product OR solution:Policy
OPTIONAL MATCH path4 = (news:NewsArticle)-[:HAS_IMPACT_ON]->(u)
WHERE news.publishDate > datetime() - duration({days: 7})
RETURN path1, path2, path3, path4;

// ========================================
// 10. 💬 챗봇 대화용 간단 조회
// ========================================
// "우리 회사 지금 상황 어때?"
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (u)-[:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
OPTIONAL MATCH (u)-[:IS_ELIGIBLE_FOR]->(k:KB_Product)
WHERE k.productName CONTAINS "금리" OR k.productName CONTAINS "고정"
WITH u, m, collect(k.productName)[0..3] as 추천상품
RETURN 
  u.companyName + "님의 현재 상황:" as 제목,
  "변동금리 " + toString(u.variableRateDebt/100000000) + "억원 보유" as 현황,
  "기준금리 " + toString(m.value) + "% (전월비 " + toString(m.changeRate) + "%p)" as 금리동향,
  CASE 
    WHEN m.changeRate > 0 THEN "⚠️ 금리 상승 중! 고정금리 전환 시급"
    ELSE "📊 금리 안정세, 전환 시점 검토 필요"
  END as 액션필요,
  추천상품 as 추천KB상품;