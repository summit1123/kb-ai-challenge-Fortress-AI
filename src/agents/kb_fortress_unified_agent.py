#!/usr/bin/env python3
"""
KB Fortress AI - Unified LangGraph Agent
모든 기능을 통합한 단일 LangGraph 워크플로우
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional, Annotated
from typing_extensions import TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
from neo4j_manager import Neo4jManager

# 통합 상태 정의
class KBFortressState(TypedDict):
    """KB Fortress AI 통합 상태"""
    messages: Annotated[list, add_messages]           # 사용자 메시지
    task_type: str                                    # 작업 유형 (register/analyze/query)
    company_data: Dict[str, Any]                      # 기업 정보
    user_company_node_id: Optional[str]               # 생성된 UserCompany 노드 ID
    cypher_query: str                                 # 생성된 Cypher 쿼리
    db_results: list                                  # DB 실행 결과
    analysis_results: Dict[str, Any]                  # 분석 결과
    risk_assessment: Dict[str, Any]                   # 리스크 평가
    recommendations: List[Dict[str, Any]]             # 추천사항
    final_report: str                                 # 최종 보고서
    error_history: list                               # 오류 이력
    correction_attempts: int                          # 수정 시도 횟수
    current_stage: str                                # 현재 단계
    confidence_score: float                           # 신뢰도 점수
    section_explanations: Dict[str, str]              # 섹션별 AI 설명

class KBFortressUnifiedAgent:
    """KB Fortress AI 통합 에이전트 (All-in-One LangGraph)"""
    
    def __init__(self):
        # Google Gemini 초기화
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.1
        )
        
        # Neo4j 연결
        os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
        os.environ['NEO4J_USER'] = os.getenv('NEO4J_USER', 'neo4j')
        os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
        self.neo4j_manager = Neo4jManager()
        
        # KB Graph 스키마
        self.kb_schema = self._get_kb_schema()
        
        # LangGraph 워크플로우 구성
        self.workflow = self._build_unified_workflow()
        
        print(" KB Fortress AI 통합 에이전트 초기화 완료")
    
    def _get_kb_schema(self) -> str:
        """KB Fortress AI 그래프 스키마"""
        return """
Node Labels:
UserCompany {nodeId: STRING, companyName: STRING, industryDescription: STRING, location: STRING, revenue: INTEGER, employeeCount: INTEGER, debtAmount: INTEGER, variableRateDebt: INTEGER, exportAmount: INTEGER, createdAt: DATETIME}
ReferenceCompany {companyName: STRING, sector: STRING, revenue: INTEGER, industryCode: STRING, location: STRING}
KB_Product {productName: STRING, productType: STRING, interestRate: STRING, description: STRING}
Policy {policyName: STRING, issuingOrg: STRING, supportField: STRING, eligibilityText: STRING}
MacroIndicator {indicatorName: STRING, value: FLOAT, changeRate: FLOAT, unit: STRING, lastUpdated: DATETIME}
NewsArticle {title: STRING, publisher: STRING, publishDate: DATETIME, category: STRING, content: STRING}

