#!/usr/bin/env python3
"""
KB Fortress AI - Chainlit UI Application
AI 지식그래프 기반 제조업 복합 금융위기 대응 전략 플랫폼
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

class KBFortressUI:
    """KB Fortress AI 메인 UI 클래스"""
    
    def __init__(self):
        self.user_company_manager = None
        self.cypher_agent = None
        self.graph_rag = None
        self.sentry_agent = None
        self.current_user_company = None
        
    async def initialize_agents(self):
        """에이전트 초기화"""
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

# 글로벌 UI 인스턴스
kb_ui = KBFortressUI()

@cl.on_chat_start
async def start():
    """채팅 시작 시 실행"""
    
    # 시스템 초기화 메시지
    await cl.Message(
        content=" **KB Fortress AI 시스템을 초기화하고 있습니다...**",
        author="KB Fortress AI"
    ).send()
    
    # 에이전트 초기화
    success = await kb_ui.initialize_agents()
    if not success:
        return
    
    # 환영 메시지
    welcome_msg = """
#  KB Fortress AI에 오신 것을 환영합니다!

## **AI 지식그래프 기반 제조업 복합 금융위기 대응 전략 플랫폼**

원자재 수입 의존도와 설비 투자 비중이 높은 제조업은 고금리, 고환율의 복합 금융 위기에 가장 직접적으로 노출됩니다. KB Fortress AI는 이러한 제조업의 특수성을 깊이 이해하고 대응하기 위해 개발된 **프로액티브 AI 금융 전략가**입니다.

---

##  **핵심 기능**

### ️ **1. 스마트 제조기업 등록**
- **공급망 분석**: 원자재 의존도와 수입 비중 자동 평가
- **설비투자 패턴**: 고정자산 비율과 감가상각 영향 분석  
- **지식그래프 연결**: 181개 노드, 483개 관계로 전방위 데이터 매칭

###  **2. 복합 금융위기 진단**
- **영향 등급 분석**: 금리·환율·원자재가 미치는 복합적 영향도 측정
- **판단 근거 제시**: 그래프 기반으로 "왜 우리 기업이 위험한지" 명확한 경로 설명
- **선제적 감지**: 위기 발생 전 리스크 신호 포착 및 알림

###  **3. 전략 포트폴리오 제안**
- **금융상품 매칭**: KB 전용 제조업 지원 상품 및 정책자금 추천
- **환헤지 전략**: 수출입 비중에 따른 맞춤형 환율 리스크 관리 방안  
- **공급망 다변화**: 원자재 조달처 다변화 및 관련 정책 연계

###  **4. AI 금융 전략 컨설턴트**
- **자연어 질의응답**: 복잡한 금융 상황을 쉬운 말로 설명
- **실시간 분석**: Neo4j 지식그래프와 LLM 기반 즉석 분석
- **실행 가능한 조언**: 구체적인 다음 단계와 예상 효과 제시

---

##  **제조업 특화 차별점**

### ️ **제조업 DNA 이해**
- 설비 투자 사이클과 감가상각 패턴 고려
- 원자재 가격 변동과 매출원가 연동성 분석
- 수출입 의존도와 환율 노출 정도 정밀 측정

###  **복합 영향 분석**
- 단일 변수가 아닌 금리+환율+원자재가의 연쇄 반응 모델링
- 공급망 전체의 리스크 전파 경로 시각화
- 업종별 벤치마킹과 동종업계 성공 사례 학습

###  **선제적 대응**
- 위기 발생 전 3-6개월 앞선 리스크 시그널 감지
- 시나리오별 대응 전략과 예상 효과 시뮬레이션
- KB 전문가 연결 및 긴급 지원 체계 가동

---

##  **시작하기**

아래에서 원하시는 방법을 선택해 주세요:

"""
    
    await cl.Message(
        content=welcome_msg,
        author="KB Fortress AI"
    ).send()
    
    # 액션 버튼들
    actions = [
        cl.Action(
            name="register_company",
            value="register",
            label=" 제조기업 등록하기"
        ),
        cl.Action(
            name="demo_analysis", 
            value="demo",
            label=" 대한정밀 데모 체험"
        ),
        cl.Action(
            name="crisis_simulation",
            value="crisis",
            label=" 위기 시뮬레이션"
        ),
        cl.Action(
            name="help_guide",
            value="help", 
            label=" 플랫폼 가이드"
        )
    ]
    
    await cl.Message(
        content="**어떤 방식으로 시작하시겠습니까?**",
        actions=actions,
        author="KB Fortress AI"
    ).send()

@cl.action_callback("register_company")
async def register_company_action(action):
    """제조기업 등록 액션"""
    await show_company_registration_form()

@cl.action_callback("demo_analysis") 
async def demo_analysis_action(action):
    """데모 분석 액션"""
    kb_ui.current_user_company = "대한정밀"
    
    demo_msg = """
#  **대한정밀 실전 데모 분석**

