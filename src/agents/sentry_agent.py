from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
from neo4j_manager import Neo4jManager

try:
    from enhanced_graph_rag import EnhancedGraphRAG
except ImportError:
    # agents 폴더에서 import 시도
    sys.path.append(os.path.dirname(__file__))
    from enhanced_graph_rag import EnhancedGraphRAG

class SentryAgentState(TypedDict):
    """금융 파수꾼 에이전트 상태"""
    messages: List[Dict[str, str]]
    current_event: Dict[str, Any]
    company_context: Dict[str, Any]
    identified_risks: List[Dict[str, Any]]
    impact_analysis: Dict[str, Any]
    found_solutions: List[Dict[str, Any]]
    final_report: str
    processing_stage: str
    confidence_score: float

@dataclass
class FinancialEvent:
    """금융/경제 이벤트"""
    event_id: str
    title: str
    description: str
    event_type: str  # interest_rate, exchange_rate, policy, news
    impact_magnitude: float  # -1.0 ~ 1.0
    affected_indicators: List[str]
    source: str
    timestamp: datetime

class SentryAgent:
    """KB Fortress AI 금융 파수꾼 에이전트"""
    
    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY", "AIzaSyDGYyMpF8gTOg6ps7PJAg1VAZNRJLAUiYA")
        if not self.google_api_key:
            print("️  Google API 키가 없어 LLM 기능이 제한됩니다")
            self.llm = None
        else:
            # Google API Key 환경변수 설정
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.google_api_key,
                temperature=0.1
            )
            print(" Google Gemini 2.0 Flash 모델 초기화 완료")
        
        self.enhanced_graph_rag = EnhancedGraphRAG()
        self.neo4j_manager = Neo4jManager()
        
        # 워크플로우 그래프 구성
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(SentryAgentState)
        
        # 노드 추가
        workflow.add_node("detect_event", self.detect_event)
        workflow.add_node("analyze_company_context", self.analyze_company_context)
        workflow.add_node("assess_risk_impact", self.assess_risk_impact)
        workflow.add_node("find_solutions", self.find_solutions)
        workflow.add_node("generate_report", self.generate_report)
        
        # 엣지 추가
        workflow.set_entry_point("detect_event")
        workflow.add_edge("detect_event", "analyze_company_context")
        workflow.add_edge("analyze_company_context", "assess_risk_impact")
        workflow.add_edge("assess_risk_impact", "find_solutions")
        workflow.add_edge("find_solutions", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def detect_event(self, state: SentryAgentState) -> Dict[str, Any]:
        """1단계: 이벤트 감지 및 분류"""
        print(" 1단계: 이벤트 감지 및 분류")
        
        # 샘플 이벤트 (실제로는 뉴스 API, ECOS API 등에서 수집)
        if not state.get("current_event"):
            sample_event = FinancialEvent(
                event_id="event_rate_hike_20250813",
                title="한국은행 기준금리 0.5%p 인상",
                description="한국은행이 물가 안정을 위해 기준금리를 현재 2.5%에서 3.0%로 0.5%포인트 인상했습니다.",
                event_type="interest_rate",
                impact_magnitude=-0.8,
                affected_indicators=["base_rate", "loan_rates", "bond_yields"],
                source="한국은행 금융통화위원회",
                timestamp=datetime.now()
            )
            
            state["current_event"] = asdict(sample_event)
        
        state["processing_stage"] = "event_detected"
        state["messages"].append({
            "role": "system",
            "content": f"이벤트 감지됨: {state['current_event']['title']}"
        })
        
        return state
    
    def analyze_company_context(self, state: SentryAgentState) -> Dict[str, Any]:
        """2단계: 기업 컨텍스트 분석 (LLM 기반)"""
        print(" 2단계: 기업 컨텍스트 분석 (LLM 활용)")
        
        # Enhanced Graph RAG로 기업 종합 분석
        company_name = "대한정밀"  # 기본값, 추후 동적으로 변경 가능
        company_analysis = self.enhanced_graph_rag.analyze_user_company(company_name)
        
        # 프로필 정보 추출
        profile_data = company_analysis.get("profile")
        profile_results = profile_data.results if profile_data and hasattr(profile_data, 'results') else []
        
        # 리스크 노출도 분석
        risk_data = company_analysis.get("risk_analysis")
        risk_results = risk_data.results if risk_data and hasattr(risk_data, 'results') else []
        
        # KB 상품 데이터
        kb_data = company_analysis.get("solution_recommendations", {}).get("kb_products")
        kb_results = kb_data.results if kb_data and hasattr(kb_data, 'results') else []
        
        # 기본 프로필 설정
        if profile_results:
            profile = profile_results[0]
            revenue = profile.get('revenue', 30000000000)
            industry = profile.get('industry', '자동차부품 제조업')
            location = profile.get('location', '경기도')
            employees = profile.get('employees', 120)
            variable_debt = profile.get('variableRateDebt', 8000000000)
        else:
            revenue = 30000000000
            industry = "자동차부품 제조업"
            location = "경기도"
            employees = 120
            variable_debt = 8000000000
        
        # LLM을 활용한 기업 컨텍스트 심화 분석
        if self.llm:
            context_prompt = f"""
당신은 KB국민은행의 수석 중소기업 금융 전문가입니다. 
다음 기업 데이터를 바탕으로 종합적인 기업 프로필과 금융 현황을 분석하여 전문 보고서를 작성하세요.

##  기업 기본 정보
- **기업명**: {company_name}
- **업종**: {industry}  
- **위치**: {location}
- **연매출**: {revenue:,}원 ({revenue//1000000000}억원)
- **직원 수**: {employees}명
- **변동금리 대출**: {variable_debt:,}원 ({variable_debt//1000000000}억원)

##  그래프 데이터베이스 분석 결과

### 리스크 노출도 데이터 ({len(risk_results)}개):
{self._format_risk_data_for_prompt(risk_results)}

### 적합 금융상품 ({len(kb_results)}개):
{self._format_kb_products_for_prompt(kb_results)}

##  분석 요구사항
다음 관점에서 종합적으로 분석하여 JSON 형식으로 출력하세요:

1. **기업 규모 및 위치 분석**: 업종 내 위상, 지역 경제적 특성
2. **재무 건전성 평가**: 매출 대비 부채비율, 변동금리 대출의 위험성
3. **업종별 특성 분석**: 자동차부품업계의 현재 상황과 전망
4. **리스크 프로필 종합**: 거시경제 변수에 대한 노출도 종합 평가
5. **금융 니즈 분석**: 현재 금융 상황에서 필요한 솔루션 유형

출력 형식:
```json
{{
    "company_profile": {{
        "industry_position": "현대자동차 1차 협력사로서 안정적 매출 기반 확보",
        "regional_advantage": "경기도 화성 소재로 주요 고객사 근접성 우수",
        "scale_assessment": "연매출 300억원, 직원 120명 규모의 중견 중소기업"
    }},
    "financial_health": {{
        "debt_ratio_analysis": "변동금리 대출 80억원, 매출 대비 26.7% 수준으로 관리 필요",
        "cash_flow_stability": "자동차부품 수주 기반 안정적 현금흐름 예상",
        "vulnerability_assessment": "금리 인상에 높은 민감도, 헤지 전략 필요"
    }},
    "risk_summary": {{
        "primary_risks": ["기준금리 상승", "원달러 환율 변동", "원자재 가격 상승"],
        "risk_level": "중상 (7.2/10)",
        "urgency": "금리 리스크는 즉시 대응 필요"
    }},
    "financial_needs": {{
        "immediate": "변동금리 고정화",
        "short_term": "운전자금 안정성 확보", 
        "long_term": "사업 확장 자금 준비"
    }}
}}
```

분석을 시작하세요.
"""
            
            try:
                context_response = self.llm.invoke(context_prompt)
                llm_analysis = self._parse_llm_json_response(context_response.content)
                print(" LLM 기반 기업 컨텍스트 분석 완료")
            except Exception as e:
                print(f"️ LLM 분석 실패, 기본 분석 사용: {e}")
                llm_analysis = {"error": "LLM 분석 실패"}
        else:
            llm_analysis = {"error": "LLM 없음"}
        
        state["company_context"] = {
            "company_name": company_name,
            "industry": industry,
            "location": location,
            "revenue": revenue,
            "employees": employees,
            "variable_debt": variable_debt,
            "key_exposures": risk_results,
            "financial_profile": {
                "revenue_range": f"{revenue//1000000000}억원",
                "debt_structure": f"변동금리 대출 {variable_debt//1000000000}억원",
                "export_ratio": "20% (자동차부품)"
            },
            "analysis_data": company_analysis,
            "llm_analysis": llm_analysis
        }
        
        # 분석 결과에 따른 메시지 생성
        analysis_summary = llm_analysis.get("risk_summary", {}).get("risk_level", "분석 중")
        
        state["processing_stage"] = "context_analyzed"
        state["messages"].append({
            "role": "assistant",
            "content": f"{company_name} LLM 기반 종합분석 완료. 리스크 수준: {analysis_summary}, 노출지표: {len(risk_results)}개"
        })
        
        return state
    
    def assess_risk_impact(self, state: SentryAgentState) -> Dict[str, Any]:
        """3단계: 리스크 영향 평가 (LLM 기반)"""
        print("️  3단계: 리스크 영향 평가 (LLM 활용)")
        
        event = state["current_event"]
        company_context = state["company_context"]
        company_name = company_context.get("company_name", "대한정밀")
        
        risks = []
        
        # 금리 인상 영향 분석
        if event["event_type"] == "interest_rate":
            rate_change = abs(event.get("impact_magnitude", 0.5))
            
            # Enhanced Graph RAG로 금리 시뮬레이션 실행
            rate_simulation = self.enhanced_graph_rag.simulate_interest_rate_impact(company_name, rate_change)
            
            if rate_simulation and not rate_simulation.get("error"):
                impact = rate_simulation.get("impact", {})
                
                risk = {
                    "risk_type": "interest_burden_increase",
                    "severity": impact.get("severity", "medium").lower(),
                    "monthly_cost_increase": impact.get("monthly_additional_cost", 0),
                    "annual_cost_increase": impact.get("annual_additional_cost", 0),
                    "cost_to_revenue_ratio": impact.get("cost_to_revenue_ratio", 0),
                    "description": f"변동금리 대출로 인한 월 {impact.get('monthly_additional_cost', 0):,.0f}원 추가 부담",
                    "probability": 0.95,
                    "time_horizon": "immediate",
                    "simulation_data": rate_simulation
                }
                risks.append(risk)
                print(f"    금리 시뮬레이션: 월 {impact.get('monthly_additional_cost', 0):,.0f}원 영향")
            else:
                # 기본 추정치 사용
                risk = {
                    "risk_type": "interest_burden_increase",
                    "severity": "medium",
                    "monthly_cost_increase": 3000000,  # 기본 300만원 추정
                    "description": "금리 인상으로 인한 이자 부담 증가",
                    "probability": 0.9,
                    "time_horizon": "immediate"
                }
                risks.append(risk)
                print("   ️ 금리 시뮬레이션 데이터 없음, 기본 추정치 사용")
        
        # Enhanced Graph RAG에서 리스크 노출도 분석
        key_exposures = company_context.get("key_exposures", [])
        for exposure in key_exposures:
            if exposure.get("exposureLevel") == "HIGH":
                indicator = exposure.get("indicator", "알 수 없는 지표")
                
                # 중복 방지 (금리는 이미 처리)
                if "금리" not in indicator:
                    risk = {
                        "risk_type": f"{indicator.lower()}_exposure",
                        "severity": "high",
                        "description": f"{indicator} 고위험 노출로 인한 잠재적 영향",
                        "indicator_name": indicator,
                        "current_value": exposure.get("currentValue"),
                        "change_rate": exposure.get("changeRate"),
                        "probability": 0.7,
                        "time_horizon": "1-3_months"
                    }
                    risks.append(risk)
        
        # 환율 영향도 확인 (수출기업인 경우)
        export_ratio = company_context["financial_profile"].get("export_ratio", "")
        if "%" in export_ratio:
            exchange_risk = {
                "risk_type": "exchange_rate_exposure",
                "severity": "medium",
                "description": f"{export_ratio}로 원화 변동 시 수출 경쟁력 영향",
                "probability": 0.6,
                "time_horizon": "3-6_months"
            }
            risks.append(exchange_risk)
        
        # LLM을 활용한 리스크 심화 분석
        if self.llm and risks:
            risk_analysis_prompt = f"""
당신은 KB국민은행의 리스크 관리 전문가입니다. 
다음 데이터를 바탕으로 {company_name}의 금융 리스크를 전문적으로 분석하고 평가하세요.

##  기업 현황
- **기업명**: {company_name}
- **업종**: {company_context.get('industry')}
- **연매출**: {company_context.get('revenue', 0):,}원
- **변동금리 대출**: {company_context.get('variable_debt', 0):,}원
- **LLM 기업분석**: {company_context.get('llm_analysis', {})}

##  감지된 이벤트
- **이벤트**: {event['title']}
- **유형**: {event['event_type']}
- **영향도**: {event['impact_magnitude']}

##  식별된 초기 리스크
{self._format_risks_for_llm_analysis(risks)}

##  리스크 분석 요구사항
다음 관점에서 각 리스크를 전문적으로 재평가하고 새로운 리스크를 발견하여 JSON으로 출력하세요:

1. **정량적 영향 분석**: 구체적 금액, 비율, 시나리오별 손실 추정
2. **시간적 전개**: 단기/중기/장기별 영향 양상과 임계점
3. **업종 특수성**: 자동차부품업계 고유의 리스크 요인
4. **복합 리스크**: 여러 리스크가 동시 발생 시 증폭 효과
5. **대응 시급성**: 즉시/단기/중장기 대응이 필요한 리스크 분류

출력 형식:
```json
{{
    "enhanced_risks": [
        {{
            "risk_id": "interest_rate_spike",
            "risk_name": "급격한 기준금리 인상",
            "severity_score": 8.5,
            "monthly_impact": 5333333,
            "annual_impact": 64000000,
            "probability": 0.85,
            "time_horizon": "immediate",
            "urgency_level": "critical",
            "business_impact": "월 533만원 이자비용 증가로 영업이익 20% 감소",
            "scenario_analysis": {{
                "best_case": "월 400만원 부담 (0.4% 인상)",
                "worst_case": "월 800만원 부담 (1.0% 인상)",
                "stress_test": "금리 2% 인상시 연간 1.6억원 추가 부담"
            }},
            "mitigation_urgency": "2주 내 고정금리 전환 필요"
        }}
    ],
    "risk_interaction": {{
        "compound_effect": "금리인상+환율상승 동시 발생시 월 750만원 추가 부담",
        "correlation_analysis": "기준금리와 원달러환율 0.7 상관관계",
        "amplification_factor": 1.4
    }},
    "overall_assessment": {{
        "total_risk_score": 7.8,
        "financial_stress_level": "high",
        "survival_risk": "low",
        "action_timeline": "2주 내 긴급 대응, 1개월 내 구조적 개선"
    }}
}}
```

세밀하고 실무적인 리스크 분석을 시작하세요.
"""
            
            try:
                risk_response = self.llm.invoke(risk_analysis_prompt)
                llm_risk_analysis = self._parse_llm_json_response(risk_response.content)
                print(" LLM 기반 리스크 심화 분석 완료")
                
                # LLM 분석 결과로 기존 리스크 업데이트
                if "enhanced_risks" in llm_risk_analysis:
                    enhanced_risks = llm_risk_analysis["enhanced_risks"]
                    # 기존 리스크와 LLM 향상 리스크를 병합
                    for enhanced_risk in enhanced_risks:
                        # 기존 리스크 업데이트 또는 새로운 리스크 추가
                        existing_risk = next((r for r in risks if r["risk_type"] == enhanced_risk.get("risk_id", "")), None)
                        if existing_risk:
                            existing_risk.update({
                                "llm_severity_score": enhanced_risk.get("severity_score"),
                                "llm_business_impact": enhanced_risk.get("business_impact"),
                                "scenario_analysis": enhanced_risk.get("scenario_analysis"),
                                "mitigation_urgency": enhanced_risk.get("mitigation_urgency")
                            })
                        else:
                            # 새로운 리스크 추가
                            risks.append({
                                "risk_type": enhanced_risk.get("risk_id", "unknown"),
                                "risk_name": enhanced_risk.get("risk_name", "신규 리스크"),
                                "severity": "high" if enhanced_risk.get("severity_score", 0) > 7 else "medium",
                                "monthly_cost_increase": enhanced_risk.get("monthly_impact", 0),
                                "probability": enhanced_risk.get("probability", 0.5),
                                "time_horizon": enhanced_risk.get("time_horizon", "unknown"),
                                "llm_analysis": enhanced_risk
                            })
                        
            except Exception as e:
                print(f"️ LLM 리스크 분석 실패: {e}")
                llm_risk_analysis = {"error": "LLM 리스크 분석 실패"}
        else:
            llm_risk_analysis = {"error": "LLM 없음 또는 리스크 없음"}
        
        # 리스크 영향 분석 요약 (LLM 결과 반영)
        state["identified_risks"] = risks
        state["impact_analysis"] = {
            "total_risks": len(risks),
            "critical_risks": len([r for r in risks if r.get("severity") == "high"]),
            "high_risks": len([r for r in risks if r.get("severity") == "high"]),
            "medium_risks": len([r for r in risks if r.get("severity") == "medium"]),
            "estimated_monthly_impact": sum([r.get("monthly_cost_increase", 0) for r in risks]),
            "max_probability": max([r.get("probability", 0) for r in risks]) if risks else 0,
            "immediate_risks": len([r for r in risks if r.get("time_horizon") == "immediate"]),
            "llm_risk_analysis": llm_risk_analysis,
            "overall_risk_score": llm_risk_analysis.get("overall_assessment", {}).get("total_risk_score", 5.0),
            "financial_stress_level": llm_risk_analysis.get("overall_assessment", {}).get("financial_stress_level", "medium")
        }
        
        stress_level = state["impact_analysis"]["financial_stress_level"]
        risk_score = state["impact_analysis"]["overall_risk_score"]
        
        state["processing_stage"] = "risks_assessed"
        state["messages"].append({
            "role": "assistant",
            "content": f"LLM 기반 리스크 평가 완료. {len(risks)}개 위험요소 (고위험: {state['impact_analysis']['high_risks']}개), 종합점수: {risk_score}/10, 스트레스: {stress_level}"
        })
        
        return state
    
    def find_solutions(self, state: SentryAgentState) -> Dict[str, Any]:
        """4단계: 해결책 탐색"""
        print(" 4단계: 해결책 탐색")
        
        risks = state["identified_risks"]
        company_context = state["company_context"]
        company_name = company_context.get("company_name", "대한정밀")
        
        solutions = []
        
        # Enhanced Graph RAG로 종합적인 솔루션 탐색
        analysis_data = company_context.get("analysis_data", {})
        solution_recommendations = analysis_data.get("solution_recommendations", {})
        
        # KB 금융상품 추천
        kb_products_data = solution_recommendations.get("kb_products")
        if kb_products_data and hasattr(kb_products_data, 'results'):
            kb_products = kb_products_data.results[:3]  # 상위 3개
            
            for product in kb_products:
                # 리스크 유형에 맞는 예상 절감 효과 계산
                estimated_saving = 0
                for risk in risks:
                    if risk["risk_type"] == "interest_burden_increase" and risk.get("monthly_cost_increase", 0) > 0:
                        estimated_saving = risk["monthly_cost_increase"] * 0.3  # 30% 절감 가정
                        break
                
                solution = {
                    "solution_type": "kb_financial_product",
                    "product_name": product.get("productName", "KB 금융상품"),
                    "product_type": product.get("productType", "운전자금"),
                    "interest_rate": product.get("interestRate", "우대금리"),
                    "eligibility_score": product.get("eligibilityScore", 0.8),
                    "expected_benefit": product.get("expectedBenefit", "금리 우대 및 이자 부담 경감"),
                    "urgency": product.get("urgency", "MEDIUM"),
                    "implementation_timeline": "1-2주",
                    "estimated_saving": estimated_saving,
                    "risk_coverage": ["interest_burden_increase"]
                }
                solutions.append(solution)
                print(f"    KB 상품: {solution['product_name']}")
        
        # 정부 정책 지원 추천  
        policy_opportunities_data = solution_recommendations.get("policy_opportunities")
        if policy_opportunities_data and hasattr(policy_opportunities_data, 'results'):
            policies = policy_opportunities_data.results[:2]  # 상위 2개
            
            for policy in policies:
                solution = {
                    "solution_type": "government_policy",
                    "policy_name": policy.get("policyName", "정부지원정책"),
                    "issuing_org": policy.get("issuingOrg", "정부기관"),
                    "support_field": policy.get("supportField", "일반지원"),
                    "eligibility_score": policy.get("eligibilityScore", 0.75),
                    "expected_benefit": "정부 보조금 및 이차보전 지원",
                    "action_required": policy.get("actionRequired", "신청 검토"),
                    "implementation_timeline": "2-4주",
                    "estimated_saving": 1000000,  # 월 100만원 추정
                    "risk_coverage": ["interest_burden_increase", "general_financial_burden"]
                }
                solutions.append(solution)
                print(f"   ️ 정부정책: {solution['policy_name']}")
        
        # 실시간 추천 시스템 활용
        realtime_recommendations = self.enhanced_graph_rag.get_real_time_recommendations(company_name)
        for rec in realtime_recommendations[:2]:  # 상위 2개
            solution = {
                "solution_type": "realtime_recommendation",
                "product_name": rec.get("product_name", "추천상품"),
                "product_type": rec.get("product_type", "운전자금"),
                "eligibility_score": rec.get("eligibility_score", 0.8),
                "expected_benefit": rec.get("expected_benefit", "금융비용 절감"),
                "recommendation_reason": rec.get("recommendation_reason", "실시간 추천"),
                "implementation_timeline": "즉시",
                "estimated_saving": 500000,  # 월 50만원 추정
                "risk_coverage": ["interest_burden_increase"]
            }
            solutions.append(solution)
            print(f"    실시간 추천: {solution['product_name']}")
        
        # 리스크별 추가 솔루션
        for risk in risks:
            if risk["risk_type"] == "exchange_rate_exposure":
                hedge_solution = {
                    "solution_type": "financial_hedge",
                    "product_name": "KB 환율 헤지 상품",
                    "expected_benefit": "환율 변동 리스크 완화",
                    "implementation_timeline": "즉시",
                    "estimated_saving": 0,  # 보험성 상품
                    "risk_coverage": ["exchange_rate_exposure"]
                }
                solutions.append(hedge_solution)
                print(f"   ️ 헤지상품: {hedge_solution['product_name']}")
            
            elif "exposure" in risk["risk_type"] and risk["risk_type"] != "exchange_rate_exposure":
                monitoring_solution = {
                    "solution_type": "risk_monitoring",
                    "product_name": f"KB {risk.get('indicator_name', '거시지표')} 모니터링 서비스",
                    "expected_benefit": "리스크 조기 경보 및 대응 지원",
                    "implementation_timeline": "1주",
                    "estimated_saving": 0,  # 예방 효과
                    "risk_coverage": [risk["risk_type"]]
                }
                solutions.append(monitoring_solution)
        
        # 솔루션 우선순위 정렬 (절감 효과 + 적합도 기준)
        solutions.sort(key=lambda x: (x.get("estimated_saving", 0) + x.get("eligibility_score", 0) * 1000000), reverse=True)
        
        state["found_solutions"] = solutions
        state["processing_stage"] = "solutions_found"
        state["messages"].append({
            "role": "assistant",
            "content": f"해결책 탐색 완료. {len(solutions)}개 솔루션 발견 (KB상품, 정부정책, 헤지상품 포함)"
        })
        
        return state
    
    def generate_report(self, state: SentryAgentState) -> Dict[str, Any]:
        """5단계: 최종 보고서 생성"""
        print(" 5단계: 최종 보고서 생성")
        
        event = state["current_event"]
        company = state["company_context"]
        risks = state["identified_risks"]
        solutions = state["found_solutions"]
        impact = state["impact_analysis"]
        
        # 보고서 생성
        report_sections = []
        
        # 1. 요약
        report_sections.append("##  긴급 금융 리스크 알림")
        report_sections.append(f"**이벤트**: {event['title']}")
        report_sections.append(f"**대상 기업**: {company['company_name']} ({company['industry']})")
        report_sections.append(f"**영향도**: {event['impact_magnitude']:.1f} (심각)")
        
        # 2. 리스크 분석
        report_sections.append("\n## ️ 식별된 리스크")
        for i, risk in enumerate(risks, 1):
            cost_info = ""
            if risk.get("monthly_cost_increase"):
                cost_info = f" (월 {risk['monthly_cost_increase']:,.0f}원 추가 부담)"
            report_sections.append(f"{i}. **{risk['risk_type']}** - {risk['severity'].upper()}{cost_info}")
            report_sections.append(f"   - {risk['description']}")
        
        # 3. 추천 솔루션
        report_sections.append("\n##  추천 해결책")
        for i, solution in enumerate(solutions, 1):
            saving_info = ""
            if solution.get("estimated_saving", 0) > 0:
                saving_info = f" (월 {solution['estimated_saving']:,.0f}원 절감 예상)"
            
            # 상품명 처리 (product_name 또는 policy_name)
            product_name = solution.get('product_name') or solution.get('policy_name', 'KB 금융솔루션')
            
            report_sections.append(f"{i}. **{product_name}**{saving_info}")
            report_sections.append(f"   - {solution['expected_benefit']}")
            if solution.get("eligibility_score"):
                report_sections.append(f"   - 적합도: {solution['eligibility_score']:.1f}/1.0")
            if solution.get("implementation_timeline"):
                report_sections.append(f"   - 실행시간: {solution['implementation_timeline']}")
        
        # 4. 행동 권고
        report_sections.append("\n##  즉시 행동 권고")
        report_sections.append("1. **우선순위 1**: 정책자금 대출 신청으로 이자 부담 경감")
        report_sections.append("2. **우선순위 2**: KB 수출기업 우대대출 검토")
        report_sections.append("3. **모니터링**: 추가 금리 인상 시나리오 대비")
        
        final_report = "\n".join(report_sections)
        
        # 신뢰도 계산
        confidence = min(1.0, 
            len(risks) * 0.2 + 
            len(solutions) * 0.3 + 
            (impact["total_risks"] > 0) * 0.3
        )
        
        state["final_report"] = final_report
        state["confidence_score"] = confidence
        state["processing_stage"] = "report_generated"
        
        state["messages"].append({
            "role": "assistant",
            "content": "최종 보고서 생성 완료"
        })
        
        return state
    
    def process_event(self, event_data: Optional[Dict] = None) -> Dict[str, Any]:
        """이벤트 처리 메인 함수"""
        print(" KB Fortress AI 파수꾼 에이전트 시작")
        
        # 초기 상태 설정
        initial_state = SentryAgentState(
            messages=[{"role": "system", "content": "KB Fortress AI 파수꾼 에이전트 시작"}],
            current_event=event_data or {},
            company_context={},
            identified_risks=[],
            impact_analysis={},
            found_solutions=[],
            final_report="",
            processing_stage="initialized",
            confidence_score=0.0
        )
        
        try:
            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            print("\n" + "="*50)
            print(" KB Fortress AI 분석 완료")
            print("="*50)
            print(result["final_report"])
            print("="*50)
            print(f" 신뢰도: {result['confidence_score']:.1%}")
            
            return result
            
        except Exception as e:
            print(f" 에이전트 처리 오류: {e}")
            return {"error": str(e)}
        
        finally:
            self.cleanup()
    
    def save_analysis_result(self, result: Dict[str, Any], output_dir: str = "data/agent_results"):
        """분석 결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_dir, f"sentry_analysis_{timestamp}.json")
        
        # datetime 객체들을 문자열로 변환
        serializable_result = json.loads(json.dumps(result, default=str))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f" 분석 결과 저장: {file_path}")
        return file_path
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'enhanced_graph_rag') and self.enhanced_graph_rag:
            self.enhanced_graph_rag.neo4j_manager.close()
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """Sentry Agent 테스트"""
    print("=== KB Fortress AI Sentry Agent 테스트 ===")
    
    try:
        agent = SentryAgent()
        
        # 이벤트 처리
        result = agent.process_event()
        
        # 결과 저장
        agent.save_analysis_result(result)
        
        print("\n Sentry Agent 테스트 완료!")
        
    except Exception as e:
        print(f" Sentry Agent 오류: {e}")

if __name__ == "__main__":
    main()