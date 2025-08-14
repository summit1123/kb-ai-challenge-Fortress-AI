// ================================================
// 그래프 구조 기반 상관관계 분석 쿼리
// 대한정밀과 연결된 네트워크에서 인사이트 도출
// ================================================

// ========================================
// 1. 🔗 금리 리스크 전파 경로 분석
// ========================================
// 금리 변동이 대한정밀에 미치는 다단계 영향 경로
MATCH path = (m:MacroIndicator)-[:HAS_IMPACT_ON*1..3]-(target)
WHERE m.indicatorName CONTAINS "금리" AND 
      (target:UserCompany {companyName: "대한정밀"} OR 
       target:ReferenceCompany {sector: "automotive_parts"})
RETURN 
  m.indicatorName as 시작점,
  [node in nodes(path) | labels(node)[0] + ": " + coalesce(node.title, node.companyName, node.indicatorName)] as 전파경로,
  length(path) as 경로길이,
  CASE 
    WHEN length(path) = 1 THEN "직접영향"
    WHEN length(path) = 2 THEN "간접영향"
    ELSE "파급영향"
  END as 영향유형
ORDER BY length(path);

// ========================================
// 2. 📊 업종 클러스터별 리스크 패턴 분석
// ========================================
// 자동차부품업체들의 공통 리스크와 대응 패턴
MATCH (c1:ReferenceCompany {sector: "automotive_parts"})-[r1:IS_EXPOSED_TO]->(m:MacroIndicator)
WITH m, collect(DISTINCT c1) as exposed_companies, avg(toFloat(
  CASE r1.exposureLevel 
    WHEN 'HIGH' THEN 0.9 
    WHEN 'MEDIUM' THEN 0.6 
    ELSE 0.3 
  END)) as avg_exposure
WHERE size(exposed_companies) >= 3
MATCH (u:UserCompany {companyName: "대한정밀"})
RETURN 
  m.indicatorName as 공통리스크,
  size(exposed_companies) as 노출기업수,
  round(avg_exposure * 100) as 평균노출도,
  [c IN exposed_companies | c.companyName][0..3] as 주요노출기업,
  CASE 
    WHEN avg_exposure > 0.7 THEN "🔴 업종 전체 고위험"
    WHEN avg_exposure > 0.5 THEN "🟡 업종 중위험"
    ELSE "🟢 업종 저위험"
  END as 업종리스크수준,
  "대한정밀도 동일 리스크 노출 가능성 " + toString(round(avg_exposure * 100)) + "%" as 대한정밀_시사점
ORDER BY avg_exposure DESC;

// ========================================
// 3. 🎯 솔루션 효과성 네트워크 분석
// ========================================
// 유사 기업들이 활용한 솔루션의 효과성 파악
MATCH (r:ReferenceCompany)-[e1:IS_EXPOSED_TO]->(risk:MacroIndicator)
WHERE risk.indicatorName CONTAINS "금리" AND e1.exposureLevel = "HIGH"
MATCH (r)-[e2:IS_ELIGIBLE_FOR]->(solution)
WHERE solution:KB_Product OR solution:Policy
WITH risk, solution, collect(r) as companies, avg(e2.eligibilityScore) as avg_score
WHERE size(companies) >= 2
RETURN 
  risk.indicatorName as 리스크요인,
  CASE 
    WHEN solution:KB_Product THEN "KB상품: " + solution.productName
    ELSE "정책: " + solution.policyName
  END as 솔루션,
  size(companies) as 활용기업수,
  round(avg_score * 100) as 평균적합도,
  [c IN companies | c.companyName] as 활용기업목록,
  "대한정밀 추천도: " + 
  CASE 
    WHEN avg_score > 0.8 THEN "⭐⭐⭐⭐⭐ 매우높음"
    WHEN avg_score > 0.6 THEN "⭐⭐⭐⭐ 높음"
    ELSE "⭐⭐⭐ 보통"
  END as 추천수준
ORDER BY avg_score DESC
LIMIT 10;

