#!/usr/bin/env python3
"""
KB Fortress AI - Business Application Interface
기업 정보 입력을 통한 실시간 Neo4j UserCompany 노드 생성 및 분석
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

import chainlit as cl
from chainlit.input_widget import Select, TextInput, NumberInput, Slider

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.dynamic_user_company import DynamicUserCompanyManager
from agents.kb_text_to_cypher_agent import KBTextToCypherAgent
from agents.enhanced_graph_rag import EnhancedGraphRAG
from agents.sentry_agent import SentryAgent

class KBBusinessApp:
    """KB Fortress AI 비즈니스 애플리케이션"""
    
    def __init__(self):
        self.user_company_manager = None
        self.cypher_agent = None
        self.graph_rag = None
        self.sentry_agent = None
        self.current_company_data = None
        
    async def initialize_systems(self):
        """시스템 초기화"""
        try:
            self.user_company_manager = DynamicUserCompanyManager()
            self.cypher_agent = KBTextToCypherAgent()
            self.graph_rag = EnhancedGraphRAG()
            self.sentry_agent = SentryAgent()
            return True
        except Exception as e:
            await cl.Message(
                content=f" 시스템 초기화 실패: {str(e)}",
                author="시스템"
            ).send()
            return False
    
    async def process_company_registration(self, company_data: Dict[str, Any]):
        """기업 등록 처리"""
        # 기업 정보를 텍스트 형태로 변환
        company_input = f"""
회사명: {company_data['company_name']}
업종: {company_data['industry_type']}
위치: {company_data['location']}
매출: {company_data['revenue']}억원
직원: {company_data['employees']}명
부채: {company_data['debt']}억원
수출비중: {company_data['export_ratio']}%
변동금리대출: {int(company_data['debt'] * company_data['variable_debt_ratio'] / 100)}억원
"""
        
        # UserCompany 노드 생성
        result = self.user_company_manager.create_user_company_from_input(company_input)
        
        if result.success:
            self.current_company_data = company_data
            return result
        else:
            return None
    
    async def generate_comprehensive_analysis(self, company_name: str):
        """종합 분석 생성"""
        if not self.graph_rag:
            return "시스템 초기화 중입니다..."
        
        # Enhanced Graph RAG로 종합 분석
        analysis_result = await self.graph_rag.analyze_comprehensive_risk(company_name)
        return analysis_result

# 글로벌 앱 인스턴스
kb_app = KBBusinessApp()

@cl.on_chat_start
async def start():
    """비즈니스 앱 시작"""
    
    # 시스템 초기화
    await cl.Message(
        content=" **KB Fortress AI 시스템 초기화 중...**",
        author="KB Fortress AI"
    ).send()
    
    success = await kb_app.initialize_systems()
    if not success:
        return
    
    # 기업 정보 입력 폼 설정
    settings = await cl.ChatSettings([
        TextInput(
            id="company_name",
            label=" 기업명",
            placeholder="기업명을 입력하세요",
            initial=""
        ),
        Select(
            id="industry_type",
            label=" 제조업종",
            values=["자동차부품", "전자부품", "화학소재", "섬유제조", "기계제조", "금속가공", "플라스틱", "고무제품", "기타제조업"],
            initial_index=0,
        ),
        TextInput(
            id="location",
            label=" 소재지",
            placeholder="예: 경기도 안산시",
            initial=""
        ),
        NumberInput(
            id="revenue",
            label=" 연매출 (억원)",
            initial=100,
            min=10,
            max=10000,
            step=10,
        ),
        NumberInput(
            id="employees",
            label=" 직원 수 (명)",
            initial=50,
            min=5,
            max=1000,
            step=5,
        ),
        NumberInput(
            id="debt", 
            label=" 총 부채 (억원)",
            initial=50,
            min=0,
            max=1000,
            step=5,
        ),
        NumberInput(
            id="export_ratio",
            label=" 수출 비중 (%)",
            initial=30,
            min=0,
            max=100,
            step=5,
        ),
        Slider(
            id="variable_debt_ratio",
            label=" 변동금리 대출 비중 (%)",
            initial=70,
            min=0,
            max=100,
            step=5,
        )
    ]).send()

    # 메인 안내 메시지
    welcome_msg = """
#  KB Fortress AI 제조업 금융 리스크 관리

## **실시간 기업 등록 및 AI 금융 컨설팅**

---

##  **프로세스 개요**

### 1️⃣ **기업 정보 입력** (좌측 패널)
- 기업명, 업종, 소재지 등 기본 정보
- 매출, 직원 수, 부채 규모 등 재무 정보  
- 수출 비중, 변동금리 대출 비중 등 리스크 요소

### 2️⃣ **Neo4j 그래프 등록**
- UserCompany 노드 실시간 생성
- 기존 181개 노드, 483개 관계와 자동 연결
- KB상품, 정부정책, 동종기업, 거시지표 매칭

