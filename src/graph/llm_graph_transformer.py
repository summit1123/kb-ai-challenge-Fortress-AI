"""
LLM 기반 지식그래프 변환기
모든 비정형 데이터를 통합하여 Neo4j 지식그래프로 구축
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.graph.neo4j_manager import Neo4jManager
from src.graph.schema import ReferenceCompany, UserCompany, NewsArticle, MacroIndicator, KB_Product, Policy

from langchain_core.prompts import ChatPromptTemplate

@dataclass
class ExtractedEntity:
    """추출된 엔터티"""
    node_type: str  # Company, NewsArticle, Policy, MacroIndicator, KB_Product
    properties: Dict[str, Any]
    
@dataclass 
class ExtractedRelationship:
    """추출된 관계"""
    source_id: str
    target_id: str
    relationship_type: str  # IS_EXPOSED_TO, HAS_IMPACT_ON, IS_ELIGIBLE_FOR, COMPETES_WITH
    properties: Dict[str, Any]

class LLMGraphTransformer:
    """LLM 기반 그래프 변환기"""
    
    def __init__(self):
        try:
            self.neo4j_manager = Neo4jManager()
        except Exception as e:
            print(f"️  Neo4j 연결 실패, 오프라인 모드로 진행: {e}")
            self.neo4j_manager = None
        
        # Google Gemini 2.5 사용
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if google_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                google_api_key=google_api_key,
                temperature=0.1
            )
            print(" Google Gemini 2.5 Pro 사용")
        else:
            raise ValueError("GOOGLE_API_KEY 환경변수가 필요합니다")
        
        # 그래프 추출 프롬프트 정의
        self.graph_extraction_prompt = ChatPromptTemplate.from_template("""
당신은 KB 금융의 중소기업 AI 분석 전문가입니다. 
제공된 금융/경제 데이터를 KB Fortress AI 지식그래프로 정확하게 변환해주세요.

=== 스키마 정의 ===

## 노드 타입별 필수 속성:

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

## 관계 타입별 필수 속성:

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

=== 추출 지침 ===

1. **노드 생성 기준** ️ 매우 중요 ️:
   - 실제 제목을 그대로 사용하세요! "뉴스_0", "정책_1" 같은 플레이스홀더 절대 금지!
   - 실제 언론사명을 그대로 사용하세요! "미지정" 금지!
   - 실제 기업명을 그대로 사용하세요! "기업_1" 금지!
   - 한국어 정보는 원문 보존 필수
   - ID만 영문_underscore: news_bridge_economy_20250618, policy_sme_digital_support

2. **관계 생성 기준**:
   - 명확한 인과관계나 연관성이 있는 경우만
   - 추측이나 가정 금지
   - 제조업 특성과 금융 리스크 중심

3. **점수 산정 기준**:
   - exposureLevel: 변동금리노출 70%이상=HIGH, 40%이상=MEDIUM, 미만=LOW  
   - impactScore: 직접언급=0.8이상, 간접언급=0.3-0.7, 일반영향=0.1-0.3
   - eligibilityScore: 명시적조건부합=0.8이상, 일반적부합=0.4-0.7

4. **업종 매칭**:
   - "자동차", "부품" → automotive_parts
   - "철강", "제철", "강관" → steel  
   - "화학", "케미칼", "나프타" → chemicals

=== 올바른 예시 ===
입력: {{"title": "은행권, 기업 '위기 극복' 힘 보탠다", "media": "브릿지경제"}}
출력: 
{{
  "id": "news_bridge_economy_crisis_support",
  "type": "NewsArticle", 
  "properties": {{
    "title": "은행권, 기업 '위기 극복' 힘 보탠다",  //  실제 제목 사용
    "publisher": "브릿지경제"  //  실제 언론사 사용
  }}
}}

 잘못된 예시:
{{
  "title": "뉴스_0",  // 절대 금지!
  "publisher": "미지정"  // 절대 금지!
}}

=== 입력 데이터 ===
{input_data}

=== 출력 형식 ===
다음 JSON 형식으로만 응답하세요. 설명이나 부연설명 금지:

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