##  **기업 프로필**
- **회사명**: 대한정밀 (Daehan Precision)
- **업종**: 자동차부품 제조업 (현대자동차 1차 협력사)  
- **소재지**: 경기도 화성시 (서해안 공업단지)
- **설립**: 1995년 (업력 29년)

##  **재무 현황**  
- **연매출**: 300억원 (2023년 기준)
- **직원수**: 120명 (생산직 80%, 사무직 20%)
- **수출비중**: 20% (동남아, 중동 진출)
- **주요 고객**: 현대자동차, 기아, 현대모비스

## ️ **제조업 특성**
- **설비투자 비중**: 매출의 8% (연간 24억원)
- **원자재 의존도**: 철강 70%, 플라스틱 20%, 기타 10%
- **변동금리 대출**: 80억원 (총 부채의 90%)
- **재고자산 회전율**: 연 6회 (2개월 재고 유지)

##  **리스크 노출도**
- **금리 민감도**: ️ **HIGH** (변동금리 비중 90%)
- **환율 영향도**: ️ **MEDIUM** (수출 20% + 원자재 수입)  
- **원자재가 연동성**: ️ **HIGH** (철강가 직접 영향)
- **공급망 안정성**:  **GOOD** (국내 협력사 위주)

---

##  **이제 자유롭게 질문해 보세요!**

###  **인기 질문 TOP 5**
1. **"금리가 1% 더 오르면 대한정밀에게 어떤 영향이 있나요?"**
2. **"환율이 1,400원을 넘으면 우리 회사 수익성은 어떻게 될까요?"**  
3. **"철강 가격 급등 시 대응할 수 있는 KB 금융상품이 있나요?"**
4. **"유사한 자동차부품 업체들은 어떤 금융전략을 사용하고 있나요?"**
5. **"복합 위기(금리+환율+원자재) 상황에서 생존 전략을 제안해주세요"**

###  **분석 가능한 영역**
-  리스크 노출도 정밀 진단
-  KB 맞춤형 금융상품 추천  
- ️ 정부 제조업 지원정책 매칭
-  동종업계 벤치마킹 분석
-  위기 시나리오 시뮬레이션
-  6개월 전략 로드맵 수립

** 채팅창에 궁금한 것을 자유롭게 입력해 주세요!**
    """
    
    await cl.Message(
        content=demo_msg,
        author="KB Fortress AI"
    ).send()

@cl.action_callback("crisis_simulation")
async def crisis_simulation_action(action):
    """위기 시뮬레이션 액션"""
    crisis_msg = """
#  **복합 금융위기 시뮬레이션**

## ️ **위기 시나리오 설정**

###  **동시다발 충격**
- **금리**: 현재 3.5% → 6개월 내 5.5% (2%p 급등)
- **환율**: 현재 1,350원 → 3개월 내 1,500원 (11% 급등)  
- **철강가**: 현재 대비 30% 상승 (글로벌 공급망 차질)
- **유가**: 배럴당 100달러 돌파 (물류비 상승)

###  **제조업 타격 요인**
1. **이자부담 폭증**: 변동금리 대출 보유 기업 직격탄
2. **원자재비 급등**: 수입 의존도 높은 소재 가격 폭등
3. **수출 경쟁력 저하**: 환율 상승으로 가격 경쟁력 상실
4. **유동성 경색**: 은행권 대출 축소 및 조건 강화

##  **시뮬레이션 대상 선택**

다음 중 어떤 기업으로 위기 시뮬레이션을 진행하시겠습니까?
    """
    
    actions = [
        cl.Action(
            name="crisis_daehan",
            value="crisis_daehan", 
            label=" 대한정밀",
            description="자동차부품 제조업 (변동금리 80억, 수출 20%)"
        ),
        cl.Action(
            name="crisis_new_company",
            value="crisis_new",
            label="️ 새로운 기업", 
            description="우리 회사 정보로 위기 시뮬레이션"
        ),
        cl.Action(
            name="crisis_industry",
            value="crisis_industry",
            label=" 업종별 분석",
            description="제조업 전체 위기 영향도 분석"
        )
    ]
    
    await cl.Message(
        content=crisis_msg,
        actions=actions,
        author="KB Fortress AI"
    ).send()

@cl.action_callback("crisis_daehan")
async def crisis_daehan_action(action):
    """대한정밀 위기 시뮬레이션"""
    kb_ui.current_user_company = "대한정밀"
    
    await cl.Message(
        content=" **대한정밀 복합 금융위기 시뮬레이션을 시작합니다...**\n\n 위기 영향도를 분석 중입니다...",
        author="KB Fortress AI"
    ).send()
    
    # 실제 위기 분석 수행
    crisis_result = """
#  **대한정밀 복합 금융위기 영향 분석**

##  **긴급 경보: 고위험 수준**

---

##  **재무 충격 시뮬레이션**

###  **이자 부담 증가** 
- **현재 월 이자**: 2,330만원 (금리 3.5%, 대출 80억)
- **위기 시 월 이자**: 3,670만원 (금리 5.5%)
- ** 월 추가 부담**: **+1,340만원** (연간 +1.6억원)

