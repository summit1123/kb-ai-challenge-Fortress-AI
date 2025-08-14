// ================================================
// 대한정밀 실전 분석 쿼리
// 금리 민감 자동차부품 제조업체 페르소나
// ================================================

// ========================================
// 1. 🏢 대한정밀 기본 정보 확인
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
// 2. 💰 금리 변동 영향 분석 (핵심!)
// ========================================
// 현재 금리 상황과 대한정밀의 이자 부담 계산
MATCH (u:UserCompany {companyName: "대한정밀"})
WITH u, u.variableRateDebt as 변동금리부채
RETURN 
  u.companyName as 기업명,
  변동금리부채 as 변동금리대출,
  변동금리부채 * 0.048 / 12 as 현재_월이자부담,
  변동금리부채 * 0.0505 / 12 as "금리0.25%인상시_월이자",
  변동금리부채 * 0.053 / 12 as "금리0.5%인상시_월이자",
  변동금리부채 * 0.058 / 12 as "금리1%인상시_월이자",
  (변동금리부채 * 0.053 / 12) - (변동금리부채 * 0.048 / 12) as "0.5%인상시_월추가부담",
  ((변동금리부채 * 0.053 / 12) - (변동금리부채 * 0.048 / 12)) * 12 as "0.5%인상시_연간추가부담";

// ========================================
// 3. 🔍 유사 기업과 비교 분석
// ========================================
// 자동차부품 제조업체들의 대응 전략 벤치마킹
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
// 4. 🚨 즉시 활용 가능한 KB 금융상품
// ========================================
// 대한정밀의 상황에 맞는 KB 상품 추천
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
// 5. 📋 정부 지원사업 매칭
// ========================================
// 제조업 + 자동차부품 + 금리지원 정책
MATCH (p:Policy)
WHERE (p.supportField CONTAINS "제조" OR 
       p.targetBusiness CONTAINS "중소기업" OR
       p.eligibilityText CONTAINS "자동차") AND
      (p.policyName CONTAINS "이차보전" OR 
       p.policyName CONTAINS "금리" OR 
       p.policyName CONTAINS "대출" OR
       p.supportField CONTAINS "자금")
RETURN 
  p.policyName as 정책명,
  p.issuingOrg as 주관기관,
  p.supportField as 지원분야,
  CASE
    WHEN p.policyName CONTAINS "이차보전" THEN "최우선"
    WHEN p.policyName CONTAINS "금리" THEN "우선"
    ELSE "검토"
  END as 우선순위
ORDER BY 우선순위
LIMIT 15;

// ========================================
// 6. 📰 최근 영향 뉴스 분석
// ========================================
// 금리, 자동차산업 관련 뉴스의 영향
MATCH (n:NewsArticle)
WHERE n.publishDate > date() - duration({days: 30}) AND
      (n.title CONTAINS "금리" OR 
       n.title CONTAINS "자동차" OR 
       n.title CONTAINS "부품" OR
       n.category IN ["financial", "manufacturing"])
RETURN 
  n.title as 뉴스제목,
  n.publisher as 언론사,
  n.publishDate as 날짜,
  CASE
    WHEN n.title CONTAINS "금리" AND n.title CONTAINS "인상" THEN "🔴 부정적"
    WHEN n.title CONTAINS "자동차" AND n.title CONTAINS "감소" THEN "🔴 부정적"
    WHEN n.title CONTAINS "지원" THEN "🟢 긍정적"
    ELSE "🟡 중립"
  END as 영향,
  CASE
    WHEN n.title CONTAINS "금리" AND n.title CONTAINS "인상" THEN "이자부담 증가 예상"
    WHEN n.title CONTAINS "자동차" AND n.title CONTAINS "감소" THEN "매출 감소 우려"
    WHEN n.title CONTAINS "지원" THEN "정책 활용 기회"
    ELSE "모니터링 필요"
  END as 시사점
ORDER BY n.publishDate DESC
LIMIT 10;

// ========================================
// 7. 💡 대한정밀 맞춤 액션플랜
// ========================================
// UserCompany와 솔루션 연결
MATCH (u:UserCompany {companyName: "대한정밀"})
// KB 상품 연결
MATCH (k:KB_Product)
WHERE k.productName CONTAINS "고정금리" OR k.productName CONTAINS "금리스왑"
MERGE (u)-[r1:IS_ELIGIBLE_FOR]->(k)
SET r1.eligibilityScore = 0.95,
    r1.urgency = "CRITICAL",
    r1.expectedBenefit = "월 800만원 이자 절감 가능"
// 정책 연결
WITH u
MATCH (p:Policy)
WHERE p.policyName CONTAINS "이차보전" OR p.policyName CONTAINS "제조업"
WITH u, p LIMIT 5
MERGE (u)-[r2:IS_ELIGIBLE_FOR]->(p)
SET r2.eligibilityScore = 0.85,
    r2.actionRequired = "즉시 신청"
// 결과 조회
WITH u
MATCH (u)-[r:IS_ELIGIBLE_FOR]->(solution)
RETURN 
  solution.policyName as 솔루션명,
  labels(solution)[0] as 유형,
  r.eligibilityScore as 적합도,
  r.urgency as 긴급도,
  r.expectedBenefit as 예상효과
ORDER BY r.eligibilityScore DESC;

// ========================================
// 8. 📊 경영진 의사결정 지원 요약
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
  변동금리부채 * 0.053 as "0.5%인상시_연간이자",
  변동금리부채 * 0.005 as "0.5%인상시_추가부담",
  "1. 즉시 KB 고정금리 대환대출 전환 (80억원)" as 액션1,
  "2. 정부 제조업 이차보전 프로그램 신청" as 액션2,
  "3. 금리스왑으로 나머지 리스크 헤지" as 액션3;

// ========================================
// 9. 🎯 실시간 모니터링 대시보드
// ========================================
// 대한정밀 전용 실시간 지표
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
  최근뉴스수 as "24시간내_관련뉴스",
  u.variableRateDebt * (m.changeRate / 100) / 12 as 월영향액;

// ========================================
// 10. 🔔 알림 설정용 쿼리
// ========================================
// 이 조건 충족 시 대한정밀에 즉시 알림
MATCH (m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리" AND 
      m.lastUpdated > datetime() - duration({hours: 1})
WITH m
MATCH (u:UserCompany {companyName: "대한정밀"})
WHERE m.changeRate > 0  // 금리 인상 시
RETURN 
  "🚨 긴급 알림" as 알림유형,
  u.companyName as 수신기업,
  m.indicatorName + " " + toString(m.changeRate) + "%p 인상" as 변동내용,
  "월 " + toString(u.variableRateDebt * (m.changeRate / 100) / 12) + "원 추가 부담 발생" as 영향,
  "KB 고정금리 전환 상품 즉시 상담 필요" as 권고사항,
  "02-2073-7114" as KB기업금융_긴급상담;