#!/usr/bin/env python3
"""
Enhanced Graph RAG System for KB Fortress AI (Fixed Version)
실제 Neo4j 스키마에 맞춘 완전히 수정된 버전
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
from neo4j_manager import Neo4jManager

@dataclass
class GraphQueryResult:
    """그래프 쿼리 결과"""
    query: str
    results: List[Dict[str, Any]]
    explanation: str
    confidence: float
    timestamp: datetime
    context: Dict[str, Any] = None

class EnhancedGraphRAG:
    """KB Fortress AI용 향상된 Graph RAG 시스템 (수정됨)"""
    
    def __init__(self):
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'
        
        self.neo4j_manager = Neo4jManager()
        print(" Enhanced Graph RAG 시스템 (Fixed) 초기화 완료")
        
        # 실제 스키마에 맞춘 쿼리 템플릿
        self.query_templates = {
            "user_company_profile": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})
                RETURN u.companyName as companyName,
                       u.industryDescription as industry,
                       u.revenue as revenue,
                       u.employeeCount as employees,
                       u.variableRateDebt as variableRateDebt,
                       u.location as location,
                       u.nodeId as nodeId
                """,
                "description": "사용자 기업 프로필 조회"
            },
            
            "risk_exposure_analysis": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_EXPOSED_TO]->(m:MacroIndicator)
                RETURN m.indicatorName as indicator,
                       m.value as currentValue,
                       coalesce(m.changeRate, 0) as changeRate,
                       m.unit as unit,
                       r.exposureLevel as exposureLevel,
                       coalesce(r.rationale, '일반 노출') as rationale,
                       coalesce(r.riskType, '기타') as riskType
                ORDER BY 
                  CASE r.exposureLevel 
                    WHEN 'HIGH' THEN 3 
                    WHEN 'MEDIUM' THEN 2 
                    ELSE 1 
                  END DESC
                """,
                "description": "기업의 거시경제 리스크 노출도 분석"
            },
            
            "kb_product_recommendations": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(k:KB_Product)
                RETURN k.productName as productName,
                       k.productType as productType,
                       coalesce(k.interestRate, '금리 정보 없음') as interestRate,
                       r.eligibilityScore as eligibilityScore,
                       coalesce(r.urgency, 'MEDIUM') as urgency,
                       coalesce(r.expectedBenefit, '금융비용 절감') as expectedBenefit
                ORDER BY r.eligibilityScore DESC
                """,
                "description": "KB 금융상품 맞춤 추천"
            },
            
            "policy_opportunities": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(p:Policy)
                RETURN p.policyName as policyName,
                       p.issuingOrg as issuingOrg,
                       p.supportField as supportField,
                       p.eligibilityText as eligibilityText,
                       r.eligibilityScore as eligibilityScore,
                       coalesce(r.actionRequired, '신청 검토') as actionRequired
                ORDER BY r.eligibilityScore DESC
                LIMIT 10
                """,
                "description": "정부 지원정책 매칭 기회"
            },
            
            "similar_company_insights": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[s:SIMILAR_TO]->(r:ReferenceCompany)
                OPTIONAL MATCH (r)-[e:IS_EXPOSED_TO]->(m:MacroIndicator)
                WITH r, s.similarityScore as similarityScore,
                     collect(DISTINCT {indicator: m.indicatorName, level: e.exposureLevel}) as riskProfile
                RETURN r.companyName as similarCompany,
                       r.sector as sector,
                       r.revenue as revenue,
                       similarityScore,
                       riskProfile[0..5] as topRisks
                ORDER BY similarityScore DESC
                """,
                "description": "유사 기업 벤치마킹 인사이트"
            },
            
            "news_impact_monitoring": {
                "query": """
                MATCH (n:NewsArticle)-[i:HAS_IMPACT_ON]->(u:UserCompany {companyName: $companyName})
                WHERE n.publishDate > datetime() - duration({days: $dayRange})
                RETURN n.title as newsTitle,
                       n.publisher as publisher,
                       n.publishDate as publishDate,
                       n.category as category,
                       coalesce(i.impactScore, 0.5) as impactScore,
                       coalesce(i.impactDirection, 'NEUTRAL') as impactDirection
                ORDER BY n.publishDate DESC, i.impactScore DESC
                LIMIT 20
                """,
                "description": "최근 뉴스 영향 모니터링"
            }
        }
    
    def analyze_user_company(self, company_name: str = "대한정밀") -> Dict[str, Any]:
        """사용자 기업 종합 분석"""
        print(f" {company_name} 기업 분석 시작...")
        
        analysis_result = {
            "company_name": company_name,
            "analysis_timestamp": datetime.now(),
            "profile": None,
            "risk_analysis": None,
            "solution_recommendations": {},
            "market_insights": {},
            "summary": {}
        }
        
        try:
            # 1. 기업 프로필 조회
            profile_result = self.execute_template_query(
                "user_company_profile", 
                {"companyName": company_name}
            )
            analysis_result["profile"] = profile_result
            
            # 2. 리스크 노출 분석
            risk_result = self.execute_template_query(
                "risk_exposure_analysis",
                {"companyName": company_name}
            )
            analysis_result["risk_analysis"] = risk_result
            
            # 3. KB 상품 추천
            kb_products = self.execute_template_query(
                "kb_product_recommendations",
                {"companyName": company_name}
            )
            
            # 4. 정책 기회 분석
            policy_opportunities = self.execute_template_query(
                "policy_opportunities",
                {"companyName": company_name}
            )
            
            analysis_result["solution_recommendations"] = {
                "kb_products": kb_products,
                "policy_opportunities": policy_opportunities
            }
            
            # 5. 유사 기업 인사이트
            similar_insights = self.execute_template_query(
                "similar_company_insights",
                {"companyName": company_name}
            )
            
            # 6. 뉴스 영향 모니터링
            news_impact = self.execute_template_query(
                "news_impact_monitoring",
                {"companyName": company_name, "dayRange": 30}
            )
            
            analysis_result["market_insights"] = {
                "similar_companies": similar_insights,
                "news_impact": news_impact
            }
            
            # 7. 요약 생성
            analysis_result["summary"] = self._generate_simple_summary(analysis_result)
            
            print(f" {company_name} 분석 완료")
            return analysis_result
            
        except Exception as e:
            print(f" 분석 오류: {e}")
            analysis_result["error"] = str(e)
            return analysis_result
    
    def simulate_interest_rate_impact(self, company_name: str = "대한정밀", rate_change: float = 0.5) -> Dict[str, Any]:
        """금리 변동 시뮬레이션"""
        print(f" {company_name} 금리 {rate_change}% 인상 영향 시뮬레이션...")
        
        profile_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        RETURN u.variableRateDebt as variableRateDebt,
               u.revenue as revenue,
               u.companyName as companyName
        """
        
        try:
            profile_result = self.neo4j_manager.execute_query(profile_query, {"companyName": company_name})
            
            if not profile_result:
                return {"error": f"{company_name} 정보를 찾을 수 없습니다"}
            
            company_data = profile_result[0]
            variable_debt = company_data.get("variableRateDebt", 0)
            revenue = company_data.get("revenue", 0)
            
            if variable_debt == 0:
                return {"error": "변동금리 대출 정보가 없습니다"}
            
            # 영향 계산
            annual_additional_cost = variable_debt * (rate_change / 100)
            monthly_additional_cost = annual_additional_cost / 12
            cost_to_revenue_ratio = (annual_additional_cost / revenue * 100) if revenue > 0 else 0
            
            # 심각도 분류
            if cost_to_revenue_ratio > 2:
                severity = "CRITICAL"
                severity_desc = "매출 대비 2% 이상 부담 증가"
            elif cost_to_revenue_ratio > 1:
                severity = "HIGH"
                severity_desc = "매출 대비 1-2% 부담 증가"
            elif cost_to_revenue_ratio > 0.5:
                severity = "MEDIUM"
                severity_desc = "매출 대비 0.5-1% 부담 증가"
            else:
                severity = "LOW"
                severity_desc = "상대적으로 낮은 부담 증가"
            
            simulation_result = {
                "company_name": company_name,
                "rate_change_percent": rate_change,
                "variable_rate_debt": variable_debt,
                "impact": {
                    "annual_additional_cost": annual_additional_cost,
                    "monthly_additional_cost": monthly_additional_cost,
                    "cost_to_revenue_ratio": cost_to_revenue_ratio,
                    "severity": severity,
                    "severity_description": severity_desc
                },
                "recommendations": [
                    "KB 고정금리 대환대출 검토",
                    "정부 이차보전 사업 신청",
                    "금리스왑 상품 활용 검토"
                ],
                "simulation_date": datetime.now()
            }
            
            return simulation_result
            
        except Exception as e:
            print(f" 금리 시뮬레이션 오류: {e}")
            return {"error": str(e)}
    
    def execute_template_query(self, template_name: str, parameters: Dict[str, Any]) -> GraphQueryResult:
        """템플릿 쿼리 실행"""
        if template_name not in self.query_templates:
            raise ValueError(f"알 수 없는 쿼리 템플릿: {template_name}")
        
        template = self.query_templates[template_name]
        query = template["query"]
        description = template["description"]
        
        try:
            results = self.neo4j_manager.execute_query(query, parameters)
            
            confidence = min(1.0, len(results) * 0.1) if results else 0.0
            
            return GraphQueryResult(
                query=query,
                results=results,
                explanation=description,
                confidence=confidence,
                timestamp=datetime.now(),
                context={"template": template_name, "parameters": parameters}
            )
            
        except Exception as e:
            print(f" 쿼리 실행 오류 ({template_name}): {e}")
            return GraphQueryResult(
                query=query,
                results=[],
                explanation=f"쿼리 실행 실패: {e}",
                confidence=0.0,
                timestamp=datetime.now(),
                context={"error": str(e)}
            )
    
    def _generate_simple_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 요약 생성"""
        try:
            # 안전한 데이터 추출
            risk_data = analysis_result.get("risk_analysis")
            risk_results = risk_data.results if risk_data and hasattr(risk_data, 'results') else []
            
            kb_data = analysis_result.get("solution_recommendations", {}).get("kb_products")
            kb_results = kb_data.results if kb_data and hasattr(kb_data, 'results') else []
            
            policy_data = analysis_result.get("solution_recommendations", {}).get("policy_opportunities")  
            policy_results = policy_data.results if policy_data and hasattr(policy_data, 'results') else []
            
            high_risks = [r for r in risk_results if r.get("exposureLevel") == "HIGH"]
            
            return {
                "total_risks": len(risk_results),
                "high_priority_risks": len(high_risks),
                "available_kb_products": len(kb_results),
                "available_policies": len(policy_results),
                "top_kb_product": kb_results[0].get("productName") if kb_results else "없음",
                "priority_risk": high_risks[0].get("indicator") if high_risks else "없음",
                "analysis_confidence": risk_data.confidence if risk_data and hasattr(risk_data, 'confidence') else 0.0
            }
        except Exception as e:
            print(f"️ 요약 생성 오류: {e}")
            return {"error": "요약 생성 실패"}
    
    def get_real_time_recommendations(self, company_name: str = "대한정밀") -> List[Dict[str, Any]]:
        """실시간 추천 시스템"""
        print(f" {company_name} 실시간 추천")
        
        recommendations_query = """
        MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(k:KB_Product)
        WHERE k.productName CONTAINS "고정금리" OR 
              k.productName CONTAINS "운전자금" OR
              r.eligibilityScore > 0.8
        RETURN k.productName as product,
               k.productType as type,
               r.eligibilityScore as score,
               coalesce(r.expectedBenefit, "금융비용 절감") as benefit,
               "금리 대응 추천" as reason
        ORDER BY r.eligibilityScore DESC
        LIMIT 5
        """
        
        try:
            results = self.neo4j_manager.execute_query(recommendations_query, {"companyName": company_name})
            
            recommendations = []
            for result in results:
                recommendation = {
                    "product_name": result.get("product"),
                    "product_type": result.get("type"),
                    "eligibility_score": result.get("score"),
                    "expected_benefit": result.get("benefit"),
                    "recommendation_reason": result.get("reason"),
                    "timestamp": datetime.now()
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            print(f" 실시간 추천 오류: {e}")
            return []
    
    def save_analysis_report(self, analysis_result: Dict[str, Any], output_dir: str = None) -> str:
        """분석 보고서 저장"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "data", "reports")
        
        os.makedirs(output_dir, exist_ok=True)
        
        company_name = analysis_result.get("company_name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = f"enhanced_analysis_{company_name}_{timestamp}"
        
        file_path = os.path.join(output_dir, f"{report_id}.json")
        
        # JSON 직렬화 가능한 형태로 변환
        serializable_result = json.loads(json.dumps(analysis_result, default=str))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f" 분석 보고서 저장: {file_path}")
        return file_path

def main():
    """Enhanced Graph RAG 시스템 테스트 (Fixed)"""
    print("=== Enhanced Graph RAG 시스템 테스트 (Fixed) ===")
    
    try:
        # 시스템 초기화
        enhanced_rag = EnhancedGraphRAG()
        
        # 대한정밀 종합 분석
        print("\n1. 대한정밀 종합 분석...")
        analysis = enhanced_rag.analyze_user_company("대한정밀")
        
        # 금리 영향 시뮬레이션
        print("\n2. 금리 0.5% 인상 시뮬레이션...")
        rate_simulation = enhanced_rag.simulate_interest_rate_impact("대한정밀", 0.5)
        
        # 실시간 추천
        print("\n3. 실시간 추천 시스템...")
        realtime_recs = enhanced_rag.get_real_time_recommendations("대한정밀")
        
        # 결과 종합
        final_report = {
            "comprehensive_analysis": analysis,
            "rate_impact_simulation": rate_simulation,
            "realtime_recommendations": realtime_recs,
            "generated_at": datetime.now()
        }
        
        # 보고서 저장
        report_path = enhanced_rag.save_analysis_report(final_report)
        
        # 핵심 결과 출력
        print("\n" + "="*60)
        print(" 대한정밀 분석 결과 요약")
        print("="*60)
        
        # 분석 요약 출력
        summary = analysis.get("summary", {})
        if summary and not summary.get("error"):
            print(f" 기업: 대한정밀")
            print(f"️  총 리스크: {summary.get('total_risks')}개")
            print(f" 고위험: {summary.get('high_priority_risks')}개")
            print(f" KB 상품: {summary.get('available_kb_products')}개")
            print(f" 정책 기회: {summary.get('available_policies')}개")
            print(f" 최우선 상품: {summary.get('top_kb_product')}")
            print(f" 핵심 리스크: {summary.get('priority_risk')}")
        
        # 금리 시뮬레이션 결과
        if rate_simulation and 'impact' in rate_simulation:
            impact = rate_simulation['impact']
            print(f" 금리 0.5% 인상 시 월 추가부담: {impact.get('monthly_additional_cost', 0):,.0f}원")
            print(f" 심각도: {impact.get('severity')}")
        
        # 실시간 추천 결과
        if realtime_recs:
            print(f" 긴급 추천 상품: {len(realtime_recs)}개")
            for i, rec in enumerate(realtime_recs[:3], 1):
                print(f"   {i}. {rec['product_name']} (적합도: {rec['eligibility_score']:.2f})")
        
        print(f"\n 상세 보고서: {report_path}")
        print("Enhanced Graph RAG 분석 완료!")
        
    except Exception as e:
        print(f" Enhanced Graph RAG 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'enhanced_rag' in locals() and hasattr(enhanced_rag, 'neo4j_manager'):
            enhanced_rag.neo4j_manager.close()

if __name__ == "__main__":
    main()