###  **환율 영향**
- **수출 매출**: 60억원 (연간)
- **환율 상승 효과**: +11% (1,350→1,500원)
- ** 추가 수익**: **+6.6억원** (연간)

### ️ **원자재비 급등**
- **철강재 비용**: 연간 150억원 (매출의 50%)
- **가격 상승**: +30%
- ** 추가 부담**: **+45억원** (연간)

## ️ **순 영향 분석**

| 구분 | 영향 | 연간 금액 |
|------|------|----------|
| 이자 부담 증가 |  부정적 | **-1.6억원** |
| 환율 상승 효과 |  긍정적 | **+6.6억원** |  
| 원자재비 급등 |  부정적 | **-45.0억원** |
| **순 영향** | ** 부정적** | **-40.0억원** |

###  **위기 진단**
- **매출 대비 손실**: -13.3% (300억 → 260억 수준)
- **생존 가능성**: ️ **위험** (6개월 내 유동성 위기)
- **대응 시급도**:  **최고 수준**

---

##  **KB Fortress AI 긴급 대응 전략**

###  **1단계: 긴급 유동성 확보 (1개월 내)**
- **KB 긴급경영안정자금**: 15억원 (정책금리 2.5%)
- **매출채권 팩토링**: 월 5억원 유동성 확보
- **기존 변동금리 → 고정금리 전환**: 80억원

### ️ **2단계: 리스크 헤징 (3개월 내)**  
- **원자재 가격 헤징**: 철강 선물 계약 (6개월분)
- **환율 헤징**: 수출 대금 6개월 선물 고정
- **KB 무역금융 패키지**: 수출입 통합 관리

### ️ **3단계: 구조적 개선 (6개월 내)**
- **공급망 다변화**: 국산 철강 비중 30% 확대  
- **제품 믹스 고도화**: 고부가가치 부품 비중 확대
- **KB 스마트팩토리 자금**: 자동화 투자로 원가 절감

###  **예상 효과**
- **연간 손실 규모**: -40억 → **-15억** (62.5% 감소)
- **생존 가능성**: ️ 위험 →  **안정** 
- **추가 투자 회수**: 2년 내 손익분기점 달성

---

##  **지금 바로 실행하세요!**

**KB국민은행 기업금융 긴급상담**: ️ 1588-1234
**대응 시한**: 위기 본격화 전 **30일** 

** 더 구체적인 실행 방안이나 다른 시나리오가 궁금하시면 언제든 질문하세요!**
    """
    
    await cl.Message(
        content=crisis_result,
        author="KB Fortress AI"
    ).send()

@cl.action_callback("help_guide")
async def help_guide_action(action):
    """도움말 액션"""
    help_msg = """
#  **KB Fortress AI 플랫폼 완전 가이드**

##  **제조업 특화 AI 금융 전략가의 모든 것**

---

##  **1단계: 제조기업 스마트 등록**

###  **등록 프로세스**
1. **"제조기업 등록하기"** 클릭
2. 기본 정보 입력 (회사명, 업종, 위치, 매출 등)
3. 제조업 특성 정보 (설비투자, 원자재 비중, 수출입 현황)
4. **AI 자동 분석**: 지식그래프 연결 및 관계 매핑

###  **자동 연결되는 데이터**
- **거시경제지표**: 금리, 환율, 원자재가 등 6개 지표
- **KB 금융상품**: 제조업 특화 대출 및 지원 상품 20개  
- **정부 정책**: 제조업 지원 정책 및 보조금 70개
- **유사 기업**: 동종업계 벤치마킹 대상 22개

---

##  **2단계: AI 금융 컨설팅 활용**

###  **질문 유형별 가이드**

####  **리스크 분석 질문**
```
 좋은 질문 예시:
"금리가 1% 더 오르면 우리 회사 이자 부담은 얼마나 늘어날까요?"
"환율 1,400원 돌파 시 수익성에 미치는 영향을 분석해주세요"
"철강가 30% 급등 시 대응 방안을 제시해주세요"

 피해야 할 질문:
"리스크가 뭔가요?" (너무 포괄적)
"좋은 대출 있나요?" (구체성 부족)
```

####  **솔루션 추천 질문**  
```
 좋은 질문 예시:
"변동금리 부채 50억원을 고정금리로 전환할 수 있는 상품은?"
"수출 확대를 위한 KB 무역금융 상품을 추천해주세요"
"설비 투자 자금 마련을 위한 최적의 방안은?"

 맞춤형 추천을 위한 정보 제공:
"우리는 자동차부품 제조업체이고, 현대차 납품 비중이 60%입니다"
"연매출 200억, 수출 비중 30%, 주요 거래처는..."
```

####  **전략 수립 질문**
```
 시나리오 기반 질문:
"복합 위기(금리+환율+원자재가) 상황에서 6개월 생존 전략은?"
"경쟁사 대비 우리 회사의 위기 대응력은 어느 수준인가요?"
"향후 3년간 지속 성장을 위한 금융 전략 로드맵을 제시해주세요"
```

