from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime
import os

import sys
import os
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

class GraphRAG:
    """Neo4j 기반 Graph RAG 시스템"""
    
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
        
        # 사전 정의된 쿼리 템플릿
        self.query_templates = {
            "company_eligibility": {
                "query": """
                MATCH (c:Company {nodeId: $companyId})-[r:IS_ELIGIBLE_FOR]->(p:KB_Product)
                RETURN c.companyName as company, 
                       p.productName as product,
                       p.productType as type,
                       p.interestRate as rate,
                       p.loanLimit as limit,
                       r.eligibilityScore as score,
                       r.matchingConditions as conditions
                ORDER BY r.eligibilityScore DESC
                """,
                "description": "기업이 자격을 갖춘 금융상품 조회"
            },
            
            "macro_exposure": {
                "query": """
                MATCH (c:Company {nodeId: $companyId})-[r:IS_EXPOSED_TO]->(m:MacroIndicator)
                RETURN c.companyName as company,
                       m.indicatorName as indicator,
                       m.value as current_value,
                       m.changeRate as change_rate,
                       m.unit as unit,
                       r.exposureLevel as exposure,
                       r.rationale as reason
                ORDER BY r.exposureLevel DESC
                """,
                "description": "기업의 거시경제지표 노출도 분석"
            },
            
            "impact_analysis": {
                "query": """
                MATCH (n:NewsArticle)-[r:HAS_IMPACT_ON]->(c:Company {nodeId: $companyId})
                RETURN n.title as news_title,
                       n.summary as summary,
                       n.publishDate as date,
                       r.impactScore as impact,
                       r.rationale as reason,
                       r.estimatedCost as cost
                ORDER BY n.publishDate DESC
                """,
                "description": "기업에 대한 뉴스 영향 분석"
            },
            
            "related_indicators": {
                "query": """
                MATCH (m1:MacroIndicator)-[:HAS_IMPACT_ON*1..2]-(m2:MacroIndicator)
                WHERE m1.nodeId = $indicatorId
                RETURN DISTINCT m2.indicatorName as indicator,
                       m2.value as value,
                       m2.changeRate as change_rate,
                       m2.unit as unit
                """,
                "description": "특정 지표와 연관된 다른 지표들"
            },
            
            "risk_propagation": {
                "query": """
                MATCH path = (event:NewsArticle)-[:HAS_IMPACT_ON]->(indicator:MacroIndicator)-[:IS_EXPOSED_TO]-(company:Company)
                WHERE event.nodeId = $eventId
                RETURN event.title as trigger_event,
                       indicator.indicatorName as affected_indicator,
                       company.companyName as impacted_company,
                       length(path) as propagation_steps
                """,
                "description": "이벤트에서 기업까지의 리스크 전파 경로"
            }
        }
    
    def execute_company_analysis(self, company_id: str = "company_daehan_precision") -> Dict[str, Any]:
        """특정 기업에 대한 종합 분석"""
        analysis_result = {
            "company_id": company_id,
            "timestamp": datetime.now(),
            "analyses": {}
        }
        
        # 1. 자격 상품 분석
        eligibility_result = self.execute_template_query(
            "company_eligibility", 
            {"companyId": company_id}
        )
        analysis_result["analyses"]["eligible_products"] = eligibility_result
        
        # 2. 거시경제 노출도 분석
        exposure_result = self.execute_template_query(
            "macro_exposure",
            {"companyId": company_id}
        )
        analysis_result["analyses"]["macro_exposure"] = exposure_result
        
        # 3. 영향 분석
        impact_result = self.execute_template_query(
            "impact_analysis",
            {"companyId": company_id}
        )
        analysis_result["analyses"]["impact_events"] = impact_result
        
        return analysis_result
    
    def execute_template_query(self, template_name: str, parameters: Dict[str, Any]) -> GraphQueryResult:
        """템플릿 쿼리 실행"""
        if template_name not in self.query_templates:
            raise ValueError(f"알 수 없는 쿼리 템플릿: {template_name}")
        
        template = self.query_templates[template_name]
        query = template["query"]
        description = template["description"]
        
        try:
            results = self.neo4j_manager.execute_query(query, parameters)
            
            # 신뢰도 계산 (결과 수와 데이터 완성도 기반)
            confidence = min(1.0, len(results) * 0.2) if results else 0.0
            
            return GraphQueryResult(
                query=query,
                results=results,
                explanation=description,
                confidence=confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"쿼리 실행 오류 ({template_name}): {e}")
            return GraphQueryResult(
                query=query,
                results=[],
                explanation=f"쿼리 실행 실패: {e}",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    def analyze_interest_rate_impact(self, rate_change: float = 0.5) -> Dict[str, Any]:
        """금리 변동 영향 분석"""
        
        # 기준금리에 노출된 기업들 조회
        exposure_query = """
        MATCH (c:Company)-[r:IS_EXPOSED_TO]->(m:MacroIndicator {indicatorName: '한국은행 기준금리'})
        RETURN c.companyName as company,
               c.nodeId as company_id,
               c.debtInfo as debt_info,
               r.exposureLevel as exposure,
               r.rationale as reason
        """
        
        try:
            exposed_companies = self.neo4j_manager.execute_query(exposure_query)
            
            impact_analysis = {
                "rate_change": rate_change,
                "analysis_date": datetime.now().isoformat(),
                "affected_companies": []
            }
            
            for company in exposed_companies:
                # 부채 정보에서 대출 규모 추출 (간단한 파싱)
                debt_info = company.get("debt_info", "")
                loan_amount = self._extract_loan_amount(debt_info)
                
                if loan_amount > 0:
                    # 연간 추가 이자 부담 계산
                    annual_additional_cost = loan_amount * (rate_change / 100)
                    monthly_additional_cost = annual_additional_cost / 12
                    
                    company_impact = {
                        "company": company["company"],
                        "exposure_level": company["exposure"],
                        "loan_amount": loan_amount,
                        "annual_additional_cost": annual_additional_cost,
                        "monthly_additional_cost": monthly_additional_cost,
                        "impact_severity": self._calculate_impact_severity(
                            company["exposure"], annual_additional_cost
                        )
                    }
                    impact_analysis["affected_companies"].append(company_impact)
            
            return impact_analysis
            
        except Exception as e:
            print(f"금리 영향 분석 오류: {e}")
            return {"error": str(e)}
    
    def _extract_loan_amount(self, debt_info: str) -> float:
        """부채 정보에서 대출 금액 추출 (간단한 파싱)"""
        import re
        
        # "변동금리 대출 10억원" 같은 패턴에서 숫자 추출
        pattern = r"(\d+)억원?"
        match = re.search(pattern, debt_info)
        
        if match:
            return float(match.group(1)) * 100000000  # 억 단위를 원 단위로 변환
        return 0.0
    
    def _calculate_impact_severity(self, exposure_level: float, additional_cost: float) -> str:
        """영향 심각도 계산"""
        severity_score = exposure_level * (additional_cost / 10000000)  # 천만원 단위로 정규화
        
        if severity_score >= 3.0:
            return "High"
        elif severity_score >= 1.5:
            return "Medium"
        else:
            return "Low"
    
    def find_solution_products(self, company_id: str, problem_type: str = "interest_burden") -> List[Dict[str, Any]]:
        """문제 해결을 위한 적합한 금융상품 추천"""
        
        if problem_type == "interest_burden":
            # 이자 부담 해결을 위한 상품 추천
            solution_query = """
            MATCH (c:Company {nodeId: $companyId})-[r:IS_ELIGIBLE_FOR]->(p:KB_Product)
            WHERE p.productType IN ['운전자금', '기타'] 
              AND (p.specialConditions CONTAINS '협약' OR p.collateral = '부동산담보')
            RETURN p.productName as product,
                   p.productType as type,
                   p.interestRate as rate,
                   p.specialConditions as conditions,
                   r.eligibilityScore as score,
                   CASE 
                     WHEN p.specialConditions CONTAINS '협약' THEN '정책자금 우대금리 활용'
                     WHEN p.collateral = '부동산담보' THEN '담보대출로 금리 우대'
                     ELSE '일반 운전자금'
                   END as solution_type
            ORDER BY r.eligibilityScore DESC
            """
        else:
            # 기본 추천
            solution_query = """
            MATCH (c:Company {nodeId: $companyId})-[r:IS_ELIGIBLE_FOR]->(p:KB_Product)
            RETURN p.productName as product,
                   p.productType as type,
                   p.interestRate as rate,
                   r.eligibilityScore as score
            ORDER BY r.eligibilityScore DESC
            LIMIT 5
            """
        
        try:
            results = self.neo4j_manager.execute_query(solution_query, {"companyId": company_id})
            
            recommendations = []
            for result in results:
                recommendation = {
                    "product_name": result.get("product"),
                    "product_type": result.get("type"),
                    "interest_rate": result.get("rate"),
                    "eligibility_score": result.get("score"),
                    "solution_rationale": result.get("solution_type", "일반 추천")
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            print(f"해결책 추천 오류: {e}")
            return []
    
    def generate_comprehensive_report(self, company_id: str = "company_daehan_precision") -> Dict[str, Any]:
        """종합 분석 보고서 생성"""
        
        print(f"'{company_id}' 기업 종합 분석 보고서 생성 중...")
        
        # 1. 기본 기업 분석
        company_analysis = self.execute_company_analysis(company_id)
        
        # 2. 금리 영향 분석
        rate_impact = self.analyze_interest_rate_impact(0.5)
        
        # 3. 해결책 추천
        solutions = self.find_solution_products(company_id, "interest_burden")
        
        # 4. 종합 보고서 구성
        comprehensive_report = {
            "report_id": f"report_{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "company_analysis": company_analysis,
            "risk_analysis": {
                "interest_rate_impact": rate_impact
            },
            "recommendations": {
                "financial_products": solutions
            },
            "summary": self._generate_executive_summary(company_analysis, rate_impact, solutions)
        }
        
        return comprehensive_report
    
    def _generate_executive_summary(self, company_analysis: Dict, rate_impact: Dict, solutions: List) -> Dict[str, str]:
        """경영진 요약 생성"""
        
        # 주요 리스크 식별
        main_risks = []
        if rate_impact.get("affected_companies"):
            company_impact = rate_impact["affected_companies"][0]
            monthly_cost = company_impact.get("monthly_additional_cost", 0)
            if monthly_cost > 0:
                main_risks.append(f"금리 인상으로 월 {monthly_cost:,.0f}원 추가 부담")
        
        # 주요 기회 식별
        opportunities = []
        if solutions:
            top_solution = solutions[0]
            opportunities.append(f"{top_solution['product_name']} 활용으로 금융비용 절감 가능")
        
        return {
            "main_risks": "; ".join(main_risks) if main_risks else "주요 리스크 없음",
            "opportunities": "; ".join(opportunities) if opportunities else "추천 상품 없음",
            "recommended_action": "정책자금 대출 활용으로 이자 부담 경감 필요" if solutions else "현 상황 모니터링 지속"
        }
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "data/reports"):
        """보고서 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        report_id = report.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        file_path = os.path.join(output_dir, f"{report_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f" 보고서 저장: {file_path}")
        return file_path

def main():
    """Graph RAG 시스템 테스트"""
    print("=== Graph RAG 시스템 테스트 ===")
    
    try:
        graph_rag = GraphRAG()
        
        # 종합 분석 보고서 생성
        report = graph_rag.generate_comprehensive_report()
        
        # 보고서 저장
        file_path = graph_rag.save_report(report)
        
        # 요약 출력
        print("\n=== 분석 결과 요약 ===")
        summary = report["summary"]
        print(f"주요 리스크: {summary['main_risks']}")
        print(f"기회 요소: {summary['opportunities']}")
        print(f"권장 조치: {summary['recommended_action']}")
        
        # 추천 상품 출력
        recommendations = report["recommendations"]["financial_products"]
        if recommendations:
            print(f"\n=== 추천 금융상품 (상위 3개) ===")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec['product_name']} (적합도: {rec['eligibility_score']:.1f})")
                print(f"   - {rec['solution_rationale']}")
        
        print(f"\n Graph RAG 분석 완료! 상세 보고서: {file_path}")
        
    except Exception as e:
        print(f" Graph RAG 시스템 오류: {e}")
    
    finally:
        if 'graph_rag' in locals():
            graph_rag.neo4j_manager.close()

if __name__ == "__main__":
    main()