### 3️⃣ **AI 종합 분석**
- 멀티팩터 리스크 진단 (금리/환율/원자재)
- KB 맞춤형 금융솔루션 추천
- 실행 가능한 전략 로드맵 제시

---

##  **시작하기**

**Step 1**: 좌측 설정 패널에서 기업 정보를 모두 입력하세요.

**Step 2**: 아래 **"기업 등록 및 분석 시작"** 버튼을 클릭하세요.

**Step 3**: AI가 실시간으로 분석한 결과를 확인하세요.

---

##  **분석 결과 미리보기**

등록 완료 시 다음 분석을 제공합니다:

-  **리스크 노출도**: HIGH/MEDIUM/LOW 등급별 분류
-  **KB 추천상품**: 적합도 점수 기반 TOP 10
- ️ **정부 지원정책**: 신청 가능한 사업 목록
-  **동종업계 비교**: 유사 기업 대비 포지셔닝
-  **위기 대응전략**: 복합 리스크 시나리오별 대안
-  **실행 로드맵**: 단계별 구체적 행동계획

"""
    
    await cl.Message(
        content=welcome_msg,
        author="KB Fortress AI"
    ).send()
    
    # 등록 버튼
    await cl.Message(
        content="** 좌측에서 정보 입력 후 아래 버튼을 클릭하세요!**",
        actions=[
            cl.Action(name="register_and_analyze", value="register", label=" 기업 등록 및 AI 분석 시작"),
            cl.Action(name="demo_company", value="demo", label=" 데모 기업으로 체험하기")
        ],
        author="시스템"
    ).send()

@cl.action_callback("register_and_analyze")
async def register_and_analyze(action):
    """기업 등록 및 분석"""
    
    # 현재 설정값 가져오기
    user_session = cl.user_session.get()
    settings = user_session.get("settings", {})
    
    # 필수 입력값 검증
    company_name = settings.get("company_name", "").strip()
    if not company_name:
        await cl.Message(
            content=" 기업명을 입력해주세요.",
            author="시스템"
        ).send()
        return
    
    location = settings.get("location", "").strip()
    if not location:
        await cl.Message(
            content=" 소재지를 입력해주세요.",
            author="시스템"
        ).send()
        return
    
    # 진행 상황 알림
    await cl.Message(
        content=f"️ **{company_name}** 기업 등록을 시작합니다...",
        author="KB Fortress AI"
    ).send()
    
    # 기업 데이터 구성
    company_data = {
        "company_name": company_name,
        "industry_type": settings.get("industry_type", "기타제조업"),
        "location": location,
        "revenue": settings.get("revenue", 100),
        "employees": settings.get("employees", 50),
        "debt": settings.get("debt", 50),
        "export_ratio": settings.get("export_ratio", 30),
        "variable_debt_ratio": settings.get("variable_debt_ratio", 70)
    }
    
    try:
        # 1단계: 기업 등록
        await cl.Message(
            content=" 1단계: Neo4j 그래프에 UserCompany 노드 생성 중...",
            author="처리 상황"
        ).send()
        
        result = await kb_app.process_company_registration(company_data)
        
        if not result:
            await cl.Message(
                content=" 기업 등록에 실패했습니다. 다시 시도해주세요.",
                author="오류"
            ).send()
            return
        
        # 등록 성공 메시지
        registration_msg = f"""
##  **{company_name}** 등록 완료!

** 등록 결과**
- **Node ID**: `{result.node_id}`
- **생성된 관계**: {sum(result.created_relationships.values()) if result.created_relationships else 0}개
- **실행 시간**: {result.execution_time:.2f}초

** 연결된 데이터**
- KB 금융상품과의 적합성 분석 완료
- 정부 지원정책 매칭 완료  
- 거시경제지표 노출도 계산 완료
- 동종업계 유사기업 연결 완료

---

** 이제 AI 종합 분석을 시작합니다...**
        """
        
        await cl.Message(
            content=registration_msg,
            author="등록 완료"
        ).send()
        
        # 2단계: 종합 분석
        await cl.Message(
            content=" 2단계: Enhanced Graph RAG 기반 종합 분석 중...",
            author="처리 상황"
        ).send()
        
        # Enhanced Graph RAG 분석
        analysis_result = await kb_app.generate_comprehensive_analysis(company_name)
        
        # 분석 결과 표시
        final_report = f"""
#  **{company_name}** AI 종합 분석 보고서

{analysis_result}

---

##  **추가 질문 및 상세 분석**

이제 자유롭게 질문하실 수 있습니다:

** 추천 질문**
- "{company_name}의 가장 큰 리스크 요인은 무엇인가요?"
- "금리가 1% 더 오르면 우리 회사에 어떤 영향이 있나요?"
- "추천해주신 KB 상품 중 가장 시급한 것은 무엇인가요?"  
- "유사한 {company_data['industry_type']} 기업들의 성공사례를 알려주세요"
- "복합 금융위기 상황에서의 생존전략을 제안해주세요"