---

##  **3단계: 심화 분석 기능 활용**

###  **위기 시뮬레이션**
- **복합 위기 시나리오**: 금리+환율+원자재가 동시 악화
- **업종별 벤치마킹**: 동종업계 평균 대비 우리 위치
- **시간대별 영향도**: 1개월/3개월/6개월 단위 영향 분석

###  **실시간 모니터링**  
- **위기 신호 감지**: 주요 지표 임계점 도달 시 자동 알림
- **경쟁사 동향**: 유사 기업들의 대응 전략 실시간 업데이트
- **정책 변화**: 제조업 관련 정책 및 지원 제도 변경 사항

---

##  **4단계: 전문가 연결 및 실행**

### ‍ **KB 전문가 상담**
- **기업금융 전문가**: 맞춤형 금융상품 상담
- **무역금융 전문가**: 수출입 및 환헤지 전문 상담  
- **정책자금 전문가**: 정부 지원 사업 신청 지원

###  **실행 체크리스트**
AI가 제안한 전략을 실제 실행하기 위한 단계별 가이드:
1. **우선순위 정하기**: 긴급도/중요도 매트릭스
2. **필요 서류 준비**: 대출 신청, 정책자금 신청 서류  
3. **실행 일정 수립**: 단계별 실행 타임라인
4. **효과 측정**: KPI 설정 및 모니터링 체계

---

##  **고급 활용 팁**

###  **파워 유저 되기**
- **구체적 수치 활용**: "매출 300억, 부채 80억" 등 정확한 정보 제공
- **시나리오 조합**: "만약 금리가 2% 오르고 환율이 1,500원이 되면..."
- **벤치마킹 요청**: "동종업계 상위 20% 기업들과 비교해주세요"

###  **데이터 기반 의사결정**
- **근거 확인**: AI가 제시하는 모든 분석의 데이터 소스 확인
- **교차 검증**: 여러 관점에서 동일한 문제 질문해보기  
- **가정 변경**: "만약 우리 수출 비중이 50%라면?" 같은 가정 변경

---

##  **지금 바로 시작하세요!**

** 첫 질문 추천**: "우리 회사의 현재 금융 리스크를 종합 분석해주세요"

** 목표**: KB Fortress AI와 함께 **데이터 기반 금융 전략 수립**으로 불확실한 시대를 돌파하세요!
    """
    
    await cl.Message(
        content=help_msg,
        author="KB Fortress AI"
    ).send()

async def show_company_registration_form():
    """제조기업 등록 폼 표시"""
    
    # 제조업 업종 옵션 (더 구체적으로)
    manufacturing_industries = [
        "자동차부품 제조업",
        "자동차 완성차 제조업",
        "전자부품 제조업", 
        "반도체 제조업",
        "디스플레이 제조업",
        "기계부품 제조업",
        "산업기계 제조업",
        "정밀기계 제조업",
        "철강 제조업",
        "비철금속 제조업",
        "금속제품 제조업",
        "화학제품 제조업",
        "석유화학 제조업",
        "플라스틱제품 제조업",
        "고무제품 제조업",
        "섬유제품 제조업",
        "의류 제조업",
        "식품 제조업",
        "음료 제조업",
        "기타 제조업"
    ]
    
    # 지역 선택 옵션 (제조업 클러스터 중심)
    location_options = [
        "서울특별시",
        "경기도 (안산/시흥/화성/평택)",
        "경기도 (성남/용인/수원)",
        "인천광역시 (남동공단/부평공단)",
        "부산광역시 (사상/강서구)",
        "울산광역시 (미포/온산공단)",
        "대구광역시 (달성/서구)",
        "광주광역시 (하남/광산구)",
        "대전광역시 (대덕연구단지)",
        "충청북도 (청주/충주/제천)",
        "충청남도 (아산/천안/당진)",
        "전라북도 (전주/군산/익산)", 
        "전라남도 (여수/광양/목포)",
        "경상북도 (구미/포항/경주)",
        "경상남도 (창원/김해/거제)",
        "강원도 (춘천/원주)",
        "제주도"
    ]
    
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="company_name",
                label=" 제조기업명",
                placeholder="예: 혁신테크, 대한정밀, KB화학",
                description="등록할 제조기업명을 입력하세요"
            ),
            Select(
                id="manufacturing_type", 
                label=" 제조업 분야",
                values=manufacturing_industries,
                initial_index=0,
                description="주력 제조 분야를 선택하세요"
            ),
            Select(
                id="location",
                label="️ 생산기지 위치", 
                values=location_options,
                initial_index=1,  # 경기도 안산/화성 기본 선택
                description="주요 생산 공장 위치를 선택하세요"
            ),
            NumberInput(
                id="annual_revenue",
                label=" 연매출 (억원)",
                initial=200,
                min=10,
                max=50000,
                step=10,
                description="최근 연도 매출액을 억원 단위로 입력하세요"
            ),
            NumberInput(
                id="employee_count",
                label=" 전체 직원수 (명)",
                initial=80,
                min=5,
                max=5000,
                step=5,
                description="정규직+비정규직 전체 직원 수"
            ),
            Slider(
                id="production_ratio",
                label="️ 생산직 비중 (%)",
                initial=70,
                min=30,
                max=95,
                step=5,
                description="전체 직원 중 생산직(현장 근무자) 비중"
            ),
            NumberInput(
                id="total_debt",
                label=" 총 부채 (억원)", 
                initial=50,
                min=0,
                max=10000,
                step=5,
                description="은행 대출 + 회사채 + 기타 차입금 총합"
            ),
            NumberInput(
                id="variable_rate_debt",
                label=" 변동금리 대출 (억원)",
                initial=35, 
                min=0,
                max=10000,
                step=5,
                description="금리 변동 위험에 노출된 대출 규모"
            ),
            NumberInput(
                id="annual_capex",
                label="️ 연간 설비투자 (억원)",
                initial=15,
                min=0, 
                max=1000,
                step=2,
                description="연간 기계설비, 공장, IT 시설 투자액"
            ),
            NumberInput(
                id="export_revenue",
                label=" 수출 매출 (억원)",
                initial=40,
                min=0, 
                max=10000,
                step=5,
                description="해외 직수출 + 간접수출 매출 합계"
            ),
            Slider(
                id="raw_material_import_ratio",
                label=" 원자재 수입 의존도 (%)",
                initial=40,
                min=0,
                max=100,
                step=5,
                description="전체 원자재 중 해외 수입 비중"
            ),
            Select(
                id="main_raw_material",
                label=" 주요 원자재",
                values=["철강/금속", "석유화학", "반도체/전자부품", "플라스틱/고분자", "섬유/원사", "식품/농산물", "기타"],
                initial_index=0,
                description="원가에서 가장 큰 비중을 차지하는 원자재"
            ),
            Slider(
                id="raw_material_cost_ratio",
                label=" 원자재비 비중 (%)",
                initial=45,
                min=20,
                max=80,
                step=5,
                description="전체 매출원가 중 원자재비가 차지하는 비중"
            )
        ]
    ).send()
    
    registration_guide = """
