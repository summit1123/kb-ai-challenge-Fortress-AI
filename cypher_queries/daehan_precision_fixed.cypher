// ================================================
// 대한정밀 분석 쿼리 (Neo4j 문법 수정)
// 백틱(`)으로 특수문자 포함 컬럼명 처리
// ================================================

// ========================================
// 1. ✅ 대한정밀 기본 정보 확인 (정상 작동)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
RETURN 
  u.companyName as 기업명,
  u.industryDescription as 업종,
  u.revenue as 연매출,
  u.employeeCount as 직원수,
  u.debtAmount as 총부채,
  u.variableRateDebt as 변동금리부채,
  u.location as 위치,
  u.nodeId as ID;

// ========================================
// 2. 💰 금리 변동 영향 분석 (수정됨)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
WITH u, u.variableRateDebt as 변동금리부채
RETURN 
  u.companyName as 기업명,
  변동금리부채 as 변동금리대출,
  변동금리부채 * 0.048 / 12 as 현재_월이자부담,
  변동금리부채 * 0.0505 / 12 as `금리0.25%인상시_월이자`,
  변동금리부채 * 0.053 / 12 as `금리0.5%인상시_월이자`,
  변동금리부채 * 0.058 / 12 as `금리1%인상시_월이자`,
  (변동금리부채 * 0.053 / 12) - (변동금리부채 * 0.048 / 12) as `0.5%인상시_월추가부담`,
  ((변동금리부채 * 0.053 / 12) - (변동금리부채 * 0.048 / 12)) * 12 as `0.5%인상시_연간추가부담`;

// ========================================
// 3. ✅ 유사 기업 비교 (정상 작동)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (r:ReferenceCompany)
WHERE r.sector = "automotive_parts" OR 
      r.companyName IN ["현대모비스", "만도", "화신", "평화정공"]
