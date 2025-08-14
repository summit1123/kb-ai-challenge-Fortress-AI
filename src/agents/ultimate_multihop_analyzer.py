"""
Ultimate Multi-hop Analysis System
완벽한 그래프 경로 기반 복합 위험 분석 시스템
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.graph.neo4j_manager import Neo4jManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

@dataclass
class RiskPath:
    """위험 전파 경로"""
    path_id: str
    path_length: int
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    total_risk_score: float
    path_explanation: str
    impact_chain: str

@dataclass
class ComprehensiveRiskAssessment:
    """종합 위험 평가"""
    company_name: str
    risk_paths: List[RiskPath]
    composite_risk_score: float
    primary_risk_factors: List[str]
    recommended_solutions: List[Dict[str, Any]]
    risk_mitigation_strategies: List[str]
    monitoring_indicators: List[str]

class UltimateMultihopAnalyzer:
    """궁극의 멀티홉 분석 시스템"""
    
    def __init__(self):
        try:
            self.neo4j_manager = Neo4jManager()
            print(" Neo4j 연결 성공: Ultimate Multihop Analyzer 준비 완료")
        except Exception as e:
            print(f" Neo4j 연결 실패: {e}")
            self.neo4j_manager = None
        
        # LLM 설정
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=google_api_key
            )
            print(" LLM 분석 엔진 준비 완료")
        else:
            self.llm = None
            print("️ LLM 없이 진행 (기본 분석만 가능)")
    
    def analyze_company_multihop_risks(self, company_name: str) -> ComprehensiveRiskAssessment:
        """기업의 멀티홉 위험 종합 분석"""
        print(f" {company_name} 멀티홉 위험 분석 시작...")
        
        # 1. 모든 위험 경로 탐색
        risk_paths = self._discover_all_risk_paths(company_name)
        print(f" 발견된 위험 경로: {len(risk_paths)}개")
        
        # 2. 경로별 위험도 계산
        analyzed_paths = []
        for path in risk_paths:
            analyzed_path = self._analyze_risk_path(path)
            if analyzed_path:
                analyzed_paths.append(analyzed_path)
        
        # 3. 복합 위험도 계산
        composite_score = self._calculate_composite_risk_score(analyzed_paths)
        
        # 4. 주요 위험 요소 식별
        primary_risks = self._identify_primary_risk_factors(analyzed_paths)
        
        # 5. 솔루션 추천
        solutions = self._recommend_solutions(company_name, analyzed_paths)
        
        # 6. 완화 전략 생성
        strategies = self._generate_mitigation_strategies(analyzed_paths)
        
        # 7. 모니터링 지표 제안
        monitoring = self._suggest_monitoring_indicators(analyzed_paths)
        
        return ComprehensiveRiskAssessment(
            company_name=company_name,
            risk_paths=analyzed_paths,
            composite_risk_score=composite_score,
            primary_risk_factors=primary_risks,
            recommended_solutions=solutions,
            risk_mitigation_strategies=strategies,
            monitoring_indicators=monitoring
        )
    
    def _discover_all_risk_paths(self, company_name: str) -> List[Dict[str, Any]]:
        """모든 가능한 위험 경로 발견"""
        if not self.neo4j_manager:
            return []
        
        # 멀티홉 경로 탐색 쿼리들
        path_queries = [
            # 2단계: 뉴스 → 거시지표 → 기업
            """
            MATCH path = (news:NewsArticle)-[r1:HAS_IMPACT_ON]->(macro:MacroIndicator)
                         <-[r2:IS_EXPOSED_TO]-(company:UserCompany {companyName: $company_name})
            RETURN path, 
                   news.title as news_title,
                   news.publisher as news_publisher,
                   macro.indicatorName as indicator,
                   r1.impactScore as news_impact,
                   r1.rationale as impact_rationale,
                   r2.exposureLevel as exposure_level,
                   r2.rationale as exposure_rationale,
                   'news_macro_company' as path_type,
                   2 as path_length
            """,
            
            # 3단계: 뉴스 → 거시지표 → 벤치마크기업 → 우리기업
            """
            MATCH path = (news:NewsArticle)-[r1:HAS_IMPACT_ON]->(macro:MacroIndicator)
                         <-[r2:IS_EXPOSED_TO]-(benchmark:ReferenceCompany)
                         -[r3:SIMILAR_TO]-(company:UserCompany {companyName: $company_name})
            RETURN path,
                   news.title as news_title,
                   macro.indicatorName as indicator,
                   benchmark.companyName as benchmark_company,
                   'news_macro_benchmark_company' as path_type,
                   3 as path_length
            """,
            
            # 직접 영향: 뉴스 → 기업
            """
            MATCH path = (news:NewsArticle)-[r1:HAS_IMPACT_ON]->(company:ReferenceCompany)
                         -[r2:SIMILAR_TO]-(user_company:UserCompany {companyName: $company_name})
            RETURN path,
                   news.title as news_title,
                   company.companyName as affected_company,
                   r1.impactScore as direct_impact,
                   'news_company_similarity' as path_type,
                   2 as path_length
            """,
            
            # 기업 → 정책 → 솔루션 경로
            """
            MATCH path = (company:UserCompany {companyName: $company_name})
                         -[r1:IS_ELIGIBLE_FOR]->(policy:Policy)
                         -[r2:SYNERGY_WITH]->(product:KB_Product)
            RETURN path,
                   policy.policyName as policy_name,
                   product.productName as solution,
                   'company_policy_solution' as path_type,
                   2 as path_length
            """
        ]
        
        all_paths = []
        for query in path_queries:
            try:
                results = self.neo4j_manager.execute_query(query, {"company_name": company_name})
                all_paths.extend(results)
            except Exception as e:
                print(f" 경로 탐색 실패: {e}")
                continue
        
        return all_paths
    
    def _analyze_risk_path(self, path_data: Dict[str, Any]) -> Optional[RiskPath]:
        """개별 위험 경로 분석"""
        try:
            path_type = path_data.get('path_type', '')
            path_length = path_data.get('path_length', 0)
            
            # 경로별 위험도 계산
            risk_score = 0.0
            
            if path_type == 'news_macro_company':
                # 뉴스 영향도 × 기업 노출도
                news_impact = path_data.get('news_impact', 0.0)
                exposure_level = path_data.get('exposure_level', 'LOW')
                exposure_multiplier = {'HIGH': 1.0, 'MEDIUM': 0.7, 'LOW': 0.4}.get(exposure_level, 0.4)
                risk_score = news_impact * exposure_multiplier
                
                # 경로 설명 생성
                explanation = f"뉴스 '{path_data.get('news_title', '')}' → {path_data.get('indicator', '')} → 기업 노출"
                impact_chain = f"언론보도({news_impact:.1f}) → 거시지표변동 → 기업영향({exposure_level})"
                
            elif path_type == 'news_macro_benchmark_company':
                # 3단계 경로는 감쇠 적용
                risk_score = 0.6  # 기본값, 벤치마킹 효과
                explanation = f"뉴스 → {path_data.get('indicator', '')} → 벤치마크기업({path_data.get('benchmark_company', '')}) → 우리기업"
                impact_chain = "산업 전반 영향 → 유사기업 → 간접 파급효과"
                
            elif path_type == 'news_company_similarity':
                direct_impact = path_data.get('direct_impact', 0.0)
                risk_score = direct_impact * 0.8  # 유사성 할인
                explanation = f"뉴스 → {path_data.get('affected_company', '')} → 유사성을 통한 간접 영향"
                impact_chain = f"직접영향({direct_impact:.1f}) → 유사기업 → 간접영향"
                
            elif path_type == 'company_policy_solution':
                risk_score = -0.3  # 정책/솔루션은 위험 완화 효과
                explanation = f"정책 '{path_data.get('policy_name', '')}' → 솔루션 '{path_data.get('solution', '')}'"
                impact_chain = "정책 지원 → 금융 솔루션 → 위험 완화"
            
            return RiskPath(
                path_id=f"{path_type}_{hash(str(path_data))}",
                path_length=path_length,
                nodes=[],  # 필요시 상세 노드 정보 추가
                relationships=[],  # 필요시 상세 관계 정보 추가
                total_risk_score=risk_score,
                path_explanation=explanation,
                impact_chain=impact_chain
            )
            
        except Exception as e:
            print(f" 경로 분석 실패: {e}")
            return None
    
    def _calculate_composite_risk_score(self, risk_paths: List[RiskPath]) -> float:
        """복합 위험도 계산"""
        if not risk_paths:
            return 0.0
        
        # 가중 평균 계산 (경로 길이에 따라 가중치 조정)
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for path in risk_paths:
            # 경로가 짧을수록 더 직접적인 영향 (높은 가중치)
            weight = 1.0 / path.path_length
            total_weighted_score += path.total_risk_score * weight
            total_weight += weight
        
        composite_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # 0-100 스케일로 정규화
        return min(max(composite_score * 100, 0), 100)
    
    def _identify_primary_risk_factors(self, risk_paths: List[RiskPath]) -> List[str]:
        """주요 위험 요소 식별"""
        risk_factors = []
        
        # 위험도가 높은 경로들에서 핵심 요소 추출
        high_risk_paths = [path for path in risk_paths if path.total_risk_score > 0.5]
        
        for path in high_risk_paths[:3]:  # 상위 3개
            risk_factors.append(path.path_explanation)
        
        if not risk_factors:
            risk_factors = ["현재 식별된 고위험 요소 없음"]
        
        return risk_factors
    
    def _recommend_solutions(self, company_name: str, risk_paths: List[RiskPath]) -> List[Dict[str, Any]]:
        """KB 솔루션 추천"""
        if not self.neo4j_manager:
            return []
        
        # 위험 유형별 적합한 KB 상품 매칭
        solution_query = """
        MATCH (company:UserCompany {companyName: $company_name})-[:IS_EXPOSED_TO]->(macro:MacroIndicator),
              (product:KB_Product)
        WHERE (macro.indicatorName CONTAINS '금리' AND product.productName CONTAINS '금리')
           OR (macro.indicatorName CONTAINS '환율' AND product.productName CONTAINS '환헤지')
           OR product.targetCustomer CONTAINS '중소기업'
        RETURN DISTINCT product.productName as product,
                        product.productType as type,
                        product.description as description,
                        macro.indicatorName as target_risk
        LIMIT 5
        """
        
        try:
            solutions = self.neo4j_manager.execute_query(solution_query, {"company_name": company_name})
            
            # 솔루션 데이터 정리
            formatted_solutions = []
            for sol in solutions:
                formatted_solutions.append({
                    "product_name": sol.get("product", ""),
                    "product_type": sol.get("type", ""),
                    "description": sol.get("description", ""),
                    "target_risk": sol.get("target_risk", ""),
                    "recommendation_reason": f"{sol.get('target_risk', '')} 위험 대응"
                })
            
            return formatted_solutions
            
        except Exception as e:
            print(f" 솔루션 추천 실패: {e}")
            return []
    
    def _generate_mitigation_strategies(self, risk_paths: List[RiskPath]) -> List[str]:
        """위험 완화 전략 생성"""
        strategies = []
        
        # 경로 유형별 맞춤 전략
        path_types = [path.impact_chain for path in risk_paths if path.total_risk_score > 0.3]
        
        if any("금리" in chain for chain in path_types):
            strategies.append("변동금리 대출 비중 축소 및 고정금리 전환 검토")
        
        if any("환율" in chain for chain in path_types):
            strategies.append("환헤지 상품 활용으로 환율 변동 리스크 완화")
        
        if any("원자재" in chain for chain in path_types):
            strategies.append("원자재 가격 안정화를 위한 장기 계약 체결")
        
        if any("유사기업" in chain for chain in path_types):
            strategies.append("업종 특화 위험 모니터링 및 벤치마킹 강화")
        
        if not strategies:
            strategies.append("정기적인 재무 건전성 점검 및 위험 관리 체계 구축")
        
        return strategies
    
    def _suggest_monitoring_indicators(self, risk_paths: List[RiskPath]) -> List[str]:
        """모니터링 지표 제안"""
        indicators = []
        
        # 위험 경로 기반 핵심 모니터링 지표
        indicators.extend([
            "한국은행 기준금리 변동 추이",
            "원/달러 환율 변동성",
            "업종별 제조업 BSI (기업경기실사지수)",
            "변동금리 대출 이자부담률",
            "수출 계약 환율 적용 현황"
        ])
        
        return indicators[:5]  # 최대 5개
    
    def generate_analysis_report(self, assessment: ComprehensiveRiskAssessment) -> str:
        """종합 분석 보고서 생성"""
        
        report = f"""