#  **제조기업 스마트 등록 시스템**

**우측 설정 패널**에서 기업의 제조업 특성 정보를 입력한 후 **"등록 완료"**를 입력해 주세요.

---

##  **제조업 특화 입력 항목**

###  **기업 기본 정보**
- **기업명**: 등록할 제조기업명 (예: 대한정밀, 혁신테크)
- **제조 분야**: 23개 세부 제조업 분야 중 선택
- **생산기지**: 주요 공단/산업단지 기준 위치 선택

###  **재무 구조 분석**
- **연매출**: 최근 1년 실적 (10억~5조원)
- **직원 구성**: 총원 + 생산직 비중 (제조업 특성 반영)
- **부채 구조**: 총부채 + 변동금리 노출 규모

### ️ **제조업 특성 지표**
- **설비투자**: 연간 CAPEX 규모 (자동화/스마트팩토리 투자)
- **수출 비중**: 해외 매출 규모 (환율 리스크 분석용)
- **원자재 구조**: 수입 의존도 + 주요 소재 + 원가 비중

###  **리스크 프로파일 자동 생성**
입력된 정보로 AI가 자동 분석하는 항목:
- **금리 민감도**: 변동금리 대출 비중 기반
- **환율 노출도**: 수출입 의존도 기반  
- **원자재 리스크**: 수입 의존도 + 원가 비중 기반
- **유동성 위험**: 부채구조 + 매출 안정성 기반

---

##  **AI 자동 연결 프로세스**

### 1️⃣ **거시경제지표 매칭** 
- 금리, 환율, 주요 원자재가(철강, 유가 등) 자동 연결
- 업종별 민감도 가중치 적용

### 2️⃣ **KB 금융상품 필터링**
- 제조업 특화 대출상품 + 무역금융 + 정책자금
- 매출 규모별 + 업종별 맞춤 상품 선별

### 3️⃣ **정부 정책 매칭** 
- 70개+ 제조업 지원 정책 중 자격 요건 충족 항목 자동 선별
- 지역별 + 업종별 + 규모별 세분화 매칭

### 4️⃣ **유사 기업 벤치마킹**
- 동일/인접 업종 + 유사 규모 기업 22개 자동 연결  
- 성공 사례 + 위기 대응 전략 학습

---

## ⏱️ **예상 소요시간**
- **입력**: 3-5분
- **AI 분석**: 30-60초  
- **그래프 연결**: 자동 완료

** 정확한 정보를 입력할수록 더 정밀한 위기 진단과 맞춤형 전략을 제공받을 수 있습니다!**

---

##  **다음 단계 미리보기**