Relationship Types:
IS_EXPOSED_TO {exposureLevel: STRING, rationale: STRING, riskType: STRING}
IS_ELIGIBLE_FOR {eligibilityScore: FLOAT, urgency: STRING, expectedBenefit: STRING, actionRequired: STRING}
SIMILAR_TO {similarityScore: FLOAT, comparisonBasis: STRING}
HAS_IMPACT_ON {impactScore: FLOAT, impactDirection: STRING, rationale: STRING}
COMPETES_WITH {competitionLevel: STRING, marketOverlap: FLOAT}
"""
    
    def _build_unified_workflow(self) -> StateGraph:
        """통합 LangGraph 워크플로우 구성"""
        workflow = StateGraph(KBFortressState)
        
        # 노드 추가
        workflow.add_node("route_task", self.route_task)
        workflow.add_node("register_company", self.register_company)
        workflow.add_node("analyze_risk", self.analyze_risk)
        workflow.add_node("generate_cypher", self.generate_cypher)
        workflow.add_node("execute_cypher", self.execute_cypher)
        workflow.add_node("correct_cypher", self.correct_cypher)
        workflow.add_node("find_solutions", self.find_solutions)
        workflow.add_node("generate_report", self.generate_report)
        
        # 엔트리 포인트
        workflow.set_entry_point("route_task")
        
        # 작업 유형별 라우팅
        workflow.add_conditional_edges(
            "route_task",
            self.route_by_task_type,
            {
                "register": "register_company",
                "query": "generate_cypher",
                "analyze": "analyze_risk"
            }
        )
        
        # 기업 등록 플로우
        workflow.add_edge("register_company", "analyze_risk")
        workflow.add_edge("analyze_risk", "find_solutions")
        
        # 쿼리 플로우 (피드백 루프)
        workflow.add_edge("generate_cypher", "execute_cypher")
        workflow.add_conditional_edges(
            "execute_cypher",
            self.route_correction,
            {
                "correct": "correct_cypher",
                "continue": "find_solutions"
            }
        )
        workflow.add_edge("correct_cypher", "execute_cypher")
        
        # 최종 보고서 생성
        workflow.add_edge("find_solutions", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def route_task(self, state: KBFortressState) -> Dict[str, Any]:
        """작업 유형 라우팅"""
        print(" 작업 유형 분석 중...")
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        # 기업 등록 요청인지 확인
        if any(keyword in last_message for keyword in ["등록", "회사명:", "업종:", "매출:", "직원"]):
            task_type = "register"
            # 기업 정보 추출
            company_data = self._extract_company_info(last_message)
        # 분석 요청인지 확인  
        elif any(keyword in last_message for keyword in ["분석", "리스크", "위험", "진단"]):
            task_type = "analyze"
            company_data = {"analysis_request": True}
            # 분석 요청에서도 회사명 추출 시도
            import re
            match = re.search(r'([가-힣a-zA-Z0-9\-]+)\s*(?:회사|기업|의)', last_message)
            if match:
                company_data["company_name"] = match.group(1).strip()
                print(f"분석 요청에서 추출한 회사명: {company_data['company_name']}")
        # 일반 질의
        else:
            task_type = "query"
            company_data = {}
        
        print(f" 작업 유형: {task_type}")
        
        return {
            "task_type": task_type,
            "company_data": company_data,
            "current_stage": "routing"
        }
    
    def route_by_task_type(self, state: KBFortressState) -> str:
        """작업 유형별 라우팅 결정"""
        task_type = state.get("task_type", "query")
        print(f" 라우팅: {task_type}")
        return task_type
    
    def register_company(self, state: KBFortressState) -> Dict[str, Any]:
        """기업 등록 (UserCompany 노드 생성)"""
        print(" 기업 등록 시작...")
        
        company_data = state.get("company_data", {})
        company_name = company_data.get("company_name", "테스트기업")
        
        # UserCompany 생성 쿼리
        create_query = f"""
        CREATE (u:UserCompany {{
            nodeId: '{company_name.replace(' ', '_').lower()}_' + toString(timestamp()),
            companyName: $company_name,
            industryDescription: $industry,
            location: $location,
            revenue: $revenue,
            employeeCount: $employees,
            debtAmount: $debt,
            variableRateDebt: $variable_debt,
            exportAmount: $export_amount,
            createdAt: datetime()
        }})
        RETURN u.nodeId as nodeId
        """
        
        parameters = {
            'company_name': company_name,
            'industry': company_data.get("industry", "제조업"),
            'location': company_data.get("location", "경기도"),
            'revenue': company_data.get("revenue", 100),
            'employees': company_data.get("employees", 50),
            'debt': company_data.get("debt", 50),
            'variable_debt': int(company_data.get("debt", 50) * 0.7),
            'export_amount': int(company_data.get("revenue", 100) * 0.3)
        }
        
        try:
            results = self.neo4j_manager.execute_query(create_query, parameters)
            node_id = results[0]['nodeId'] if results else None
            
            if node_id:
                print(f" UserCompany 노드 생성 완료: {node_id}")
                
                # 관계 생성 (기업 데이터 전달)
                relationship_count = self._create_all_relationships(company_name, company_data)
                
                return {
                    "user_company_node_id": node_id,
                    "current_stage": "company_registered",
                    "company_data": {**company_data, "node_id": node_id, "relationships_created": relationship_count},
                    "company_name": company_name  # 직접 company_name 추가
                }
            else:
                return {
                    "error_history": [{"stage": "register", "error": "노드 생성 실패"}],
                    "current_stage": "registration_failed"
                }
                
        except Exception as e:
            print(f" 기업 등록 실패: {e}")
            return {
                "error_history": [{"stage": "register", "error": str(e)}],
                "current_stage": "registration_failed"
            }
    
    def analyze_risk(self, state: KBFortressState) -> Dict[str, Any]:
        """리스크 분석 - Text-to-Cypher 기반 동적 쿼리"""
        print(" 리스크 분석 시작...")
        
        # state에 직접 company_name이 있는 경우
        company_name = state.get("company_name")
        
        # company_data 가져오기
        company_data = state.get("company_data", {})
        
        # company_data에서 찾기
        if not company_name:
            company_name = company_data.get("company_name")
        
        # 여전히 없으면 메시지에서 추출 시도
        if not company_name and state.get("messages"):
            user_message = state["messages"][0].content
            # 메시지에서 회사명 추출
            import re
            # "kb-fortress 회사의" 또는 "대한정밀의" 패턴 매칭
            match = re.search(r'([가-힣a-zA-Z0-9\-]+)\s*(?:회사|기업|의)', user_message)
            if match:
                company_name = match.group(1).strip()
                print(f"메시지에서 추출한 회사명: {company_name}")
        
        # 여전히 없으면 기본값
        if not company_name:
            company_name = "테스트기업"
        
        # company_data에 기본값 추가 (없는 경우)
        if "variable_debt_ratio" not in company_data:
            company_data["variable_debt_ratio"] = 70
        if "export_ratio" not in company_data:
            company_data["export_ratio"] = 20
        
        # 분석을 위한 자연어 질문들
        analysis_questions = [
            f"{company_name}이 노출된 거시경제지표와 노출 수준을 분석해주세요. 환율, 금리 등에 대한 노출도와 그 이유를 포함해주세요.",
            f"{company_name}에게 적합한 KB 금융상품을 추천해주세요. 각 상품의 적합도 점수와 기대효과를 포함해주세요.",
            f"{company_name}이 활용할 수 있는 정부 정책이나 지원사업을 찾아주세요. 정책명, 지원분야, 발행기관을 포함해주세요.",
            f"{company_name}에 영향을 미치는 최근 뉴스를 분석해주세요. 뉴스 제목, 날짜, 영향도와 그 이유를 포함해주세요.",
            f"{company_name}과 유사한 기업들을 찾아주세요. 비교 기준과 유사도를 포함해주세요."
        ]
        
        analysis_results = {
            "macro_exposure": [],
            "kb_products": [],
            "policies": [],
            "news_impacts": [],
            "similar_companies": []
        }
        graph_paths = {}
        
        # 각 질문에 대해 Text-to-Cypher로 쿼리 생성 및 실행
        for idx, question in enumerate(analysis_questions):
            analysis_type = list(analysis_results.keys())[idx]
            print(f"\n 분석 중: {analysis_type}")
            
            # Text-to-Cypher로 쿼리 생성
            cypher_state = KBFortressState(
                messages=[HumanMessage(content=question)],
                task_type="query",
                company_data=company_data,
                current_stage="cypher_generation"
            )
            
            # Cypher 쿼리 생성
            cypher_result = self.generate_cypher(cypher_state)
            cypher_query = cypher_result.get("cypher_query", "")
            
            # 쿼리 실행
            if cypher_query and cypher_query != "RETURN '쿼리 생성 실패' as message":
                try:
                    results = self.neo4j_manager.execute_query(cypher_query)
                    analysis_results[analysis_type] = results
                    
                    # 그래프 경로 설명 생성
                    if results:
                        graph_paths[analysis_type] = self._generate_path_explanation(question, cypher_query, results)
                    
                    print(f" {analysis_type}: {len(results)}개 결과")
                except Exception as e:
                    print(f" {analysis_type} 쿼리 실행 실패: {e}")
                    # 오류 시 수정 시도
                    correction_state = {
                        **cypher_state,
                        "cypher_query": cypher_query,
                        "db_results": [],
                        "error_history": [{"query": cypher_query, "error": str(e)}],
                        "correction_attempts": 1
                    }
                    
                    corrected = self.correct_cypher(correction_state)
                    corrected_query = corrected.get("cypher_query", "")
                    
                    if corrected_query and corrected_query != cypher_query:
                        try:
                            results = self.neo4j_manager.execute_query(corrected_query)
                            analysis_results[analysis_type] = results
                            print(f" {analysis_type}: 수정 후 {len(results)}개 결과")
                        except:
                            analysis_results[analysis_type] = []
        
        #  원자재 분석 추가
        raw_material_analysis = self._analyze_raw_material_dependencies(company_name)
        
        # 구조화된 리스크 평가 생성
        risk_assessment = self._generate_structured_risk_assessment(
            company_name, 
            analysis_results, 
            graph_paths,
            company_data
        )
        
        # 원자재 분석 결과를 analysis_results에 통합
        analysis_results.update({
            "raw_material_dependencies": raw_material_analysis["dependencies"],
            "raw_material_price_changes": raw_material_analysis["price_changes"],
            "raw_material_risks": raw_material_analysis["risk_factors"],
            "raw_material_cost_impact": raw_material_analysis["cost_impact"],
            "supply_chain_risks": raw_material_analysis["supply_chain_risks"]
        })
        
        # 각 섹션별 LLM 설명 생성
        print(f" 섹션 설명 생성 시작 - 회사명: {company_name}")
        print(f" 전달되는 데이터: risk_assessment={risk_assessment}, company_data={company_data}")
        section_explanations = self._generate_section_explanations(
            company_name, analysis_results, risk_assessment, company_data
        )
        print(f" 생성된 섹션 설명: {section_explanations}")
        
        print(f" 분석 완료 - 섹션 설명: {section_explanations}")
        
        # State에 명시적으로 업데이트
        state["analysis_results"] = analysis_results
        state["risk_assessment"] = risk_assessment
        state["section_explanations"] = section_explanations
        state["graph_paths"] = graph_paths
        state["current_stage"] = "risk_analyzed"
        state["company_name"] = company_name
        
        print(f" analyze_risk 반환값: section_explanations = {section_explanations}")
        
        # 전체 state 반환
        return state
    
    def generate_cypher(self, state: KBFortressState) -> Dict[str, Any]:
        """자연어 질문을 Cypher 쿼리로 변환"""
        print(" Cypher 쿼리 생성...")
        
        user_question = state["messages"][-1].content if state["messages"] else ""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 KB Fortress AI의 Cypher 쿼리 전문가입니다.
사용자 질문을 정확한 Cypher 쿼리로 변환하세요.

KB Graph 스키마:
{schema}

쿼리 가이드라인:
1. UserCompany 노드를 기준점으로 사용
2. KB 상품 조회: MATCH (company:UserCompany)-[r:IS_ELIGIBLE_FOR]->(product:KB_Product) RETURN product.productName as product, r.eligibilityScore as score, product.description as description
3. 정책 조회: MATCH (company:UserCompany)-[r:IS_ELIGIBLE_FOR]->(policy:Policy) RETURN policy.policyName as policy, policy.issuingOrg as organization, r.actionRequired as action
4. 거시지표 노출: MATCH (company:UserCompany)-[r:IS_EXPOSED_TO]->(indicator:MacroIndicator) RETURN indicator.indicatorName as indicator, r.exposureLevel as level, r.rationale as reason
5. 뉴스 영향: MATCH (news:NewsArticle)-[r:HAS_IMPACT_ON]->(company:UserCompany) RETURN news.title as news, news.publishDate as date, r.impactScore as impact, r.rationale as reason
6. 유사기업: MATCH (company:UserCompany)-[r:SIMILAR_TO]->(similar:ReferenceCompany) RETURN similar.companyName as company, r.similarityScore as similarity, r.comparisonBasis as basis

중요 규칙:
- 반드시 회사명으로 UserCompany 찾기: WHERE company.companyName = "실제회사명"
- 회사명은 대소문자와 형식을 정확히 유지하세요 (예: kb-fortress는 그대로 kb-fortress로 사용)
- 회사명을 임의로 변경하지 마세요 (예: kb-fortress를 KB Fortress로 변경하지 마세요)
- 적절한 관계와 노드 라벨 사용
- LIMIT 10 추가
- ORDER BY로 점수 내림차순 정렬"""),
            ("user", "질문: {question}\n\nCypher 쿼리:")
        ])
        
        try:
            response = self.llm.invoke(
                prompt.format_messages(schema=self.kb_schema, question=user_question)
            )
            
            cypher_query = response.content.strip().replace('```cypher\n', '').replace('\n```', '').replace('```', '')
            print(f"생성된 쿼리: {cypher_query}")
            
            return {
                "cypher_query": cypher_query,
                "current_stage": "cypher_generated"
            }
            
        except Exception as e:
            print(f" Cypher 생성 실패: {e}")
            return {
                "error_history": [{"stage": "generate_cypher", "error": str(e)}],
                "current_stage": "cypher_failed"
            }
    
    def execute_cypher(self, state: KBFortressState) -> Dict[str, Any]:
        """Cypher 쿼리 실행"""
        print(" Cypher 쿼리 실행...")
        
        cypher_query = state.get("cypher_query", "")
        if not cypher_query:
            return {"db_results": [], "current_stage": "execution_failed"}
        
        try:
            results = self.neo4j_manager.execute_query(cypher_query)
            print(f" 쿼리 실행 성공: {len(results)}개 결과")
            
            return {
                "db_results": results,
                "current_stage": "cypher_executed"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f" 쿼리 실행 실패: {error_msg}")
            
            error_history = state.get("error_history", [])
            error_history.append({
                "stage": "execute",
                "query": cypher_query,
                "error": error_msg
            })
            
            return {
                "db_results": [error_msg],
                "error_history": error_history,
                "current_stage": "execution_failed"
            }
    
    def route_correction(self, state: KBFortressState) -> str:
        """오류 수정 라우팅"""
        db_results = state.get("db_results", [])
        correction_attempts = state.get("correction_attempts", 0)
        
        if isinstance(db_results, list) and len(db_results) >= 0 and not isinstance(db_results[0] if db_results else None, str):
            return "continue"  # 성공
        elif correction_attempts < 2:
            return "correct"   # 수정 시도
        else:
            return "continue"  # 포기하고 계속
    
    def correct_cypher(self, state: KBFortressState) -> Dict[str, Any]:
        """Cypher 쿼리 자동 수정"""
        print(" Cypher 쿼리 수정...")
        
        failed_query = state.get("cypher_query", "")
        error_history = state.get("error_history", [])
        correction_attempts = state.get("correction_attempts", 0) + 1
        
        latest_error = error_history[-1].get("error", "") if error_history else ""
        user_question = state["messages"][0].content if state["messages"] else ""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Cypher 쿼리 오류를 수정하는 전문가입니다.

