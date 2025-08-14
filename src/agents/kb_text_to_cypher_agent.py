#!/usr/bin/env python3
"""
KB Fortress AI - Text-to-Cypher Agent with Feedback Loop
사용자 자연어를 KB 그래프 DB용 Cypher 쿼리로 변환하고, 오류 시 자동 수정하는 에이전트
"""

import os
import sys
import json
import re
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

# State 정의
class KBCypherState(TypedDict):
    """KB Text-to-Cypher Agent 상태"""
    messages: Annotated[list, add_messages]  # 사용자 메시지
    cypher_query: str                        # 생성된 Cypher 쿼리
    db_outputs: list                         # DB 실행 결과
    error_history: list                      # 오류 이력
    correction_attempts: int                 # 수정 시도 횟수
    final_answer: str                       # 최종 답변
    context: Dict[str, Any]                 # 추가 컨텍스트

class KBTextToCypherAgent:
    """KB Fortress AI Text-to-Cypher Agent with Feedback Loop"""
    
    def __init__(self):
        # Google Gemini 초기화
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "AIzaSyDGYyMpF8gTOg6ps7PJAg1VAZNRJLAUiYA")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.1
        )
        
        # Neo4j 연결
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'
        self.neo4j_manager = Neo4jManager()
        
        # KB Graph 스키마
        self.kb_schema = self._get_kb_schema()
        
        # Few-shot 예시
        self.fewshot_examples = [
            "USER: '대한정밀의 리스크 노출도를 알려주세요' CYPHER: MATCH (u:UserCompany {companyName: '대한정밀'})-[r:IS_EXPOSED_TO]->(m:MacroIndicator) RETURN m.indicatorName, r.exposureLevel, m.value ORDER BY r.exposureLevel DESC",
            "USER: '대한정밀에게 적합한 KB 상품을 추천해주세요' CYPHER: MATCH (u:UserCompany {companyName: '대한정밀'})-[r:IS_ELIGIBLE_FOR]->(k:KB_Product) RETURN k.productName, k.productType, r.eligibilityScore ORDER BY r.eligibilityScore DESC LIMIT 10",
            "USER: '자동차부품업계에서 기준금리에 노출된 기업들을 찾아주세요' CYPHER: MATCH (u:UserCompany)-[r:IS_EXPOSED_TO]->(m:MacroIndicator {indicatorName: '기준금리'}) WHERE u.industryDescription CONTAINS '자동차' AND r.exposureLevel = 'HIGH' RETURN u.companyName, u.revenue, r.exposureLevel",
            "USER: '대한정밀과 유사한 기업들이 사용한 금융솔루션을 보여주세요' CYPHER: MATCH (u:UserCompany {companyName: '대한정밀'})-[:SIMILAR_TO]->(r:ReferenceCompany)-[:IS_ELIGIBLE_FOR]->(k:KB_Product) RETURN r.companyName, k.productName, k.productType LIMIT 5"
        ]
        
        # LangGraph 워크플로우 구성
        self.workflow = self._build_workflow()
        
        print(" KB Text-to-Cypher Agent 초기화 완료 (피드백 루프 포함)")
    
    def _get_kb_schema(self) -> str:
        """KB Fortress AI 그래프 스키마 반환"""
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