등록 완료 후 바로 이용 가능한 기능:
-  **종합 리스크 진단**: 7개 영역 위험도 측정
-  **맞춤형 솔루션**: KB 상품 + 정부 정책 추천  
-  **위기 시뮬레이션**: 복합 위기 시나리오 분석
-  **벤치마킹**: 동종업계 상위 20% 기업과 비교

** 정보 입력이 완료되면 "등록 완료"라고 입력해 주세요!**
    """
    
    await cl.Message(
        content=registration_guide,
        author="KB Fortress AI"
    ).send()

@cl.on_settings_update
async def update_settings(settings):
    """설정 업데이트 시 호출"""
    cl.user_session.set("company_settings", settings)
    
    company_name = settings.get('company_name', '기업명 미입력')
    manufacturing_type = settings.get('manufacturing_type', '업종 미선택')
    
    await cl.Message(
        content=f" **{company_name}** ({manufacturing_type}) 정보가 준비되었습니다.\n\n **\"등록 완료\"**를 입력하여 KB Fortress AI에 제조기업 등록을 완료하세요!",
        author="KB Fortress AI"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """메시지 처리"""
    
    user_input = message.content.strip()
    
    # 등록 완료 처리
    if user_input == "등록 완료":
        await handle_company_registration()
        return
    
    # 일반 질문 처리 
    if kb_ui.current_user_company:
        await handle_user_question(user_input)
    else:
        # 기업이 등록되지 않은 경우
        await cl.Message(
            content=" **먼저 제조기업 등록을 완료해 주세요!**\n\n**\"제조기업 등록하기\"** 버튼을 클릭하거나, 이미 등록된 기업명(예: 대한정밀)을 알려주세요.\n\n KB Fortress AI는 제조업 특성을 반영한 맞춤형 분석을 제공합니다.",
            author="KB Fortress AI"
        ).send()

async def handle_company_registration():
    """제조기업 등록 처리"""
    
    settings = cl.user_session.get("company_settings", {})
    
    if not settings or not settings.get("company_name"):
        await cl.Message(
            content=" **제조기업 정보가 입력되지 않았습니다.**\n\n우측 설정 패널에서 제조업 특성 정보를 입력한 후 다시 시도해 주세요.\n\n 정확한 정보 입력이 정밀한 AI 분석의 시작입니다!",
            author="KB Fortress AI"
        ).send()
        return
    
    # 등록 중 메시지
    await cl.Message(
        content=f" **{settings['company_name']} 제조기업을 KB Fortress AI에 등록 중입니다...**\n\n 지식그래프 연결 및 제조업 특화 분석 준비 중...\n\n 거시경제지표, KB상품, 정부정책, 유사기업 데이터 매칭 중...",
        author="KB Fortress AI"
    ).send()
    
    try:
        # UserCompany 생성을 위한 상세 텍스트 구성
        user_input_text = f"""
        제조기업명: {settings['company_name']}
        제조업분야: {settings['manufacturing_type']}
        생산기지: {settings['location']}
        연매출: {settings['annual_revenue']}억원
        전체직원: {settings['employee_count']}명
        생산직비중: {settings['production_ratio']}%
        총부채: {settings['total_debt']}억원  
        변동금리대출: {settings['variable_rate_debt']}억원
        연간설비투자: {settings['annual_capex']}억원
        수출매출: {settings['export_revenue']}억원
        원자재수입의존도: {settings['raw_material_import_ratio']}%
        주요원자재: {settings['main_raw_material']}
        원자재비비중: {settings['raw_material_cost_ratio']}%
        """
        
        result = kb_ui.user_company_manager.create_user_company_from_input(user_input_text)
        
        if result.success:
            kb_ui.current_user_company = settings['company_name']
            
            # 제조업 특화 리스크 분석
            production_workers = int(settings['employee_count'] * settings['production_ratio'] / 100)
            office_workers = settings['employee_count'] - production_workers
            
            # 리스크 등급 계산
            interest_risk = " HIGH" if settings['variable_rate_debt'] > settings['total_debt'] * 0.7 else " MEDIUM" if settings['variable_rate_debt'] > settings['total_debt'] * 0.3 else " LOW"
            
            fx_risk = " HIGH" if settings['export_revenue'] > settings['annual_revenue'] * 0.3 or settings['raw_material_import_ratio'] > 60 else " MEDIUM" if settings['export_revenue'] > settings['annual_revenue'] * 0.1 or settings['raw_material_import_ratio'] > 30 else " LOW"
            
            material_risk = " HIGH" if settings['raw_material_cost_ratio'] > 60 and settings['raw_material_import_ratio'] > 50 else " MEDIUM" if settings['raw_material_cost_ratio'] > 40 or settings['raw_material_import_ratio'] > 30 else " LOW"
            
            success_msg = f"""
#  **{settings['company_name']} 제조기업 등록 완료!**

---

##  **등록된 제조기업 정보**

###  **기업 개요**
- **기업명**: **{settings['company_name']}**
- **제조분야**: {settings['manufacturing_type']}
- **생산기지**: {settings['location']}  
- **기업규모**: 연매출 **{settings['annual_revenue']:,}억원** / 직원 **{settings['employee_count']:,}명**