스키마: {schema}

수정 가이드라인:
1. 노드 라벨과 속성명 정확히 맞추기
2. 문법 오류 수정
3. 존재하지 않는 속성 제거

수정된 Cypher 쿼리만 반환하세요."""),
            ("user", """사용자 질문: {question}
실패한 쿼리: {failed_query}
오류: {error}

수정된 쿼리:""")
        ])
        
        try:
            response = self.llm.invoke(
                prompt.format_messages(
                    schema=self.kb_schema,
                    question=user_question,
                    failed_query=failed_query,
                    error=latest_error
                )
            )
            
            corrected_query = response.content.strip().replace('```cypher\n', '').replace('\n```', '').replace('```', '')
            print(f"수정된 쿼리: {corrected_query}")
            
            return {
                "cypher_query": corrected_query,
                "correction_attempts": correction_attempts,
                "current_stage": "cypher_corrected"
            }
            
        except Exception as e:
            print(f" 쿼리 수정 실패: {e}")
            return {
                "cypher_query": "RETURN '쿼리 수정 실패' as message",
                "correction_attempts": correction_attempts,
                "current_stage": "correction_failed"
            }
    
    def find_solutions(self, state: KBFortressState) -> Dict[str, Any]:
        """솔루션 탐색 및 추천"""
        print(" 솔루션 탐색...")
        
        analysis_results = state.get("analysis_results", {})
        risk_assessment = state.get("risk_assessment", {})
        db_results = state.get("db_results", [])
        section_explanations = state.get("section_explanations", {})
        
        # LLM을 사용한 솔루션 생성
        recommendations = self._generate_recommendations(analysis_results, risk_assessment, db_results)
        
        print(f" find_solutions: section_explanations 전달 = {section_explanations}")
        
        # state 업데이트
        state["recommendations"] = recommendations
        state["current_stage"] = "solutions_found"
        # section_explanations는 이미 state에 있음
        
        return state
    
    def generate_report(self, state: KBFortressState) -> Dict[str, Any]:
        """최종 보고서 생성"""
        print(" 최종 보고서 생성...")
        
        user_question = state["messages"][0].content if state["messages"] else ""
        task_type = state.get("task_type", "query")
        company_data = state.get("company_data", {})
        analysis_results = state.get("analysis_results", {})
        risk_assessment = state.get("risk_assessment", {})
        recommendations = state.get("recommendations", [])
        db_results = state.get("db_results", [])
        
        # 보고서 생성 프롬프트
        report_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 KB국민은행의 수석 중소기업 금융 전문가입니다.
KB Fortress AI 분석 결과를 바탕으로 전문적이고 실행 가능한 보고서를 작성하세요.

보고서 구조:
1.  핵심 요약
2.  분석 결과
3. ️ 주요 리스크
4.  추천 솔루션
5.  실행 계획

한국어로 친근하고 전문적으로 작성하세요."""),
            
            ("user", """작업 유형: {task_type}
사용자 질문: {question}
기업 정보: {company_data}
분석 결과: {analysis_results}
리스크 평가: {risk_assessment}
추천사항: {recommendations}
DB 결과: {db_results}

위 내용을 종합하여 전문적인 보고서를 작성해주세요.""")
        ])
        
        try:
            response = self.llm.invoke(
                report_prompt.format_messages(
                    task_type=task_type,
                    question=user_question,
                    company_data=json.dumps(company_data, ensure_ascii=False, indent=2),
                    analysis_results=json.dumps(analysis_results, ensure_ascii=False, indent=2, default=str),
                    risk_assessment=json.dumps(risk_assessment, ensure_ascii=False, indent=2, default=str),
                    recommendations=json.dumps(recommendations, ensure_ascii=False, indent=2, default=str),
                    db_results=json.dumps(db_results, ensure_ascii=False, indent=2, default=str)
                )
            )
            
            final_report = response.content
            print(" 최종 보고서 생성 완료")
            
            state["final_report"] = final_report
            state["current_stage"] = "completed"
            state["confidence_score"] = self._calculate_confidence_score(state)
            
            return state
            
        except Exception as e:
            print(f" 보고서 생성 실패: {e}")
            return {
                "final_report": "죄송합니다. 보고서 생성 중 오류가 발생했습니다.",
                "current_stage": "report_failed",
                "confidence_score": 0.0
            }
    
    def _extract_company_info(self, text: str) -> Dict[str, Any]:
        """텍스트에서 기업 정보 추출"""
        import re
        
        info = {}
        
        # 정규식으로 정보 추출
        patterns = {
            "company_name": r"(?:회사명|기업명|제조기업명)[:\s]*([^\n,]+)",
            "industry": r"(?:업종|제조분야|제조업분야)[:\s]*([^\n,]+)",
            "location": r"(?:위치|소재지|생산기지)[:\s]*([^\n,]+)",
            "revenue": r"(?:매출|연매출)[:\s]*(\d+)",
            "employees": r"(?:직원|직원수)[:\s]*(\d+)",
            "debt": r"(?:부채|총부채)[:\s]*(\d+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key in ["revenue", "employees", "debt"]:
                    info[key] = int(match.group(1))
                else:
                    info[key] = match.group(1).strip()
        
        # 변동금리 비중과 수출 비중 추가 (기본값 설정)
        info["variable_debt_ratio"] = 70  # 변동금리 비중 기본값 70%
        info["export_ratio"] = 20  # 수출 비중 기본값 20%
        
        # 텍스트에서 명시적으로 언급된 경우 업데이트
        variable_match = re.search(r"변동금리[:\s]*(\d+)%", text)
        if variable_match:
            info["variable_debt_ratio"] = int(variable_match.group(1))
            
        export_match = re.search(r"수출[비중]*[:\s]*(\d+)%", text)
        if export_match:
            info["export_ratio"] = int(export_match.group(1))
        
        return info
    
    def _create_all_relationships(self, company_name: str, company_data: Dict[str, Any]) -> int:
        """모든 관계 생성 (기업 정보 기반)"""
        
        # 변동금리 비중에 따른 금리 노출도
        variable_debt_ratio = company_data.get('variable_debt_ratio', 70)
        if variable_debt_ratio >= 70:
            interest_exposure = "HIGH"
        elif variable_debt_ratio >= 40:
            interest_exposure = "MEDIUM" 
        else:
            interest_exposure = "LOW"
        
        # 수출 비중에 따른 환율 노출도
        export_ratio = company_data.get('export_ratio', 20)
        if export_ratio >= 50:
            exchange_exposure = "HIGH"
        elif export_ratio >= 20:
            exchange_exposure = "MEDIUM"
        else:
            exchange_exposure = "LOW"
        
        relationship_queries = [
            # 1. 기준금리 노출도
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (m:MacroIndicator {{indicatorName: '기준금리'}})
                CREATE (u)-[:IS_EXPOSED_TO {{
                    exposureLevel: '{interest_exposure}',
                    rationale: '변동금리 대출 비중 {variable_debt_ratio}%',
                    riskType: 'INTEREST_RATE',
                    createdAt: datetime()
                }}]->(m)
                RETURN count(*) as created
                """,
                "description": "기준금리 노출도"
            },
            
            # 2. 환율 노출도  
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (m:MacroIndicator {{indicatorName: '원달러환율'}})
                CREATE (u)-[:IS_EXPOSED_TO {{
                    exposureLevel: '{exchange_exposure}',
                    rationale: '수출 비중 {export_ratio}%',
                    riskType: 'EXCHANGE_RATE',
                    createdAt: datetime()
                }}]->(m)
                RETURN count(*) as created
                """,
                "description": "환율 노출도"
            },
            
            # 3. KB 고정금리 전환대출 (변동금리 비중이 높으면 추천)
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (k:KB_Product)
                WHERE k.productName CONTAINS '고정금리' OR k.productName CONTAINS '전환대출'
                CREATE (u)-[:IS_ELIGIBLE_FOR {{
                    eligibilityScore: {0.9 if variable_debt_ratio >= 50 else 0.6},
                    urgency: '{'HIGH' if variable_debt_ratio >= 70 else 'MEDIUM'}',
                    expectedBenefit: '월 이자부담 절감',
                    actionRequired: 'KB 지점 방문 상담',
                    createdAt: datetime()
                }}]->(k)
                RETURN count(*) as created
                """,
                "description": "KB 고정금리 상품"
            },
            
            # 4. 환헤지 상품 (수출 비중이 높으면 추천)
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (k:KB_Product)
                WHERE k.productName CONTAINS '환헤지' OR k.productName CONTAINS '수출기업'
                CREATE (u)-[:IS_ELIGIBLE_FOR {{
                    eligibilityScore: {0.8 if export_ratio >= 30 else 0.5},
                    urgency: '{'HIGH' if export_ratio >= 50 else 'MEDIUM'}',
                    expectedBenefit: '환율변동 리스크 헤지',
                    actionRequired: '수출입 실적 준비 후 상담',
                    createdAt: datetime()
                }}]->(k)
                RETURN count(*) as created
                """,
                "description": "KB 환헤지 상품"
            },
            
            # 5. 중소기업 정책 (매출 규모 기준)
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (p:Policy)
                WHERE p.supportField CONTAINS '중소기업' AND p.policyName CONTAINS '제조업'
                CREATE (u)-[:IS_ELIGIBLE_FOR {{
                    eligibilityScore: {0.8 if company_data.get('revenue', 100) <= 120 else 0.6},
                    urgency: 'MEDIUM',
                    expectedBenefit: '정부 지원자금 확보',
                    actionRequired: '사업계획서 및 재무제표 준비',
                    createdAt: datetime()
                }}]->(p)
                RETURN count(*) as created
                """,
                "description": "정부 지원정책"
            },
            
            # 6. 동종업계 유사기업
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (r:ReferenceCompany)
                WHERE r.sector CONTAINS '{company_data.get('industry', '제조')}'
                WITH u, r, 
                     CASE 
                         WHEN abs(r.revenue - {company_data.get('revenue', 100)}) < 50 THEN 0.9
                         WHEN abs(r.revenue - {company_data.get('revenue', 100)}) < 100 THEN 0.7
                         ELSE 0.5
                     END as similarity
                WHERE similarity > 0.6
                CREATE (u)-[:SIMILAR_TO {{
                    similarityScore: similarity,
                    comparisonBasis: '업종 및 매출규모 유사',
                    createdAt: datetime()
                }}]->(r)
                RETURN count(*) as created
                """,
                "description": "유사기업 매칭"
            },
            
            # 7. 관련 뉴스 영향 (제조업, 금융 뉴스)
            {
                "query": f"""
                MATCH (u:UserCompany {{companyName: '{company_name}'}}), (n:NewsArticle)
                WHERE (n.category IN ['manufacturing', 'financial'] 
                       AND (n.title CONTAINS '제조업' OR n.title CONTAINS '자동차' 
                            OR n.title CONTAINS '부품' OR n.title CONTAINS '금리'
                            OR n.title CONTAINS '환율' OR n.title CONTAINS '{company_data.get('industry', '제조')}'))
                CREATE (n)-[:HAS_IMPACT_ON {{
                    impactScore: 0.6,
                    impactDirection: 'NEUTRAL',
                    rationale: '업종 관련 뉴스 영향',
                    edgeType: 'NEWS_COMPANY_IMPACT',
                    createdAt: datetime()
                }}]->(u)
                RETURN count(*) as created
                """,
                "description": "관련 뉴스 영향"
            }
        ]
        
        total_relationships = 0
        for rel_info in relationship_queries:
            try:
                result = self.neo4j_manager.execute_query(rel_info["query"])
                created = result[0].get('created', 0) if result else 0
                total_relationships += created
                print(f" {rel_info['description']}: {created}개 관계 생성")
            except Exception as e:
                print(f" {rel_info['description']} 생성 실패: {e}")
        
        return total_relationships
    
    def _generate_structured_risk_assessment(self, company_name: str, analysis_results: Dict[str, Any], 
                                           graph_paths: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """구조화된 LLM 기반 리스크 평가"""
        print(" 구조화된 리스크 평가 생성 시작...")
        
        # 기본값 준비
        variable_debt_ratio = company_data.get('variable_debt_ratio', 70)
        export_ratio = company_data.get('export_ratio', 20)
        macro_exposures = analysis_results.get("macro_exposure", [])
        
        # 리스크 레벨 결정 로직
        risk_factors = 0
        if variable_debt_ratio >= 70:
            risk_factors += 2
        elif variable_debt_ratio >= 50:
            risk_factors += 1
            
        if export_ratio >= 50:
            risk_factors += 2
        elif export_ratio >= 30:
            risk_factors += 1
            
        # 거시지표 노출도 확인
        high_exposures = [e for e in macro_exposures if e.get("level") == "HIGH"]
        risk_factors += len(high_exposures)
        
        # 최종 리스크 레벨 결정
        if risk_factors >= 4:
            default_risk_level = "HIGH"
            default_risk_score = 0.75
        elif risk_factors >= 2:
            default_risk_level = "MEDIUM"
            default_risk_score = 0.5
        else:
            default_risk_level = "LOW"
            default_risk_score = 0.25
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """KB 중소기업 리스크 분석 전문가입니다. 
분석 결과를 바탕으로 구조화된 JSON 형태의 리스크 평가를 제공하세요.

중요: 반드시 유효한 JSON 형식으로만 응답하세요. 추가 설명이나 마크다운 없이 순수 JSON만 반환하세요.

{
    "overall_risk_level": "HIGH/MEDIUM/LOW",
    "risk_score": 0.0-1.0,
    "key_risks": [
        {
            "type": "금리리스크/환율리스크/원자재리스크/시장리스크",
            "level": "HIGH/MEDIUM/LOW", 
            "impact": "예상 영향",
            "mitigation": "대응 방안"
        }
    ],
    "opportunities": ["기회 요인들"],
    "assessment_summary": "종합 평가 요약"
}"""),
            ("user", """기업명: {company_name}
변동금리 비중: {variable_debt_ratio}%
수출 비중: {export_ratio}%
거시지표 노출: {macro_exposures}개 (HIGH: {high_exposures}개)

위 데이터를 종합하여 구조화된 리스크 평가를 JSON 형태로 제공하세요.""")
        ])
        
        try:
            response = self.llm.invoke(
                prompt.format_messages(
                    company_name=company_name,
                    variable_debt_ratio=variable_debt_ratio,
                    export_ratio=export_ratio,
                    macro_exposures=len(macro_exposures),
                    high_exposures=len(high_exposures)
                )
            )
            
            content = response.content.strip()
            print(f"LLM 리스크 평가 응답: {content[:200]}...")
            
            # JSON 파싱 시도
            import re
            # 마크다운 코드 블록 제거
            content = content.replace('```json', '').replace('```', '').strip()
            
            # JSON 객체 추출
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                try:
                    parsed_result = json.loads(json_match.group())
                    print(" JSON 파싱 성공")
                    
                    # 필수 필드 검증 및 보완
                    if "overall_risk_level" not in parsed_result:
                        parsed_result["overall_risk_level"] = default_risk_level
                    if "risk_score" not in parsed_result:
                        parsed_result["risk_score"] = default_risk_score
                    if "key_risks" not in parsed_result or not parsed_result["key_risks"]:
                        parsed_result["key_risks"] = self._generate_default_risks(company_data, default_risk_level)
                    if "opportunities" not in parsed_result:
                        parsed_result["opportunities"] = ["KB 금융상품 활용을 통한 금융비용 절감"]
                    if "assessment_summary" not in parsed_result:
                        parsed_result["assessment_summary"] = f"{company_name}은 {default_risk_level} 수준의 종합 리스크를 보이고 있습니다."
                        
                    return parsed_result
                    
                except json.JSONDecodeError as e:
                    print(f" JSON 파싱 실패: {e}")
            
            # 파싱 실패 시 기본 구조 반환
            return self._generate_default_risk_assessment(company_name, company_data, default_risk_level, default_risk_score)
            
        except Exception as e:
            print(f" 구조화된 리스크 평가 생성 실패: {e}")
            return self._generate_default_risk_assessment(company_name, company_data, default_risk_level, default_risk_score)
    
    def _generate_default_risks(self, company_data: Dict[str, Any], risk_level: str) -> List[Dict[str, Any]]:
        """기본 리스크 목록 생성"""
        risks = []
        
        variable_debt_ratio = company_data.get('variable_debt_ratio', 70)
        export_ratio = company_data.get('export_ratio', 20)
        
        # 금리 리스크
        if variable_debt_ratio > 50:
            risks.append({
                "type": "금리리스크",
                "level": "HIGH" if variable_debt_ratio >= 70 else "MEDIUM",
                "impact": f"변동금리 대출 비중 {variable_debt_ratio}%로 금리 1%p 상승 시 연간 이자부담 {int(variable_debt_ratio * 0.5)}만원 증가 예상",
                "mitigation": "KB 고정금리 전환대출 활용으로 금리 상승 리스크 헤지"
            })
        
        # 환율 리스크
        if export_ratio > 20:
            risks.append({
                "type": "환율리스크",
                "level": "HIGH" if export_ratio >= 50 else "MEDIUM",
                "impact": f"수출 비중 {export_ratio}%로 원/달러 환율 10원 변동 시 월 매출 {int(export_ratio * 0.3)}만원 변동",
                "mitigation": "KB 환헤지 상품을 통한 환율 변동성 관리"
            })
        
        # 원자재 리스크 (제조업 특성상 항상 포함)
        risks.append({
            "type": "원자재리스크",
            "level": "MEDIUM",
            "impact": "주요 원자재 가격 10% 상승 시 제조원가 3-5% 증가 예상",
            "mitigation": "장기 공급계약 체결 및 대체 공급처 확보"
        })
        
        return risks
    
    def _generate_default_risk_assessment(self, company_name: str, company_data: Dict[str, Any], 
                                         risk_level: str, risk_score: float) -> Dict[str, Any]:
        """기본 리스크 평가 생성"""
        return {
            "overall_risk_level": risk_level,
            "risk_score": risk_score,
            "key_risks": self._generate_default_risks(company_data, risk_level),
            "opportunities": [
                "KB 금융상품 활용을 통한 금융비용 절감",
                "정부 지원정책 활용으로 자금 조달 비용 감소",
                "환헤지 전략 수립으로 수익성 안정화"
            ],
            "assessment_summary": f"{company_name}은 변동금리 비중 {company_data.get('variable_debt_ratio', 70)}%, 수출 비중 {company_data.get('export_ratio', 20)}%로 {risk_level} 수준의 종합 리스크를 보이고 있습니다. 특히 금리와 환율 변동에 대한 선제적 대응이 필요합니다."
        }
    
    def _generate_path_explanation(self, question: str, cypher_query: str, results: list) -> str:
        """그래프 경로 설명 생성"""
        if not results:
            return "데이터가 없습니다."
        
        explanation = f"질문: {question}\n\n"
        explanation += f"실행된 쿼리: {cypher_query[:200]}...\n\n"
        explanation += f"발견된 관계: {len(results)}개\n"
        
        if len(results) > 0:
            sample = results[0]
            explanation += f"예시: {json.dumps(sample, ensure_ascii=False, default=str)[:200]}..."
        
        return explanation
    
    def _generate_section_explanations(self, company_name: str, analysis_results: Dict[str, Any], 
                                     risk_assessment: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, str]:
        """각 섹션별 LLM 설명 생성"""
        print(f" 섹션별 설명 생성 시작: {company_name}")
        print(f" 입력 데이터 - risk_level: {risk_assessment.get('overall_risk_level')}")
        print(f" 입력 데이터 - kb_products: {len(analysis_results.get('kb_products', []))}개")
        print(f" 입력 데이터 - policies: {len(analysis_results.get('policies', []))}개")
        
        # 리스크 레벨 설명
        risk_level = risk_assessment.get("overall_risk_level", "MEDIUM")
        kb_products_count = len(analysis_results.get("kb_products", []))
        policies_count = len(analysis_results.get("policies", []))
        
        # 변동금리 비중과 수출 비중 확인
        variable_debt_ratio = company_data.get('variable_debt_ratio', 70)
        export_ratio = company_data.get('export_ratio', 20)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """KB 중소기업 금융 전문가입니다. 
각 분석 섹션에 대해 고객이 이해하기 쉽도록 설명해주세요.
전문 용어를 사용하되 친근하고 이해하기 쉽게 설명하세요.

응답 형식:
1. risk_explanation: [리스크 설명]
2. kb_products_explanation: [KB 상품 설명]  
3. policies_explanation: [정책 설명]"""),
            ("user", """기업명: {company_name}
리스크 레벨: {risk_level}
KB 상품 개수: {kb_products_count}개
정책 개수: {policies_count}개
변동금리 비중: {variable_debt_ratio}%
수출 비중: {export_ratio}%

위 정보를 바탕으로 다음 각 섹션에 대한 설명을 생성해주세요:

1. risk_explanation: 왜 이 리스크 레벨({risk_level})로 평가되었는지 구체적인 이유 (변동금리 비중과 수출 비중 언급)
2. kb_products_explanation: KB 상품 추천 결과에 대한 설명
3. policies_explanation: 정부 정책 추천 결과에 대한 설명

각 설명은 2-3문장으로 간결하고 명확하게 작성해주세요.""")
        ])
        
        try:
            response = self.llm.invoke(
                prompt.format_messages(
                    company_name=company_name,
                    risk_level=risk_level,
                    kb_products_count=kb_products_count,
                    policies_count=policies_count,
                    variable_debt_ratio=variable_debt_ratio,
                    export_ratio=export_ratio
                )
            )
            
            content = response.content
            print(f"LLM 응답: {content[:200]}...")
            
            explanations = {}
            
            # 번호 형식으로 파싱 시도
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip().startswith('1.') and 'risk_explanation:' in line:
                    explanations["risk_explanation"] = line.split(':', 1)[1].strip()
                elif line.strip().startswith('2.') and 'kb_products_explanation:' in line:
                    explanations["kb_products_explanation"] = line.split(':', 1)[1].strip()
                elif line.strip().startswith('3.') and 'policies_explanation:' in line:
                    explanations["policies_explanation"] = line.split(':', 1)[1].strip()
            
            # 더 유연한 파싱 (번호 형식이 아닌 경우)
            if not explanations.get("risk_explanation"):
                if "risk_explanation:" in content:
                    risk_part = content.split("risk_explanation:")[1]
                    if "kb_products_explanation:" in risk_part:
                        risk_part = risk_part.split("kb_products_explanation:")[0]
                    elif "2." in risk_part:
                        risk_part = risk_part.split("2.")[0]
                    explanations["risk_explanation"] = risk_part.strip()
            
            if not explanations.get("kb_products_explanation"):
                if "kb_products_explanation:" in content:
                    products_part = content.split("kb_products_explanation:")[1]
                    if "policies_explanation:" in products_part:
                        products_part = products_part.split("policies_explanation:")[0]
                    elif "3." in products_part:
                        products_part = products_part.split("3.")[0]
                    explanations["kb_products_explanation"] = products_part.strip()
                
            if not explanations.get("policies_explanation"):
                if "policies_explanation:" in content:
                    policies_part = content.split("policies_explanation:")[1].strip()
                    explanations["policies_explanation"] = policies_part
            
            # 기본값 설정 (더 구체적으로)
            if not explanations.get("risk_explanation"):
                if risk_level == "HIGH":
                    explanations["risk_explanation"] = f"변동금리 대출 비중이 {variable_debt_ratio}%로 높고, 수출 비중이 {export_ratio}%인 상황에서 금리 상승과 환율 변동이 복합적으로 작용하여 HIGH 위험도로 평가되었습니다."
                elif risk_level == "MEDIUM":
                    explanations["risk_explanation"] = f"변동금리 대출 비중 {variable_debt_ratio}%와 수출 비중 {export_ratio}%를 종합적으로 고려한 결과, 관리 가능한 수준의 MEDIUM 위험도로 평가되었습니다."
                else:
                    explanations["risk_explanation"] = f"재무구조가 안정적이며 외부 충격에 대한 노출이 제한적이어서 LOW 위험도로 평가되었습니다."
                    
            if not explanations.get("kb_products_explanation"):
                explanations["kb_products_explanation"] = f"귀사의 재무상황과 업종 특성을 분석하여 {kb_products_count}개의 KB 금융상품을 추천드립니다. 특히 금리 리스크 관리와 운전자금 확보에 중점을 둔 상품들입니다."
                
            if not explanations.get("policies_explanation"):
                explanations["policies_explanation"] = f"중소 제조업을 위한 {policies_count}개의 정부 지원정책이 확인되었습니다. 금리 부담 완화와 수출 지원에 관련된 정책들을 우선적으로 활용하시기 바랍니다."
            
            print(f" 생성된 설명: {explanations}")
            return explanations
            
        except Exception as e:
            print(f" 섹션 설명 생성 실패: {e}")
            return {
                "risk_explanation": f"변동금리 대출 비중 {variable_debt_ratio}%와 수출 비중 {export_ratio}%를 고려하여 {risk_level} 위험도로 평가되었습니다.",
                "kb_products_explanation": f"귀사에 적합한 {kb_products_count}개의 KB 금융상품을 추천드립니다.",
                "policies_explanation": f"활용 가능한 {policies_count}개의 정부 지원정책을 확인했습니다."
            }
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any], risk_assessment: Dict[str, Any], db_results: list) -> List[Dict[str, Any]]:
        """추천사항 생성"""
        recommendations = []
        
        # KB 상품 추천
        if 'kb_products' in analysis_results and analysis_results['kb_products']:
            top_product = analysis_results['kb_products'][0]
            recommendations.append({
                "type": "KB_PRODUCT",
                "title": f"{top_product.get('product', 'KB 금융상품')} 활용",
                "description": "추천 적합도가 가장 높은 KB 금융상품입니다.",
                "priority": "HIGH",
                "expected_benefit": "이자부담 절감 및 유동성 확보"
            })
        
        # 정책 지원 추천
        if 'policies' in analysis_results and analysis_results['policies']:
            top_policy = analysis_results['policies'][0]
            recommendations.append({
                "type": "GOVERNMENT_POLICY",
                "title": f"{top_policy.get('policy', '정부 지원사업')} 신청",
                "description": "정부 제조업 지원정책을 활용하세요.",
                "priority": "MEDIUM",
                "expected_benefit": "정부 지원금 확보"
            })
        
        return recommendations
    
    def _calculate_confidence_score(self, state: KBFortressState) -> float:
        """신뢰도 점수 계산"""
        base_score = 0.8
        
        # 오류가 있었다면 점수 차감
        error_history = state.get("error_history", [])
        if error_history:
            base_score -= len(error_history) * 0.1
        
        # 수정 시도가 많았다면 점수 차감  
        correction_attempts = state.get("correction_attempts", 0)
        if correction_attempts > 0:
            base_score -= correction_attempts * 0.05
        
        return max(0.3, min(1.0, base_score))
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """사용자 요청 처리 메인 함수"""
        print(f" KB Fortress AI 통합 에이전트 처리 시작")
        print(f"요청: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")
        
        initial_state = KBFortressState(
            messages=[HumanMessage(content=user_input)],
            task_type="",
            company_data={},
            user_company_node_id=None,
            cypher_query="",
            db_results=[],
            analysis_results={},
            risk_assessment={},
            recommendations=[],
            final_report="",
            error_history=[],
            correction_attempts=0,
            current_stage="started",
            confidence_score=0.0,
            section_explanations={}
        )
        
        try:
            # 통합 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            print("\n" + "="*60)
            print(" KB Fortress AI 통합 처리 완료")
            print("="*60)
            print(f" 작업 유형: {result.get('task_type', 'N/A')}")
            print(f" 현재 단계: {result.get('current_stage', 'N/A')}")
            print(f" 등록 노드: {result.get('user_company_node_id', 'N/A')}")
            print(f" 수정 횟수: {result.get('correction_attempts', 0)}회")
            print(f" 신뢰도: {result.get('confidence_score', 0.0):.2f}")
            print("="*60)
            print(f" 최종 보고서:\n{result.get('final_report', '보고서 없음')}")
            print("="*60)
            
            return {
                "success": True,
                "task_type": result.get("task_type", ""),
                "company_node_id": result.get("user_company_node_id"),
                "final_report": result.get("final_report", ""),
                "recommendations": result.get("recommendations", []),
                "confidence_score": result.get("confidence_score", 0.0),
                "analysis_results": result.get("analysis_results", {}),
                "risk_assessment": result.get("risk_assessment", {}),
                "section_explanations": result.get("section_explanations", {}),
                "current_stage": result.get("current_stage", ""),
                "error_history": result.get("error_history", [])
            }
            
        except Exception as e:
            print(f" 통합 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_report": "시스템 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            }
    
    def _analyze_raw_material_dependencies(self, company_name: str) -> Dict[str, Any]:
        """원자재 의존도 분석"""
        
        # 1. 기업-원자재 의존도 조회
        dependencies_query = """
        MATCH (company:UserCompany {companyName: $company_name})
              -[r:IS_DEPENDENT_ON]->(material:MacroIndicator)
        WHERE material.category = 'RAW_MATERIALS' OR r.edgeType = 'RAW_MATERIAL_DEPENDENCY'
        RETURN material.indicatorName as material,
               r.dependencyLevel as dependency_level,
               r.costRatio as cost_ratio,
               r.riskMultiplier as risk_multiplier,
               material.value as current_value,
               material.changeRate as change_rate,
               material.unit as unit
        ORDER BY r.costRatio DESC
        """
        
        dependencies = self.neo4j_manager.execute_query(dependencies_query, {"company_name": company_name})
        
        # 2. 원자재 가격 변동 조회
        price_changes_query = """
        MATCH (material:MacroIndicator)
        WHERE material.category = 'RAW_MATERIALS' OR material.indicatorName CONTAINS '가격지수'
        RETURN material.indicatorName as material,
               material.value as current_value,
               material.changeRate as change_rate,
               material.unit as unit,
               material.lastUpdated as date
        ORDER BY material.changeRate DESC
        """
        
        price_changes = self.neo4j_manager.execute_query(price_changes_query)
        
        # 3. 뉴스 영향 조회
        news_impacts_query = """
        MATCH (news:NewsArticle)-[r:AFFECTS_PRICE]->(material:MacroIndicator)
              <-[dep:IS_DEPENDENT_ON]-(company:UserCompany {companyName: $company_name})
        RETURN news.title as news_title,
               material.indicatorName as material,
               r.impactDirection as impact_direction,
               r.impactMagnitude as impact_magnitude,
               r.confidence as confidence
        ORDER BY r.impactMagnitude DESC
        LIMIT 5
        """
        
        news_impacts = self.neo4j_manager.execute_query(news_impacts_query, {"company_name": company_name})
        
        # 4. 원가 영향 계산
        total_cost_impact = 0
        high_risk_materials = []
        
        for dep in dependencies:
            cost_ratio = dep.get('cost_ratio', 0.0)
            change_rate = dep.get('change_rate', 0.0)
            risk_multiplier = dep.get('risk_multiplier', 1.0)
            
            # 월간 원가 증가 추정 (가정: 월매출 10억원 기준)
            monthly_impact = (cost_ratio * change_rate * 10) * risk_multiplier
            total_cost_impact += monthly_impact
            
            if dep.get('dependency_level') == 'HIGH' and change_rate > 2.0:
                high_risk_materials.append({
                    "material": dep['material'],
                    "impact": f"원가 {cost_ratio*100:.1f}% 차지, {change_rate:+.1f}% 변동"
                })
        
        # 5. 공급망 위험 요소
        supply_chain_risks = []
        if any(dep.get('dependency_level') == 'HIGH' for dep in dependencies):
            supply_chain_risks.append({
                "title": "주요 원자재 가격 변동성",
                "description": f"핵심 원자재 {len([d for d in dependencies if d.get('dependency_level') == 'HIGH'])}개의 높은 의존도"
            })
        
        if any(news.get('impact_direction') == 'POSITIVE' for news in news_impacts):
            supply_chain_risks.append({
                "title": "글로벌 공급망 불안정",
                "description": "최근 뉴스에서 원자재 가격 상승 요인 감지"
            })
        
        return {
            "dependencies": [
                {
                    "material": dep['material'],
                    "dependencyLevel": dep.get('dependency_level', 'MEDIUM'),
                    "costRatio": dep.get('cost_ratio', 0.0),
                    "riskMultiplier": dep.get('risk_multiplier', 1.0)
                }
                for dep in dependencies
            ],
            "price_changes": [
                {
                    "material": change['material'],
                    "currentValue": change.get('current_value'),
                    "changeRate": change.get('change_rate', 0.0),
                    "unit": change.get('unit', ''),
                    "date": str(change.get('date', '2024-08-14'))[:10]
                }
                for change in price_changes[:5]
            ],
            "risk_factors": high_risk_materials,
            "cost_impact": {
                "monthlyIncrease": max(int(total_cost_impact), 0) or 320  # 기본값
            },
            "supply_chain_risks": supply_chain_risks
        }

    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """통합 에이전트 테스트"""
    print("=== KB Fortress AI 통합 에이전트 테스트 ===")
    
    agent = KBFortressUnifiedAgent()
    
    try:
        # 테스트 시나리오
        test_scenarios = [
            # 기업 등록
            """회사명: 스마트제조
업종: 기계제조
위치: 경기도 화성시
매출: 200억원
직원: 80명
부채: 60억원""",
            
            # 일반 질의
            "대한정밀의 리스크 노출도를 분석해주세요",
            
            # 분석 요청
            "대한정밀 기업의 종합적인 금융 리스크 분석을 수행해주세요"
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*20} 테스트 시나리오 {i} {'='*20}")
            
            result = agent.process_request(scenario)
            
            if result["success"]:
                print(f" 처리 성공 - 단계: {result['current_stage']}")
                print(f"신뢰도: {result['confidence_score']:.2f}")
            else:
                print(f" 처리 실패: {result['error']}")
            
            print(f"\n다음 시나리오까지 2초 대기...")
            import time
            time.sleep(2)
        
        print(f"\n 모든 테스트 완료!")
        
    except Exception as e:
        print(f" 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        agent.cleanup()

if __name__ == "__main__":
    main()