// ========================================
// 4. 🔄 뉴스-기업-지표 순환 영향 분석
// ========================================
// 뉴스가 거시지표를 통해 기업에 미치는 간접 영향
MATCH path = (n:NewsArticle)-[:HAS_IMPACT_ON]->(m:MacroIndicator)<-[:IS_EXPOSED_TO]-(c:ReferenceCompany)
WHERE n.category = "financial" AND m.indicatorName CONTAINS "금리"
WITH n, m, collect(DISTINCT c) as affected_companies
WHERE size(affected_companies) >= 3
MATCH (u:UserCompany {companyName: "대한정밀"})
MATCH (similar:ReferenceCompany {sector: "automotive_parts"})
WHERE similar IN affected_companies
RETURN 
  substring(n.title, 0, 50) + "..." as 뉴스제목,
  m.indicatorName as 영향받은지표,
  size(affected_companies) as 영향받은기업수,
  size([c IN affected_companies WHERE c.sector = "automotive_parts"]) as 자동차부품업체수,
  CASE 
    WHEN size([c IN affected_companies WHERE c.sector = "automotive_parts"]) > 3 THEN "🔴 업종 전체 영향"
    WHEN size([c IN affected_companies WHERE c.sector = "automotive_parts"]) > 1 THEN "🟡 일부 영향"
    ELSE "🟢 제한적 영향"
  END as 업종영향도,
  "대한정밀 예상 영향: 유사기업 " + 
  toString(size([c IN affected_companies WHERE c.sector = "automotive_parts"])) + 
  "개사 영향받음" as 대한정밀_영향예측
ORDER BY size(affected_companies) DESC
LIMIT 10;

// ========================================
// 5. 💡 경쟁사 대응전략 벤치마킹 분석
// ========================================
// 유사 상황의 기업들이 선택한 솔루션 조합 패턴
MATCH (r:ReferenceCompany {sector: "automotive_parts"})-[:IS_EXPOSED_TO]->(m:MacroIndicator)
WHERE m.indicatorName CONTAINS "금리"
MATCH (r)-[:IS_ELIGIBLE_FOR]->(s1:KB_Product)
MATCH (r)-[:IS_ELIGIBLE_FOR]->(s2:Policy)
WITH r, collect(DISTINCT s1.productName) as kb_products, collect(DISTINCT s2.policyName) as policies
WHERE size(kb_products) > 0 AND size(policies) > 0
RETURN 
  r.companyName as 기업명,
  r.variableRateExposure as 변동금리노출도,
  kb_products[0..3] as 활용KB상품,
  policies[0..3] as 활용정책,
  size(kb_products) + size(policies) as 총솔루션수,
  "대한정밀 벤치마킹 포인트: " + kb_products[0] + " + " + policies[0] + " 조합 추천" as 추천조합
ORDER BY r.variableRateExposure DESC
LIMIT 5;

// ========================================
// 6. 📈 리스크-솔루션 매칭 효율성 분석
// ========================================
// 어떤 리스크에 어떤 솔루션이 가장 효과적인지
MATCH (c:ReferenceCompany)-[e1:IS_EXPOSED_TO]->(risk:MacroIndicator)
MATCH (c)-[e2:IS_ELIGIBLE_FOR]->(solution)
WHERE risk.indicatorName CONTAINS "금리" OR risk.indicatorName CONTAINS "환율"
WITH risk.indicatorName as 리스크,
     CASE 
       WHEN solution:KB_Product THEN solution.productName
       ELSE solution.policyName
     END as 솔루션명,
     labels(solution)[0] as 솔루션유형,
     count(*) as 매칭수,
     avg(e2.eligibilityScore) as 평균적합도
RETURN 
  리스크,
  솔루션유형 + ": " + 솔루션명 as 솔루션,
  매칭수,
  round(평균적합도 * 100) as 평균적합도_퍼센트,
  CASE 
    WHEN 평균적합도 > 0.8 AND 매칭수 > 5 THEN "🏆 최적 솔루션"
    WHEN 평균적합도 > 0.7 AND 매칭수 > 3 THEN "👍 추천 솔루션"
    ELSE "🔍 검토 필요"
  END as 추천등급