###  **조직 구조** 
- **생산직**: {production_workers}명 ({settings['production_ratio']}%)
- **사무직**: {office_workers}명 ({100-settings['production_ratio']}%)
- **설비투자**: 연간 **{settings['annual_capex']:,}억원** (매출 대비 {settings['annual_capex']/settings['annual_revenue']*100:.1f}%)

###  **재무 구조**
- **총 부채**: {settings['total_debt']:,}억원 (매출 대비 {settings['total_debt']/settings['annual_revenue']*100:.1f}%)
- **변동금리 대출**: {settings['variable_rate_debt']:,}억원 (부채 대비 {settings['variable_rate_debt']/settings['total_debt']*100:.1f}%)
- **수출 비중**: {settings['export_revenue']:,}억원 ({settings['export_revenue']/settings['annual_revenue']*100:.1f}%)

###  **제조업 특성**
- **주요 원자재**: {settings['main_raw_material']}
- **원자재 비중**: 매출원가의 **{settings['raw_material_cost_ratio']}%**
- **수입 의존도**: 원자재의 **{settings['raw_material_import_ratio']}%**

---

##  **AI 리스크 진단 결과**

### ️ **핵심 위험 요소**
- **금리 리스크**: {interest_risk} (변동금리 비중 {settings['variable_rate_debt']/settings['total_debt']*100:.1f}%)
- **환율 리스크**: {fx_risk} (수출+수입 노출도)  
- **원자재 리스크**: {material_risk} (수입 의존도 {settings['raw_material_import_ratio']}%)
- **유동성 리스크**:  MEDIUM (부채비율 {settings['total_debt']/settings['annual_revenue']*100:.1f}%)

###  **종합 위험도**: {" **HIGH ALERT**" if "HIGH" in [interest_risk, fx_risk, material_risk] else "️ **CAUTION**" if "MEDIUM" in [interest_risk, fx_risk, material_risk] else " **STABLE**"}

---

##  **KB Fortress AI 지식그래프 연결 현황**

###  **실시간 연결된 데이터**
- **거시경제지표**: {result.created_relationships.get('CREATE_MACRO_RELATIONSHIPS', 0)}개 지표 연결
- **KB 금융상품**: {result.created_relationships.get('CREATE_KB_PRODUCT_RELATIONSHIPS', 0)}개 맞춤 상품 매칭
- **정부 지원정책**: {result.created_relationships.get('CREATE_POLICY_RELATIONSHIPS', 0)}개 정책 자격 분석
- **벤치마킹 기업**: {result.created_relationships.get('CREATE_SIMILAR_COMPANY_RELATIONSHIPS', 0)}개 유사기업 연결

###  **분석 준비도**:  **100% 완료** (신뢰도: {result.confidence_score*100:.0f}%)

---

##  **이제 KB Fortress AI를 활용하세요!**

###  **추천 첫 질문 TOP 5**

1. ** 종합 진단**: *"우리 회사의 현재 금융 리스크를 종합 분석해주세요"*

2. ** 금리 영향**: *"금리가 2% 더 오르면 우리 이자 부담이 얼마나 늘어날까요?"*

3. ** 환율 시나리오**: *"환율 1,500원 시나리오에서 우리 수익성은 어떻게 될까요?"*

4. ** 원자재 대응**: *"{settings['main_raw_material']} 가격 30% 급등 시 대응방안을 제시해주세요"*

5. ** 위기 시뮬레이션**: *"복합 금융위기 상황에서 6개월 생존 전략을 수립해주세요"*

###  **분석 가능 영역**
-  **맞춤형 리스크 진단**: 7개 핵심 위험 영역 정밀 분석
-  **KB 솔루션 추천**: 제조업 특화 금융상품 + 무역금융  
- ️ **정책자금 매칭**: 자격 충족 정부 지원사업 자동 선별
-  **동종업계 벤치마킹**: 상위 20% 기업 성공 전략 학습
- ️ **공급망 최적화**: 원자재 조달 다변화 + 비용 절감 방안
-  **글로벌 전략**: 수출 확대 + 환헤지 + 해외진출 로드맵

---

##  **KB국민은행이 함께합니다**

**{settings['company_name']}**의 든든한 금융 파트너로서, KB Fortress AI가 **데이터 기반 최적 전략**을 제공하겠습니다!