Common Patterns:
(:UserCompany)-[:IS_EXPOSED_TO]->(:MacroIndicator)
(:UserCompany)-[:IS_ELIGIBLE_FOR]->(:KB_Product)
(:UserCompany)-[:IS_ELIGIBLE_FOR]->(:Policy)
(:UserCompany)-[:SIMILAR_TO]->(:ReferenceCompany)
(:NewsArticle)-[:HAS_IMPACT_ON]->(:UserCompany)
"""
    
    def _build_workflow(self) -> StateGraph:
        """피드백 루프가 있는 LangGraph 워크플로우 구성"""
        workflow = StateGraph(KBCypherState)
        
        # 노드 추가
        workflow.add_node("generate_cypher", self.generate_cypher)
        workflow.add_node("execute_cypher", self.execute_cypher)
        workflow.add_node("correct_cypher", self.correct_cypher)
        workflow.add_node("generate_answer", self.generate_answer)
        
        # 엣지 연결
        workflow.set_entry_point("generate_cypher")
        workflow.add_edge("generate_cypher", "execute_cypher")
        
        # 조건부 엣지 (핵심 피드백 루프!)
        workflow.add_conditional_edges(
            "execute_cypher",
            self.route_correction,
            {
                "correct_cypher": "correct_cypher",  # 실행 실패 시
                "answer": "generate_answer"          # 실행 성공 시
            }
        )
        
        # 수정 후 다시 실행
        workflow.add_edge("correct_cypher", "execute_cypher")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def generate_cypher(self, state: KBCypherState) -> Dict[str, Any]:
        """1단계: 사용자 질문을 Cypher 쿼리로 변환"""
        print(" 1단계: Cypher 쿼리 생성")
        
        user_question = state["messages"][-1].content if state["messages"] else ""
        
        generate_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 KB Fortress AI의 Graph Database Cypher 전문가입니다.
사용자 질문을 정확한 Cypher 쿼리로 변환하세요.

중요 규칙:
1. 백틱이나 추가 설명 없이 Cypher 쿼리만 반환
2. KB 그래프 스키마를 정확히 따를 것
3. 성능을 위해 적절한 LIMIT 사용
4. 결과가 유의미하도록 ORDER BY 활용"""),
            
            ("user", """KB Fortress AI Graph 스키마:
{schema}

예시 질문과 쿼리:
{examples}

사용자 질문: {question}

Cypher 쿼리:""")
        ])
        
        try:
            response = self.llm.invoke(
                generate_prompt.format_messages(
                    schema=self.kb_schema,
                    examples="\n".join(self.fewshot_examples),
                    question=user_question
                )
            )
            
            cypher_query = response.content.strip()
            # 백틱 제거 (```cypher ... ``` 형태)
            cypher_query = cypher_query.replace('```cypher\n', '').replace('\n```', '').replace('```', '')
            print(f"생성된 쿼리: {cypher_query}")
            
            return {
                "cypher_query": cypher_query,
                "messages": [AIMessage(content=cypher_query)]
            }
            
        except Exception as e:
            print(f" Cypher 생성 실패: {e}")
            return {
                "cypher_query": "",
                "error_history": [{"stage": "generate", "error": str(e)}]
            }
    
    def execute_cypher(self, state: KBCypherState) -> Dict[str, Any]:
        """2단계: 생성된 Cypher 쿼리를 Neo4j에서 실행"""
        print(" 2단계: Cypher 쿼리 실행")
        
        cypher_query = state.get("cypher_query", "")
        if not cypher_query:
            return {"db_outputs": [], "error_history": [{"stage": "execute", "error": "빈 쿼리"}]}
        
        print(f"실행 쿼리: {cypher_query}")
        
        try:
            # Neo4j에서 쿼리 실행
            results = self.neo4j_manager.execute_query(cypher_query)
            
            print(f"실행 결과: {len(results)}개 레코드 반환")
            
            return {
                "db_outputs": [results],
                "correction_attempts": state.get("correction_attempts", 0)
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f" 쿼리 실행 실패: {error_msg}")
            
            # 오류 이력에 추가
            error_history = state.get("error_history", [])
            error_history.append({
                "stage": "execute",
                "query": cypher_query,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "db_outputs": [error_msg],  # 오류 메시지를 결과로
                "error_history": error_history
            }
    
    def route_correction(self, state: KBCypherState) -> str:
        """조건부 라우팅: 실행 결과에 따라 수정 또는 답변 생성 결정"""
        print(" 실행 결과 검증 및 라우팅")
        
        db_outputs = state.get("db_outputs", [])
        if not db_outputs:
            print("!DB 결과 없음 - 수정 필요!")
            return "correct_cypher"
        
        db_result = db_outputs[-1]
        correction_attempts = state.get("correction_attempts", 0)
        
        # 성공 조건: 리스트이고 길이가 0 이상
        if isinstance(db_result, list):
            if len(db_result) > 0:
                print(" 쿼리 실행 성공 - 답변 생성")
                return "answer"
            elif len(db_result) == 0:
                print("️ 결과 없음 - 쿼리 수정 시도")
                if correction_attempts >= 2:  # 최대 2회 수정
                    print(" 최대 수정 횟수 도달 - 빈 결과로 답변 생성")
                    return "answer"
                return "correct_cypher"
        else:
            # 문자열이면 오류 메시지
            print(" 쿼리 실행 오류 - 수정 필요")
            if correction_attempts >= 2:  # 최대 2회 수정
                print(" 최대 수정 횟수 도달 - 오류로 답변 생성")
                return "answer"
            return "correct_cypher"
    
    def correct_cypher(self, state: KBCypherState) -> Dict[str, Any]:
        """3단계: 실패한 Cypher 쿼리 자동 수정"""
        print(" 3단계: Cypher 쿼리 자동 수정")
        
        failed_query = state.get("cypher_query", "")
        error_history = state.get("error_history", [])
        user_question = state["messages"][0].content if state["messages"] else ""
        correction_attempts = state.get("correction_attempts", 0) + 1
        
        # 최근 오류 메시지 추출
        latest_error = ""
        if error_history:
            latest_error = error_history[-1].get("error", "알 수 없는 오류")
        
        print(f"수정 시도 {correction_attempts}회차")
        print(f"실패한 쿼리: {failed_query}")
        print(f"오류 메시지: {latest_error}")
        
        correction_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 KB Fortress AI Graph DB의 Cypher 오류 수정 전문가입니다.
실패한 쿼리를 분석하고 정확히 수정하세요.

수정 가이드라인:
1. 노드 라벨과 속성명을 스키마와 정확히 맞출 것
2. 관계 타입과 방향을 올바르게 수정
3. 문법 오류 (따옴표, 괄호, 키워드) 수정
4. 존재하지 않는 속성이나 관계 제거
5. 성능을 위해 적절한 필터와 LIMIT 추가

수정된 Cypher 쿼리만 반환하세요 (설명 없이)."""),
            
            ("user", """KB Fortress AI Graph 스키마:
{schema}

사용자 의도: {user_question}

실패한 쿼리:
{failed_query}

오류 메시지:
{error_message}

이전 수정 이력:
{error_history}

수정된 Cypher 쿼리:""")
        ])
        
        try:
            response = self.llm.invoke(
                correction_prompt.format_messages(
                    schema=self.kb_schema,
                    user_question=user_question,
                    failed_query=failed_query,
                    error_message=latest_error,
                    error_history=json.dumps(error_history[-3:], indent=2, ensure_ascii=False)  # 최근 3개만
                )
            )
            
            corrected_query = response.content.strip()
            # 백틱 제거 (```cypher ... ``` 형태)
            corrected_query = corrected_query.replace('```cypher\n', '').replace('\n```', '').replace('```', '')
            print(f"수정된 쿼리: {corrected_query}")
            
            return {
                "cypher_query": corrected_query,
                "correction_attempts": correction_attempts,
                "messages": state["messages"] + [AIMessage(content=corrected_query)]
            }
            
        except Exception as e:
            print(f" 쿼리 수정 실패: {e}")
            
            # 수정 실패 시 안전한 기본 쿼리 제공
            fallback_query = """RETURN "쿼리 수정에 실패했습니다. 다시 시도해주세요." AS message"""
            
            return {
                "cypher_query": fallback_query,
                "correction_attempts": correction_attempts,
                "error_history": error_history + [{"stage": "correct", "error": str(e)}]
            }
    
    def generate_answer(self, state: KBCypherState) -> Dict[str, Any]:
        """4단계: DB 결과를 기반으로 자연어 답변 생성"""
        print(" 4단계: 최종 답변 생성")
        
        user_question = state["messages"][0].content if state["messages"] else ""
        cypher_query = state.get("cypher_query", "")
        db_outputs = state.get("db_outputs", [])
        
        db_result = db_outputs[-1] if db_outputs else []
        
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 KB국민은행의 중소기업 금융 전문가입니다.
Graph Database 조회 결과를 바탕으로 전문적이고 이해하기 쉬운 답변을 제공하세요.

답변 가이드라인:
1. 구체적인 데이터와 수치 포함
2. 실행 가능한 조언 제시  
3. KB 금융상품이나 정책의 실질적 혜택 강조
4. 전문용어는 쉽게 설명
5. 한국어로 친근하게 답변

결과가 없거나 오류인 경우에도 도움이 되는 대안을 제시하세요."""),
            
            ("user", """사용자 질문: {question}

실행된 Cypher 쿼리:
{cypher_query}

데이터베이스 조회 결과:
{db_result}

위 결과를 바탕으로 사용자 질문에 대한 전문적인 답변을 생성하세요.""")
        ])
        
        try:
            response = self.llm.invoke(
                answer_prompt.format_messages(
                    question=user_question,
                    cypher_query=cypher_query,
                    db_result=json.dumps(db_result, indent=2, ensure_ascii=False, default=str)
                )
            )
            
            final_answer = response.content
            print(f"최종 답변: {final_answer[:100]}...")
            
            return {
                "final_answer": final_answer,
                "messages": state["messages"] + [AIMessage(content=final_answer)]
            }
            
        except Exception as e:
            print(f" 답변 생성 실패: {e}")
            error_answer = "죄송합니다. 답변 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            
            return {
                "final_answer": error_answer,
                "messages": state["messages"] + [AIMessage(content=error_answer)]
            }
    
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """사용자 질문 처리 메인 함수"""
        print(f" KB Text-to-Cypher Agent 처리 시작")
        print(f"질문: '{user_question}'")
        
        initial_state = KBCypherState(
            messages=[HumanMessage(content=user_question)],
            cypher_query="",
            db_outputs=[],
            error_history=[],
            correction_attempts=0,
            final_answer="",
            context={"start_time": datetime.now()}
        )
        
        try:
            # LangGraph 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            execution_time = (datetime.now() - initial_state["context"]["start_time"]).total_seconds()
            
            print("\n" + "="*60)
            print(" KB Text-to-Cypher Agent 처리 완료")
            print("="*60)
            print(f"⏱️ 실행 시간: {execution_time:.2f}초")
            print(f" 수정 횟수: {result.get('correction_attempts', 0)}회")
            print(f" 최종 결과: {len(result.get('db_outputs', []))}개 결과")
            print("="*60)
            print(f" 답변:\n{result.get('final_answer', '답변 없음')}")
            print("="*60)
            
            return {
                "success": True,
                "question": user_question,
                "final_answer": result.get("final_answer", ""),
                "cypher_query": result.get("cypher_query", ""),
                "db_results": result.get("db_outputs", []),
                "correction_attempts": result.get("correction_attempts", 0),
                "execution_time": execution_time,
                "error_history": result.get("error_history", [])
            }
            
        except Exception as e:
            print(f" 전체 처리 실패: {e}")
            return {
                "success": False,
                "question": user_question,
                "error": str(e),
                "final_answer": "시스템 오류가 발생했습니다. 다시 시도해주세요."
            }
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """KB Text-to-Cypher Agent 테스트"""
    print("=== KB Fortress AI Text-to-Cypher Agent 테스트 (피드백 루프) ===")
    
    agent = KBTextToCypherAgent()
    
    try:
        # 테스트 질문들
        test_questions = [
            "대한정밀의 리스크 노출도를 알려주세요",
            "대한정밀에게 적합한 KB 상품 TOP 5를 추천해주세요",
            "자동차부품업계에서 기준금리 위험이 높은 기업들을 찾아주세요",
            "대한정밀과 유사한 기업들이 사용하는 금융솔루션을 보여주세요"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{''*20} 테스트 {i} {''*20}")
            result = agent.process_question(question)
            
            if result["success"]:
                print(f" 성공 (수정 {result['correction_attempts']}회)")
            else:
                print(f" 실패: {result['error']}")
            
            print(f"\n다음 테스트까지 3초 대기...")
            import time
            time.sleep(3)
        
        print(f"\n 모든 테스트 완료!")
        
    except Exception as e:
        print(f" 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        agent.cleanup()

if __name__ == "__main__":
    main()