OPTIONAL MATCH (r)-[exp:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
OPTIONAL MATCH (r)-[el:IS_ELIGIBLE_FOR]->(sol)
WHERE sol:KB_Product OR sol:Policy
RETURN 
  r.companyName as 유사기업,
  r.revenue as 매출규모,
  r.variableRateExposure as 변동금리노출도,
  exp.exposureLevel as 금리리스크수준,
  count(DISTINCT sol) as 활용중인_솔루션수
ORDER BY r.revenue DESC;

// ========================================
// 4. 💡 KB 금융상품 추천
// ========================================
MATCH (k:KB_Product)
WHERE k.productType IN ["대출", "운전자금", "금리헤지"] OR
      k.productName CONTAINS "고정금리" OR 
      k.productName CONTAINS "금리" OR
      k.productName CONTAINS "스왑"
RETURN 
  k.productName as KB상품명,
  k.productType as 상품유형,
  k.interestType as 금리유형,
  CASE 
    WHEN k.productName CONTAINS "고정금리" THEN "⭐⭐⭐⭐⭐"
    WHEN k.productName CONTAINS "스왑" THEN "⭐⭐⭐⭐"
    WHEN k.productName CONTAINS "운전자금" THEN "⭐⭐⭐"
    ELSE "⭐⭐"
  END as 추천도,
  CASE 
    WHEN k.productName CONTAINS "고정금리" THEN "변동금리 100% 노출 기업 필수"
    WHEN k.productName CONTAINS "스왑" THEN "금리 상승 리스크 헤지"
    ELSE "운전자금 확보"
  END as 추천이유
ORDER BY 추천도 DESC;

// ========================================
// 5. 📊 경영진 보고서 (수정됨)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
WITH u,
     u.variableRateDebt as 변동금리부채,
     u.revenue as 연매출
RETURN 
  "대한정밀 금리 리스크 분석 보고서" as 제목,
  변동금리부채 as 변동금리_노출액,
  변동금리부채 * 1.0 / 연매출 as 부채_매출_비율,
  변동금리부채 * 0.048 as 현재_연간이자,
  변동금리부채 * 0.053 as `0.5%인상시_연간이자`,
  변동금리부채 * 0.005 as `0.5%인상시_추가부담`,
  "1. 즉시 KB 고정금리 대환대출 전환 (80억원)" as 액션1,
  "2. 정부 제조업 이차보전 프로그램 신청" as 액션2,
  "3. 금리스왑으로 나머지 리스크 헤지" as 액션3;

// ========================================
// 6. 🎯 대한정밀-솔루션 매칭 생성
// ========================================
// KB 상품과 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (k:KB_Product)
WHERE k.productName CONTAINS "고정금리" OR 
      k.productName CONTAINS "금리스왑" OR
      k.productName CONTAINS "운전자금"
WITH u, k LIMIT 5
MERGE (u)-[r1:IS_ELIGIBLE_FOR]->(k)
SET r1.eligibilityScore = 
      CASE 
        WHEN k.productName CONTAINS "고정금리" THEN 0.95
        WHEN k.productName CONTAINS "금리스왑" THEN 0.90
        ELSE 0.80
      END,
    r1.urgency = "CRITICAL",
    r1.expectedBenefit = "월 800만원 이자 절감 가능"
RETURN k.productName as 매칭된_KB상품, r1.eligibilityScore as 적합도;

// ========================================
// 7. 📋 정책 매칭 생성
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (p:Policy)
WHERE p.supportField CONTAINS "제조" OR 
      p.targetBusiness CONTAINS "중소기업"
WITH u, p LIMIT 10
MERGE (u)-[r2:IS_ELIGIBLE_FOR]->(p)
SET r2.eligibilityScore = 0.85,
    r2.actionRequired = "즉시 신청"
RETURN p.policyName as 매칭된_정책, r2.eligibilityScore as 적합도;

// ========================================
// 8. 🔄 실시간 모니터링 (수정됨)
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
OPTIONAL MATCH (recent:NewsArticle)
WHERE recent.publishDate > datetime() - duration({days: 1}) AND
      (recent.title CONTAINS "금리" OR recent.title CONTAINS "자동차")
WITH u, m, count(recent) as 최근뉴스수
RETURN 
  u.companyName as 기업명,
  datetime() as 조회시간,
  m.indicatorName as 주요지표,
  m.value as 현재값,
  m.changeRate as 변동률,
  CASE 
    WHEN m.changeRate > 0 THEN "⚠️ 위험" 
    ELSE "✅ 안정" 
  END as 상태,
  최근뉴스수 as `24시간내_관련뉴스`,
  u.variableRateDebt * (coalesce(m.changeRate, 0) / 100) / 12 as 월영향액;

// ========================================
// 9. 🌟 대한정밀 종합 분석 뷰
// ========================================
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH (u)-[r1:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (u)-[r2:SIMILAR_TO]->(similar:ReferenceCompany)
OPTIONAL MATCH (u)-[r3:IS_EXPOSED_TO]->(risk:MacroIndicator)
RETURN 
  u.companyName as 기업명,
  count(DISTINCT solution) as 추천솔루션수,
  count(DISTINCT similar) as 유사기업수,
  count(DISTINCT risk) as 리스크요인수,
  collect(DISTINCT solution.productName)[0..3] as TOP3_KB상품,
  collect(DISTINCT solution.policyName)[0..3] as TOP3_정책;

// ========================================
// 10. 📊 시각화용 네트워크 그래프
// ========================================
// 대한정밀 중심의 전체 관계망
MATCH (u:UserCompany {companyName: "대한정밀"})
OPTIONAL MATCH path1 = (u)-[:IS_ELIGIBLE_FOR]->(sol)
WHERE sol:KB_Product OR sol:Policy
OPTIONAL MATCH path2 = (u)-[:SIMILAR_TO]->(sim:ReferenceCompany)
OPTIONAL MATCH path3 = (u)-[:IS_EXPOSED_TO]->(risk:MacroIndicator)
OPTIONAL MATCH path4 = (news:NewsArticle)-[:HAS_IMPACT_ON]->(u)
RETURN path1, path2, path3, path4
LIMIT 50;