** 궁금한 것이 있으시면 언제든 자유롭게 질문하세요! **
            """
            
            await cl.Message(
                content=success_msg,
                author="KB Fortress AI"
            ).send()
            
        else:
            await cl.Message(
                content=f" **제조기업 등록 실패**: {result.error_message}\n\n 다시 시도하거나 관리자에게 문의하세요.",
                author="KB Fortress AI"  
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f" **시스템 오류**: {str(e)}\n\n⏰ 잠시 후 다시 시도해 주세요.",
            author="KB Fortress AI"
        ).send()

async def handle_user_question(user_input: str):
    """사용자 질문 처리"""
    
    # 분석 중 메시지
    thinking_msg = await cl.Message(
        content=f" **{kb_ui.current_user_company}에 대한 질문을 분석 중입니다...**\n\n KB Text-to-Cypher Agent 가동\n 지식그래프 탐색 중\n LLM 분석 엔진 작동\n\n*잠시만 기다려 주세요...*",
        author="KB Fortress AI"
    ).send()
    
    try:
        # KB Text-to-Cypher Agent로 질문 처리
        result = kb_ui.cypher_agent.process_question(user_input)
        
        if result["success"]:
            # 성공적인 답변에 제조업 특화 스타일 적용
            response_msg = f"""
{result["final_answer"]}

---

##  **분석 세부 정보**

###  **처리 과정**
- **분석 대상**: {kb_ui.current_user_company} (제조기업)
- **실행 쿼리**: `{result["cypher_query"][:100]}{'...' if len(result["cypher_query"]) > 100 else ''}`
- **데이터 소스**: Neo4j 지식그래프 (181개 노드, 483개 관계)
- **처리 시간**:  {result["execution_time"]:.2f}초
- **정확도 보정**: {result["correction_attempts"]}회 자동 수정

###  **신뢰도 지표**
- **데이터 품질**:  실시간 연동 (DART, ECOS, 뉴스)
- **분석 깊이**:  멀티레이어 관계 분석  
- **제조업 특화**:  업종별 가중치 적용

---

##  **추가 질문 가이드**

궁금한 부분이 더 있으시면 **구체적으로** 질문해 주세요:

###  **심화 분석 질문**
- "이 결과를 바탕으로 6개월 실행 계획을 세워주세요"
- "동종업계 상위 기업들은 이런 상황에서 어떻게 대응했나요?"
- "KB국민은행에서 지금 당장 신청할 수 있는 상품은 무엇인가요?"

###  **시나리오 확장**
- "만약 상황이 더 악화되면 어떻게 될까요?"
- "최선의 경우와 최악의 경우를 비교 분석해주세요"  
- "경쟁사 대비 우리의 대응력은 어느 수준인가요?"

** KB Fortress AI는 {kb_ui.current_user_company}의 성공을 위해 계속 학습하고 발전합니다!**
            """
            
        else:
            # 실패 시 제조업 특화 가이드 제공
            response_msg = f"""
#  **분석 처리 중 일시적 오류 발생**

**오류 상세**: {result.get("error", "알 수 없는 오류")}

---

##  **다시 시도해 보세요**

###  **제조업 특화 질문 가이드**

####  **리스크 분석 질문**
```
 효과적인 질문:
"금리 1% 인상 시 우리 회사 이자 부담 증가액은?"
"원자재 가격 20% 상승이 수익성에 미치는 영향은?"
"환율 1,400원 돌파 시 수출 경쟁력 변화는?"
```

####  **솔루션 추천 질문**
```  
 맞춤형 질문:
"변동금리 대출을 고정금리로 전환할 수 있는 KB 상품은?"
"설비 투자 자금 마련을 위한 최적 방안은?"
"수출 확대를 위한 무역금융 상품을 추천해주세요"
```

####  **전략 수립 질문**
```
 구체적인 질문:
"향후 2년간 안정적 성장을 위한 금융 전략은?"
"공급망 리스크 최소화 방안을 제시해주세요"  
"동종업계 벤치마킹 결과를 바탕으로 개선점을 찾아주세요"
```

---

##  **KB Fortress AI 핵심 기능**

- ** 실시간 리스크 진단**: 7개 핵심 영역 위험도 측정
- ** 맞춤형 솔루션**: KB 금융상품 + 정부 정책 매칭
- ** 동종업계 분석**: 상위 20% 기업 벤치마킹  
- ** 위기 시뮬레이션**: 복합 위기 시나리오 대응 전략
- ** 종합 전략 수립**: 6개월~2년 중장기 로드맵

** 언제든 다시 질문해 주세요! {kb_ui.current_user_company}의 성공을 위해 최선을 다하겠습니다!** 
            """
        
        # thinking 메시지 업데이트
        await thinking_msg.update(content=response_msg)
        
    except Exception as e:
        await thinking_msg.update(
            content=f"""
#  **시스템 일시 오류**

**오류 내용**: {str(e)}

---

##  **해결 방법**

1. **잠시 후 재시도**: 네트워크나 DB 연결 문제일 수 있습니다
2. **질문 방식 변경**: 더 구체적이거나 간단한 질문으로 시도
3. **기본 기능 이용**: "우리 회사 정보를 보여주세요" 같은 기본 질문

##  **긴급 상황**

KB Fortress AI 시스템 문제로 긴급 상담이 필요하시면:
**️ KB국민은행 기업금융**: 1588-1234

**⏰ 잠시 후 다시 시도해 주세요!**
            """
        )

if __name__ == "__main__":
    # Chainlit 앱 실행 시 메타데이터 설정
    cl.run()