**주의**: JSON 형식을 정확히 지켜주세요. 코드블럭(```)이나 추가 텍스트 금지.
""")

    def load_all_processed_data(self) -> Dict[str, Any]:
        """모든 처리된 데이터 로드"""
        data_dir = "data/processed"
        all_data = {
            "news": [],
            "kb_products": [],
            "macro_indicators": [],
            "companies": [],
            "policies": []
        }
        
        # 1. 뉴스 데이터 로드
        news_files = [
            "news_manufacturing_20250813.json",
            "news_financial_20250813.json", 
            "news_policy_20250813.json",
            "news_macro_economic_20250813.json"
        ]
        
        for filename in news_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    news_data = json.load(f)
                    all_data["news"].extend(news_data)
        
        # 2. KB 금융상품 데이터 로드
        kb_file = os.path.join("data/raw", "kb_actual_products.json")
        if os.path.exists(kb_file):
            with open(kb_file, 'r', encoding='utf-8') as f:
                all_data["kb_products"] = json.load(f)
        
        # 3. 거시경제지표 데이터 로드
        ecos_file = os.path.join("data/raw", "ecos_latest_indicators.json") 
        if os.path.exists(ecos_file):
            with open(ecos_file, 'r', encoding='utf-8') as f:
                ecos_data = json.load(f)
                # dict를 list로 변환
                all_data["macro_indicators"] = list(ecos_data.values())
        
        # 4. 기업 데이터 로드 (DART + 시나리오)
        company_files = [f for f in os.listdir("data/raw") if f.startswith("company_data_") and f.endswith(".json")]
        if company_files:
            latest_company_file = sorted(company_files)[-1]  # 가장 최신 파일
            company_filepath = os.path.join("data/raw", latest_company_file)
            with open(company_filepath, 'r', encoding='utf-8') as f:
                company_data = json.load(f)
                all_data["companies"] = company_data.get("companies", [])
        
        # 5. 정책 데이터 로드
        policy_files = [f for f in os.listdir("data/raw") if f.startswith("policy_data_") and f.endswith(".json")]
        if policy_files:
            latest_policy_file = sorted(policy_files)[-1]  # 가장 최신 파일
            policy_filepath = os.path.join("data/raw", latest_policy_file)
            with open(policy_filepath, 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
                all_data["policies"] = policy_data.get("policies", [])
        
        print(f" 데이터 로드 완료:")
        print(f"- 뉴스: {len(all_data['news'])}개")
        print(f"- KB상품: {len(all_data['kb_products'])}개") 
        print(f"- 거시지표: {len(all_data['macro_indicators'])}개")
        print(f"- 기업: {len(all_data['companies'])}개")
        print(f"- 정책: {len(all_data['policies'])}개")
        
        return all_data
    
    def extract_graph_elements(self, batch_data: Dict[str, Any]) -> Dict[str, List]:
        """LLM으로 그래프 요소 추출"""
        
        # 배치 데이터 그대로 사용 (배치별 처리를 위해)
        formatted_data = batch_data
        
        print(" LLM으로 그래프 요소 추출 중...")
        
        try:
            # LLM 호출
            response = self.llm.invoke(
                self.graph_extraction_prompt.format(
                    input_data=json.dumps(formatted_data, ensure_ascii=False, indent=2)
                )
            )
            
            print(f" LLM 응답 미리보기: {response.content[:300]}...")
            
            # JSON 파싱 (코드블럭 제거)
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:]  # ```json 제거
            if content.endswith('```'):
                content = content[:-3]  # ``` 제거
            content = content.strip()
            
            extracted_graph = json.loads(content)
            
            print(f" 추출 완료: 노드 {len(extracted_graph['nodes'])}개, 관계 {len(extracted_graph['relationships'])}개")
            
            return extracted_graph
            
        except Exception as e:
            print(f" LLM 추출 오류: {e}")
            print(f" 전체 응답: {response.content if 'response' in locals() else 'No response'}")
            return {"nodes": [], "relationships": []}
    
    def create_nodes_in_neo4j(self, nodes: List[Dict]) -> Dict[str, int]:
        """Neo4j에 노드 생성"""
        created_counts = {}
        
        for node in nodes:
            node_type = node["type"]
            node_id = node["id"]
            properties = node["properties"]
            
            try:
                if node_type == "ReferenceCompany":
                    query = """
                    MERGE (c:ReferenceCompany {nodeId: $nodeId})
                    SET c.companyName = $companyName,
                        c.sector = $sector,
                        c.industryCode = $industryCode,
                        c.revenue = $revenue,
                        c.debtRatio = $debtRatio,
                        c.variableRateExposure = $variableRateExposure,
                        c.exportRatioPct = $exportRatioPct,
                        c.createdAt = datetime()
                    """
                    self.neo4j_manager.execute_query(query, {
                        "nodeId": node_id,
                        **properties
                    })
                
                elif node_type == "NewsArticle":
                    query = """
                    MERGE (n:NewsArticle {nodeId: $nodeId})
                    SET n.title = $title,
                        n.content = $content,
                        n.publishDate = $publishDate,
                        n.media = $media,
                        n.summary = $summary,
                        n.createdAt = datetime()
                    """
                    self.neo4j_manager.execute_query(query, {
                        "nodeId": node_id,
                        **properties
                    })
                
                elif node_type == "MacroIndicator":
                    query = """
                    MERGE (m:MacroIndicator {nodeId: $nodeId})
                    SET m.indicatorName = $indicatorName,
                        m.value = $value,
                        m.unit = $unit,
                        m.changeRate = $changeRate,
                        m.createdAt = datetime()
                    """
                    self.neo4j_manager.execute_query(query, {
                        "nodeId": node_id,
                        **properties
                    })
                
                elif node_type == "KB_Product":
                    query = """
                    MERGE (p:KB_Product {nodeId: $nodeId})
                    SET p.productName = $productName,
                        p.productType = $productType,
                        p.interestRate = $interestRate,
                        p.loanLimit = $loanLimit,
                        p.createdAt = datetime()
                    """
                    self.neo4j_manager.execute_query(query, {
                        "nodeId": node_id,
                        **properties
                    })
                
                created_counts[node_type] = created_counts.get(node_type, 0) + 1
                
            except Exception as e:
                print(f" 노드 생성 오류 ({node_type}): {e}")
        
        return created_counts
    
    def create_relationships_in_neo4j(self, relationships: List[Dict]) -> Dict[str, int]:
        """Neo4j에 관계 생성"""
        created_counts = {}
        
        for rel in relationships:
            rel_type = rel["type"]
            source_id = rel["source_id"]
            target_id = rel["target_id"]
            properties = rel.get("properties", {})
            
            try:
                if rel_type == "IS_EXPOSED_TO":
                    query = """
                    MATCH (c:ReferenceCompany {nodeId: $sourceId})
                    MATCH (m:MacroIndicator {nodeId: $targetId})
                    MERGE (c)-[r:IS_EXPOSED_TO]->(m)
                    SET r.exposureLevel = $exposureLevel,
                        r.rationale = $rationale,
                        r.riskType = $riskType,
                        r.createdAt = datetime()
                    """
                    
                elif rel_type == "HAS_IMPACT_ON":
                    query = """
                    MATCH (n:NewsArticle {nodeId: $sourceId})
                    MATCH (target {nodeId: $targetId})
                    MERGE (n)-[r:HAS_IMPACT_ON]->(target)
                    SET r.impactScore = $impactScore,
                        r.impactDirection = $impactDirection,
                        r.rationale = $rationale,
                        r.createdAt = datetime()
                    """
                
                elif rel_type == "IS_ELIGIBLE_FOR":
                    query = """
                    MATCH (c:ReferenceCompany {nodeId: $sourceId})
                    MATCH (target {nodeId: $targetId})
                    MERGE (c)-[r:IS_ELIGIBLE_FOR]->(target)
                    SET r.eligibilityScore = $eligibilityScore,
                        r.matchingConditions = $matchingConditions,
                        r.recommendationReason = $recommendationReason,
                        r.createdAt = datetime()
                    """
                
                elif rel_type == "COMPETES_WITH":
                    query = """
                    MATCH (c1:ReferenceCompany {nodeId: $sourceId})
                    MATCH (c2:ReferenceCompany {nodeId: $targetId})
                    MERGE (c1)-[r:COMPETES_WITH]->(c2)
                    SET r.similarityScore = $similarityScore,
                        r.competitionType = $competitionType,
                        r.commonFactors = $commonFactors,
                        r.createdAt = datetime()
                    """
                
                self.neo4j_manager.execute_query(query, {
                    "sourceId": source_id,
                    "targetId": target_id,
                    **properties
                })
                
                created_counts[rel_type] = created_counts.get(rel_type, 0) + 1
                
            except Exception as e:
                print(f" 관계 생성 오류 ({rel_type}): {e}")
        
        return created_counts
    
    def build_knowledge_graph(self) -> Dict[str, Any]:
        """통합 지식그래프 구축"""
        print("️  KB Fortress AI 지식그래프 구축 시작")
        
        # 1. 모든 데이터 로드
        all_data = self.load_all_processed_data()
        
        # 2. LLM으로 그래프 요소 추출
        extracted_graph = self.extract_graph_elements(all_data)
        
        # 3. Neo4j에 노드 생성
        print("\n 노드 생성 중...")
        node_counts = self.create_nodes_in_neo4j(extracted_graph["nodes"])
        
        # 4. Neo4j에 관계 생성  
        print("\n 관계 생성 중...")
        rel_counts = self.create_relationships_in_neo4j(extracted_graph["relationships"])
        
        # 5. 결과 요약
        result = {
            "total_nodes": len(extracted_graph["nodes"]),
            "total_relationships": len(extracted_graph["relationships"]),
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
            "processed_data_counts": {
                "news": len(all_data["news"]),
                "kb_products": len(all_data["kb_products"]),
                "macro_indicators": len(all_data["macro_indicators"]),
                "companies": len(all_data["companies"])
            }
        }
        
        print(f"\n 지식그래프 구축 완료!")
        print(f" 노드: {result['total_nodes']}개")
        print(f" 관계: {result['total_relationships']}개")
        
        return result
    
    def save_extraction_result(self, result: Dict[str, Any], output_dir: str = "data/graph_results"):
        """추출 결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_graph_build_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f" 구축 결과 저장: {filepath}")
        return filepath

def main():
    """지식그래프 구축 실행"""
    print("=== KB Fortress AI 지식그래프 구축 ===")
    
    try:
        transformer = LLMGraphTransformer()
        
        # 지식그래프 구축
        result = transformer.build_knowledge_graph()
        
        # 결과 저장
        transformer.save_extraction_result(result)
        
        print("\n 전체 과정 완료!")
        
    except Exception as e:
        print(f" 지식그래프 구축 오류: {e}")
    
    finally:
        if 'transformer' in locals():
            transformer.neo4j_manager.close()

if __name__ == "__main__":
    main()