** 전문가 상담**: 1599-KB24 (KB 중소기업 전용 핫라인)
        """
        
        await cl.Message(
            content=final_report,
            author="AI 분석 완료"
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f" 처리 중 오류가 발생했습니다: {str(e)}",
            author="오류"
        ).send()

@cl.action_callback("demo_company")
async def demo_company(action):
    """데모 기업 체험"""
    demo_companies = [
        {
            "name": "대한정밀",
            "industry": "자동차부품",
            "description": "현대자동차 1차 협력사, 변동금리 노출 HIGH"
        },
        {
            "name": "테크스틸", 
            "industry": "섬유제조",
            "description": "수출 중심 기업, 환율 리스크 HIGH"
        },
        {
            "name": "KB화학",
            "industry": "화학제품", 
            "description": "원자재 의존도 높음, 복합 리스크 노출"
        }
    ]
    
    demo_msg = "##  **데모 기업 선택**\n\n다음 기업 중 하나를 선택하여 즉시 체험할 수 있습니다:\n\n"
    
    actions = []
    for i, company in enumerate(demo_companies):
        demo_msg += f"**{i+1}. {company['name']}** ({company['industry']})\n- {company['description']}\n\n"
        actions.append(cl.Action(
            name=f"demo_{company['name']}", 
            value=company['name'], 
            label=f" {company['name']} 분석하기"
        ))
    
    await cl.Message(
        content=demo_msg,
        actions=actions,
        author="데모 선택"
    ).send()

@cl.action_callback("demo_대한정밀")
async def demo_daehan(action):
    """대한정밀 데모"""
    await run_company_analysis("대한정밀")

@cl.action_callback("demo_테크스틸")
async def demo_techsteel(action):
    """테크스틸 데모"""
    await run_company_analysis("테크스틸")

@cl.action_callback("demo_KB화학")
async def demo_kb_chemical(action):
    """KB화학 데모"""
    await run_company_analysis("KB화학")

async def run_company_analysis(company_name: str):
    """기업 분석 실행"""
    await cl.Message(
        content=f" **{company_name}** 기업 분석을 시작합니다...",
        author="분석 시작"
    ).send()
    
    try:
        # Enhanced Graph RAG로 분석
        analysis_result = await kb_app.generate_comprehensive_analysis(company_name)
        
        final_report = f"""
#  **{company_name}** AI 종합 분석 보고서

{analysis_result}

---

##  **추가 질문하기**

"{company_name}에 대해 더 자세히 알고 싶은 점을 자유롭게 질문하세요!"

** 추천 질문**
- "{company_name}의 가장 큰 리스크는 무엇인가요?"
- "금리 상승 시 {company_name}에 미치는 영향을 분석해주세요"
- "{company_name}에 가장 적합한 KB 상품을 추천해주세요"
- "동종업계 대비 {company_name}의 경쟁력은 어떤가요?"

 **채팅창에 질문을 입력하세요!**
        """
        
        await cl.Message(
            content=final_report,
            author="AI 분석 완료"
        ).send()
        
        # 현재 분석 중인 기업 설정
        kb_app.current_company_data = {"company_name": company_name}
        
    except Exception as e:
        await cl.Message(
            content=f" 분석 중 오류 발생: {str(e)}",
            author="오류"
        ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """사용자 질문 처리"""
    if not kb_app.current_company_data:
        await cl.Message(
            content="먼저 기업을 등록하거나 데모 기업을 선택해주세요.",
            author="안내"
        ).send()
        return
    
    user_question = message.content
    
    await cl.Message(
        content=f" 질문 분석 중: '{user_question}'",
        author="처리 중"
    ).send()
    
    try:
        # KB Text-to-Cypher Agent로 질문 처리
        result = kb_app.cypher_agent.process_question(user_question)
        
        if result["success"]:
            answer = result["final_answer"]
            
            response_msg = f"""
##  **AI 분석 결과**

{answer}

---

** 실행된 쿼리**: `{result.get('cypher_query', 'N/A')}`  
**⏱️ 분석 시간**: {result.get('execution_time', 0):.2f}초  
** 수정 횟수**: {result.get('correction_attempts', 0)}회

** 추가 질문이 있으시면 언제든 입력하세요!**
            """
            
            await cl.Message(
                content=response_msg,
                author="AI 컨설턴트"
            ).send()
        else:
            await cl.Message(
                content=f" 질문 처리 실패: {result.get('error', '알 수 없는 오류')}",
                author="오류"
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f" 처리 중 오류: {str(e)}",
            author="오류"
        ).send()

if __name__ == "__main__":
    print("KB Fortress AI Business App 시작...")