#  {assessment.company_name} 멀티홉 위험 분석 보고서

##  종합 위험도: {assessment.composite_risk_score:.1f}/100

##  주요 위험 경로 ({len(assessment.risk_paths)}개)
"""
        
        for i, path in enumerate(assessment.risk_paths[:5], 1):
            report += f"""
### {i}. {path.path_explanation}
- **위험도**: {path.total_risk_score:.2f}
- **경로 길이**: {path.path_length}단계
- **영향 체인**: {path.impact_chain}
"""
        
        report += f"""
## ️ 핵심 위험 요소
"""
        for i, risk in enumerate(assessment.primary_risk_factors, 1):
            report += f"{i}. {risk}\n"
        
        report += f"""
##  추천 KB 솔루션 ({len(assessment.recommended_solutions)}개)
"""
        for i, solution in enumerate(assessment.recommended_solutions, 1):
            report += f"""
### {i}. {solution.get('product_name', 'N/A')}
- **유형**: {solution.get('product_type', 'N/A')}
- **대응 위험**: {solution.get('target_risk', 'N/A')}
- **추천 이유**: {solution.get('recommendation_reason', 'N/A')}
"""
        
        report += f"""
## ️ 위험 완화 전략
"""
        for i, strategy in enumerate(assessment.risk_mitigation_strategies, 1):
            report += f"{i}. {strategy}\n"
        
        report += f"""
##  모니터링 지표
"""
        for i, indicator in enumerate(assessment.monitoring_indicators, 1):
            report += f"{i}. {indicator}\n"
        
        report += f"""
---
*보고서 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*분석 시스템: KB Fortress AI Ultimate Multihop Analyzer*
"""
        
        return report

# 테스트 및 실행 함수
def test_ultimate_multihop_analysis():
    """Ultimate Multihop Analyzer 테스트"""
    print(" Ultimate Multihop Analysis 테스트 시작")
    
    analyzer = UltimateMultihopAnalyzer()
    
    # 대한정밀 분석
    assessment = analyzer.analyze_company_multihop_risks("대한정밀")
    
    # 보고서 생성
    report = analyzer.generate_analysis_report(assessment)
    
    print(" 분석 보고서:")
    print(report)
    
    # 보고서 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/ultimate_multihop_analysis_{timestamp}.md"
    
    os.makedirs("reports", exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f" 보고서 저장됨: {report_path}")
    
    return assessment

if __name__ == "__main__":
    test_ultimate_multihop_analysis()