ORDER BY 리스크, 평균적합도 DESC;

// ========================================
// 7. 🌐 2차 연결 네트워크 영향력 분석
// ========================================
// 대한정밀과 2단계로 연결된 노드들의 영향력
MATCH (u:UserCompany {companyName: "대한정밀"})-[*2]-(influenced)
WHERE NOT influenced:UserCompany
WITH labels(influenced)[0] as 노드유형,
     count(DISTINCT influenced) as 연결수,
     collect(DISTINCT CASE 
       WHEN influenced:ReferenceCompany THEN influenced.companyName
       WHEN influenced:KB_Product THEN influenced.productName
       WHEN influenced:Policy THEN influenced.policyName
       WHEN influenced:NewsArticle THEN influenced.title
       WHEN influenced:MacroIndicator THEN influenced.indicatorName
       ELSE "기타"
     END)[0..3] as 주요연결
RETURN 
  노드유형,
  연결수,
  주요연결,
  CASE 
    WHEN 노드유형 = "KB_Product" THEN "💰 금융상품 확대 검토"
    WHEN 노드유형 = "Policy" THEN "📋 정책 활용 기회"
    WHEN 노드유형 = "MacroIndicator" THEN "📊 추가 리스크 모니터링"
    WHEN 노드유형 = "NewsArticle" THEN "📰 시장 동향 주시"
    ELSE "🔍 추가 분석 필요"
  END as 시사점
ORDER BY 연결수 DESC;

// ========================================
// 8. 🎨 시각화용 핵심 상관관계 네트워크
// ========================================
// 대한정밀 중심의 주요 상관관계만 추출
MATCH (u:UserCompany {companyName: "대한정밀"})
// 직접 연결
OPTIONAL MATCH (u)-[r1:IS_ELIGIBLE_FOR]->(direct_sol)
WHERE r1.eligibilityScore > 0.8
// 유사기업 경유 연결
OPTIONAL MATCH (u)-[:SIMILAR_TO]->(similar)-[:IS_ELIGIBLE_FOR]->(indirect_sol)
// 리스크 연결
OPTIONAL MATCH (u)-[:IS_EXPOSED_TO]->(risk)
RETURN u, r1, direct_sol, similar, indirect_sol, risk
LIMIT 30;

// ========================================
// 9. 📊 종합 인사이트 도출
// ========================================
// 그래프 분석을 통한 핵심 인사이트 정리
MATCH (u:UserCompany {companyName: "대한정밀"})
// 직접 연결 분석
OPTIONAL MATCH (u)-[]->(direct)
WITH u, count(DISTINCT direct) as 직접연결수
// 간접 연결 분석
OPTIONAL MATCH (u)-[*2]-(indirect)
WITH u, 직접연결수, count(DISTINCT indirect) as 간접연결수
// 리스크 분석
OPTIONAL MATCH (u)-[:IS_EXPOSED_TO]->(risk)
WITH u, 직접연결수, 간접연결수, count(DISTINCT risk) as 리스크수
// 솔루션 분석
OPTIONAL MATCH (u)-[:IS_ELIGIBLE_FOR]->(solution)
RETURN 
  "대한정밀 네트워크 분석 요약" as 제목,
  직접연결수 as 직접연결노드,
  간접연결수 as 간접영향노드,
  리스크수 as 노출리스크,
  count(DISTINCT solution) as 가용솔루션,
  CASE 
    WHEN 리스크수 > count(DISTINCT solution) THEN "⚠️ 리스크 > 솔루션: 추가 대응방안 필요"
    WHEN 리스크수 = count(DISTINCT solution) THEN "⚖️ 리스크 = 솔루션: 균형 상태"
    ELSE "✅ 리스크 < 솔루션: 충분한 대응 옵션 보유"
  END as 리스크대응수준,
  "핵심제언: " + 
  CASE 
    WHEN 리스크수 > 3 THEN "다각적 리스크 헤지 전략 시급"
    ELSE "선별적 솔루션 실행으로 효율성 극대화"
  END as 전략제언;