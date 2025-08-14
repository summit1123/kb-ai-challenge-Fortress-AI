#!/usr/bin/env python3
"""
오프라인 그래프 구축 스크립트
Neo4j 연결 없이 LLM으로 그래프 요소만 추출하여 저장
"""

import json
import os
import sys
import time
from typing import Dict, List, Any

sys.path.append('/Users/gimdonghyeon/Desktop/kb-ai-challenge')

# Google API만 사용 (Neo4j 제외)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

class OfflineGraphBuilder:
    """오프라인 그래프 구축기"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key="AIzaSyDGYyMpF8gTOg6ps7PJAg1VAZNRJLAUiYA",
            temperature=0.1
        )
        print(" Google Gemini 2.5 Pro 연결 완료")
        
        # 프롬프트 설정
        self.graph_extraction_prompt = ChatPromptTemplate.from_template("""
당신은 KB 금융의 중소기업 AI 분석 전문가입니다. 
제공된 금융/경제 데이터를 KB Fortress AI 지식그래프로 정확하게 변환해주세요.

=== 스키마 정의 ===

**ReferenceCompany** (벤치마킹 기업):
- companyName: 기업명 (원문 그대로)
- sector: "automotive_parts|steel|chemicals" 중 하나  
- industryCode: KSIC 코드 (예: C29301)
- revenue: 매출액 (숫자)
- debtRatio: 부채비율 (0-1 소수)
- variableRateExposure: 변동금리 노출도 (0-1 소수)
- exportRatioPct: 수출비중 백분율 (0-100 숫자)

**NewsArticle** (뉴스):
- title: 제목 (원문)
- publisher: 언론사명
- publishDate: 발행일 (YYYY-MM-DD)
- category: "manufacturing|financial|policy|macro_economic"
- summary: 요약문 (한국어)

**MacroIndicator** (거시지표):
- indicatorName: 지표명 (예: "기준금리", "원달러환율")
- value: 현재값 (숫자)
- unit: 단위 ("%", "원" 등)
- changeRate: 변화율 (숫자)

**Policy** (정책):
- policyName: 정책명 (원문)
- issuingOrg: 발표기관 (예: "중소벤처기업부")
- supportField: 지원분야 (예: "제조업 지원")
- targetBusiness: "중소기업" 고정
- eligibilityText: 자격요건 (한국어 원문)

**KB_Product** (KB상품):
- productName: 상품명 (원문)
- productType: "운전자금|시설자금|보증상품" 중 하나
- targetCustomer: 대상고객 (예: "중소기업")
- interestRate: 금리정보 (문자열)
- loanLimit: 한도정보 (문자열)

=== 관계 정의 ===

**IS_EXPOSED_TO**: ReferenceCompany → MacroIndicator
- exposureLevel: "HIGH|MEDIUM|LOW"
- rationale: 노출 근거 (한국어 설명)
- riskType: "interest_rate|exchange_rate|raw_material" 중 하나

**HAS_IMPACT_ON**: NewsArticle → ReferenceCompany|MacroIndicator  
- impactScore: 0.0-1.0 점수 (높을수록 큰 영향)
- impactDirection: "POSITIVE|NEGATIVE|NEUTRAL"
- rationale: 영향 근거 (한국어 구체적 설명)

**IS_ELIGIBLE_FOR**: ReferenceCompany → Policy|KB_Product
- eligibilityScore: 0.0-1.0 점수 (높을수록 적합)
- matchingConditions: 매칭 조건 (한국어 배열)
- recommendationReason: 추천 이유 (한국어)

**COMPETES_WITH**: ReferenceCompany ↔ ReferenceCompany
- similarityScore: 0.0-1.0 점수 (높을수록 유사)
- competitionType: "direct|indirect"
- commonFactors: 공통 요소들 (한국어 배열)

=== 입력 데이터 ===
{input_data}

=== 출력 형식 ===
다음 JSON 형식으로만 응답하세요:

{{
  "extraction_summary": {{
    "total_nodes": 숫자,
    "total_relationships": 숫자,
    "key_insights": ["핵심 인사이트 1", "핵심 인사이트 2"]
  }},
  "nodes": [
    {{
      "id": "node_id",
      "type": "ReferenceCompany|NewsArticle|MacroIndicator|Policy|KB_Product",
      "properties": {{
        "모든 필수 속성들": "값들"
      }}
    }}
  ],
  "relationships": [
    {{
      "source_id": "소스노드ID",
      "target_id": "타겟노드ID", 
      "type": "IS_EXPOSED_TO|HAS_IMPACT_ON|IS_ELIGIBLE_FOR|COMPETES_WITH",
      "properties": {{
        "모든 필수 속성들": "값들"
      }}
    }}
  ]
}}

**주의**: JSON 형식을 정확히 지켜주세요. 코드블럭이나 추가 텍스트 금지.
""")

    def load_all_data(self) -> Dict[str, Any]:
        """모든 데이터 로드"""
        data_dir = "data"
        all_data = {
            "news": [],
            "kb_products": [],
            "macro_indicators": [],
            "companies": [],
            "policies": []
        }
        
        # 1. 뉴스 데이터 로드
        news_files = [
            "processed/news_manufacturing_20250813.json",
            "processed/news_financial_20250813.json", 
            "processed/news_policy_20250813.json",
            "processed/news_macro_economic_20250813.json"
        ]
        
        for filename in news_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    news_data = json.load(f)
                    all_data["news"].extend(news_data)
        
        # 2. KB 상품 데이터
        kb_file = os.path.join(data_dir, "raw/kb_actual_products.json")
        if os.path.exists(kb_file):
            with open(kb_file, 'r', encoding='utf-8') as f:
                all_data["kb_products"] = json.load(f)
        
        # 3. 거시경제지표
        ecos_file = os.path.join(data_dir, "raw/ecos_latest_indicators.json")
        if os.path.exists(ecos_file):
            with open(ecos_file, 'r', encoding='utf-8') as f:
                ecos_data = json.load(f)
                all_data["macro_indicators"] = list(ecos_data.values())
        
        # 4. 기업 데이터
        company_files = [f for f in os.listdir("data/raw") if f.startswith("company_data_") and f.endswith(".json")]
        if company_files:
            latest_file = sorted(company_files)[-1]
            with open(f"data/raw/{latest_file}", 'r', encoding='utf-8') as f:
                company_data = json.load(f)
                all_data["companies"] = company_data.get("companies", [])
        
        # 5. 정책 데이터
        policy_files = [f for f in os.listdir("data/raw") if f.startswith("policy_data_") and f.endswith(".json")]
        if policy_files:
            latest_file = sorted(policy_files)[-1]
            with open(f"data/raw/{latest_file}", 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
                all_data["policies"] = policy_data.get("policies", [])
        
        print(f" 데이터 로드 완료:")
        for key, value in all_data.items():
            print(f"- {key}: {len(value)}개")
            
        return all_data

    def extract_small_batch(self, batch_data: Dict[str, Any], batch_num: int) -> Dict[str, Any]:
        """작은 배치 단위로 LLM 추출"""
        print(f"\n 배치 {batch_num} LLM 추출 중...")
        
        try:
            response = self.llm.invoke(
                self.graph_extraction_prompt.format(
                    input_data=json.dumps(batch_data, ensure_ascii=False, indent=2)
                )
            )
            
            # JSON 파싱 (코드블럭 제거)
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            print(f" 배치 {batch_num} 완료: 노드 {len(result.get('nodes', []))}개, 관계 {len(result.get('relationships', []))}개")
            
            return result
            
        except Exception as e:
            print(f" 배치 {batch_num} 오류: {e}")
            return {"nodes": [], "relationships": []}

    def build_graph_offline(self):
        """오프라인 그래프 구축"""
        print(" 오프라인 그래프 구축 시작")
        
        # 전체 데이터 로드
        all_data = self.load_all_data()
        
        # 작은 배치들로 분할 (타임아웃 방지)
        batches = [
            {"기업정보": all_data["companies"][:8]},  # 배치 1: 기업 절반
            {"기업정보": all_data["companies"][8:]},  # 배치 2: 기업 나머지  
            {"KB금융상품": all_data["kb_products"][:10]}, # 배치 3: KB상품 절반
            {"KB금융상품": all_data["kb_products"][10:]}, # 배치 4: KB상품 나머지
            {"거시경제지표": all_data["macro_indicators"]}, # 배치 5: 거시지표
            {"정책데이터": all_data["policies"][:20]}, # 배치 6: 정책 1/4
            {"정책데이터": all_data["policies"][20:40]}, # 배치 7: 정책 2/4  
            {"정책데이터": all_data["policies"][40:60]}, # 배치 8: 정책 3/4
            {"정책데이터": all_data["policies"][60:]}, # 배치 9: 정책 4/4
            {"뉴스_데이터": all_data["news"][:15]}, # 배치 10: 뉴스 1/4
            {"뉴스_데이터": all_data["news"][15:30]}, # 배치 11: 뉴스 2/4
            {"뉴스_데이터": all_data["news"][30:45]}, # 배치 12: 뉴스 3/4
            {"뉴스_데이터": all_data["news"][45:]} # 배치 13: 뉴스 4/4
        ]
        
        all_nodes = []
        all_relationships = []
        
        for i, batch in enumerate(batches, 1):
            if not any(batch.values()):  # 빈 배치 스킵
                continue
                
            result = self.extract_small_batch(batch, i)
            
            if result.get('nodes'):
                all_nodes.extend(result['nodes'])
            if result.get('relationships'):
                all_relationships.extend(result['relationships'])
            
            # 배치 간 지연 (API 제한 방지)
            if i < len(batches):
                print("⏱️  5초 대기...")
                time.sleep(5)
        
        print(f"\n️  전체 추출 완료: 노드 {len(all_nodes)}개, 관계 {len(all_relationships)}개")
        
        # 결과 저장
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result = {
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_data_processed": {
                "companies": len(all_data["companies"]),
                "kb_products": len(all_data["kb_products"]),
                "policies": len(all_data["policies"]),
                "news": len(all_data["news"]),
                "macro_indicators": len(all_data["macro_indicators"])
            },
            "extracted_graph": {
                "nodes": all_nodes,
                "relationships": all_relationships
            },
            "statistics": {
                "total_nodes": len(all_nodes),
                "total_relationships": len(all_relationships),
                "node_types": {},
                "relationship_types": {}
            }
        }
        
        # 통계 계산
        for node in all_nodes:
            node_type = node.get('type', 'Unknown')
            result["statistics"]["node_types"][node_type] = result["statistics"]["node_types"].get(node_type, 0) + 1
            
        for rel in all_relationships:
            rel_type = rel.get('type', 'Unknown')
            result["statistics"]["relationship_types"][rel_type] = result["statistics"]["relationship_types"].get(rel_type, 0) + 1
        
        # 저장
        os.makedirs("results", exist_ok=True)
        filepath = f"results/offline_graph_build_{timestamp}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f" 결과 저장 완료: {filepath}")
        return result

if __name__ == "__main__":
    builder = OfflineGraphBuilder()
    result = builder.build_graph_offline()
    
    print("\n 오프라인 그래프 구축 완료!")
    print(f" 최종 결과:")
    print(f"  - 총 노드: {result['statistics']['total_nodes']}개")  
    print(f"  - 총 관계: {result['statistics']['total_relationships']}개")
    print(f"  - 노드 분포: {result['statistics']['node_types']}")
    print(f"  - 관계 분포: {result['statistics']['relationship_types']}")