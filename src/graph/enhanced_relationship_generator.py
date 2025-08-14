"""
Enhanced Relationship Generator
LLM 기반 정교한 관계 생성 전용 시스템
"""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.graph.neo4j_manager import Neo4jManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

@dataclass
class RelationshipCandidate:
    """관계 후보"""
    source_id: str
    source_type: str
    source_data: Dict[str, Any]
    target_id: str
    target_type: str
    target_data: Dict[str, Any]
    relationship_type: str
    confidence: float = 0.0
    reasoning: str = ""

class EnhancedRelationshipGenerator:
    """LLM 기반 정교한 관계 생성기"""
    
    def __init__(self):
        try:
            self.neo4j_manager = Neo4jManager()
        except Exception as e:
            print(f"️ Neo4j 연결 실패: {e}")
            self.neo4j_manager = None
        
        # Google Gemini 설정
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=google_api_key
            )
            print(" Enhanced Relationship Generator with Gemini 2.0 Flash")
        else:
            raise ValueError("GOOGLE_API_KEY 환경변수가 필요합니다")
    
    def create_news_impact_relationships(self) -> Dict[str, Any]:
        """뉴스 → 거시지표/기업 영향 관계 생성"""
        print(" 뉴스 영향 관계 생성 시작...")
        
        # 1. 뉴스와 거시지표 데이터 로드
        news_data = self._load_news_articles()
        macro_data = self._load_macro_indicators()
        company_data = self._load_companies()
        
        print(f" 로드된 데이터: 뉴스 {len(news_data)}개, 거시지표 {len(macro_data)}개, 기업 {len(company_data)}개")
        
        # 2. 뉴스 → 거시지표 관계 생성
        news_macro_relationships = []
        for news in news_data[:10]:  # 테스트를 위해 10개만
            for macro in macro_data:
                relationship = self._analyze_news_macro_impact(news, macro)
                if relationship and relationship.confidence > 0.3:
                    news_macro_relationships.append(relationship)
        
        # 3. 뉴스 → 기업 관계 생성
        news_company_relationships = []
        for news in news_data[:10]:
            for company in company_data[:5]:  # 상위 5개 기업
                relationship = self._analyze_news_company_impact(news, company)
                if relationship and relationship.confidence > 0.3:
                    news_company_relationships.append(relationship)
        
        # 4. Neo4j에 관계 생성
        created_relationships = {
            "news_macro": 0,
            "news_company": 0,
            "total": 0
        }
        
        if self.neo4j_manager:
            created_relationships["news_macro"] = self._create_relationships_in_neo4j(news_macro_relationships)
            created_relationships["news_company"] = self._create_relationships_in_neo4j(news_company_relationships)
            created_relationships["total"] = created_relationships["news_macro"] + created_relationships["news_company"]
        
        return {
            "relationships_analyzed": len(news_macro_relationships) + len(news_company_relationships),
            "relationships_created": created_relationships,
            "news_macro_candidates": len(news_macro_relationships),
            "news_company_candidates": len(news_company_relationships)
        }
    
    def _analyze_news_macro_impact(self, news: Dict, macro: Dict) -> Optional[RelationshipCandidate]:
        """뉴스가 거시지표에 미치는 영향 분석"""
        
        prompt = ChatPromptTemplate.from_template("""
당신은 금융 분석 전문가입니다. 다음 뉴스가 거시경제지표에 미치는 영향을 분석하세요.

=== 뉴스 정보 ===
제목: {news_title}
언론사: {news_publisher}
날짜: {news_date}
내용: {news_content}
키워드: {news_keywords}

=== 거시지표 정보 ===
지표명: {macro_name}
현재값: {macro_value}
타입: {macro_type}

=== 분석 기준 ===
1. **직접 영향**: 뉴스가 해당 지표를 직접 언급하거나 변경하는 경우 (0.8-1.0)
2. **간접 영향**: 뉴스가 해당 지표에 2차적 영향을 주는 경우 (0.4-0.7)
3. **약한 연관**: 일반적인 경제 영향만 있는 경우 (0.1-0.3)
4. **무관련**: 전혀 관련 없는 경우 (0.0)

=== 제조업 특화 분석 ===
- 금리 관련: 변동금리 대출, 설비투자 비용에 미치는 영향 중점 분석
- 환율 관련: 원자재 수입, 제품 수출에 미치는 영향 중점 분석
- 원자재 관련: 철강, 구리, 알루미늄 등 제조업 핵심 소재 영향 분석

=== 출력 형식 ===
다음 JSON 형식으로만 응답하세요:

{{
  "has_impact": true/false,
  "impact_score": 0.0-1.0,
  "impact_direction": "POSITIVE/NEGATIVE/NEUTRAL",
  "confidence": 0.0-1.0,
  "reasoning": "구체적인 영향 분석 근거 (한국어, 2-3문장)",
  "impact_mechanism": "영향 전달 메커니즘 설명",
  "time_horizon": "즉시/단기/중기/장기",
  "affected_sectors": ["영향받는 제조업 분야들"]
}}

**주의**: JSON 형식만 출력하고 추가 설명 금지.
""")
        
        try:
            # 뉴스 데이터 전처리
            news_content = news.get('content', news.get('summary', ''))[:500]  # 길이 제한
            news_keywords = ', '.join(news.get('keywords', '').split(',')[:10]) if news.get('keywords') else ''
            
            formatted_prompt = prompt.format(
                news_title=news.get('title', ''),
                news_publisher=news.get('media', news.get('publisher', '')),
                news_date=news.get('date', news.get('publishDate', '')),
                news_content=news_content,
                news_keywords=news_keywords,
                macro_name=macro.get('indicatorName', ''),
                macro_value=macro.get('value', macro.get('currentValue', '')),
                macro_type=macro.get('type', macro.get('unit', ''))
            )
            
            response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
            
            # JSON 파싱
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            analysis = json.loads(response_text)
            
            if analysis.get('has_impact', False) and analysis.get('confidence', 0) > 0.3:
                return RelationshipCandidate(
                    source_id=f"news_{news.get('news_id', hash(news.get('title', '')))}",
                    source_type="NewsArticle",
                    source_data=news,
                    target_id=f"macro_{macro.get('indicator_id', hash(macro.get('indicatorName', '')))}",
                    target_type="MacroIndicator", 
                    target_data=macro,
                    relationship_type="HAS_IMPACT_ON",
                    confidence=analysis.get('confidence', 0),
                    reasoning=analysis.get('reasoning', '')
                )
            
            return None
            
        except Exception as e:
            print(f" 뉴스-거시지표 분석 실패: {e}")
            return None
    
    def _analyze_news_company_impact(self, news: Dict, company: Dict) -> Optional[RelationshipCandidate]:
        """뉴스가 특정 기업에 미치는 영향 분석"""
        
        prompt = ChatPromptTemplate.from_template("""
당신은 제조업 전문 금융 애널리스트입니다. 다음 뉴스가 특정 제조기업에 미치는 영향을 분석하세요.

=== 뉴스 정보 ===
제목: {news_title}
내용: {news_content}
키워드: {news_keywords}
카테고리: {news_category}

=== 기업 정보 ===
기업명: {company_name}
업종: {company_sector}
주요사업: {company_business}
매출규모: {company_revenue}
위치: {company_location}

=== 영향 분석 기준 ===
1. **직접 영향**: 기업명 직접 언급, 업종 특정 정책/사건 (0.8-1.0)
2. **업종 영향**: 해당 업종 전반에 영향주는 뉴스 (0.5-0.7)  
3. **간접 영향**: 일반적 경제환경 변화 (0.2-0.4)
4. **무관련**: 전혀 관련 없음 (0.0)

=== 제조업 특화 요소 ===
- 원자재 가격 변동이 제조원가에 미치는 영향
- 수출입 정책이 해외 매출에 미치는 영향  
- 금리 변동이 설비투자 및 운전자금에 미치는 영향
- 환율 변동이 수출 경쟁력에 미치는 영향

=== 출력 형식 ===
{{
  "has_impact": true/false,
  "impact_score": 0.0-1.0,
  "impact_direction": "POSITIVE/NEGATIVE/NEUTRAL",
  "confidence": 0.0-1.0,
  "reasoning": "구체적 영향 근거 (한국어, 2-3문장)",
  "impact_areas": ["영향받는 사업영역들"],
  "financial_impact": "매출/비용/투자 중 주요 영향 영역",
  "urgency": "즉시/단기/중기/장기"
}}
""")
        
        try:
            formatted_prompt = prompt.format(
                news_title=news.get('title', ''),
                news_content=news.get('content', news.get('summary', ''))[:300],
                news_keywords=', '.join(news.get('keywords', '').split(',')[:8]) if news.get('keywords') else '',
                news_category=news.get('category', ''),
                company_name=company.get('companyName', ''),
                company_sector=company.get('sector', company.get('industry', '')),
                company_business=company.get('mainBusiness', ''),
                company_revenue=company.get('revenue', ''),
                company_location=company.get('location', '')
            )
            
            response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
            response_text = response.content.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            analysis = json.loads(response_text)
            
            if analysis.get('has_impact', False) and analysis.get('confidence', 0) > 0.3:
                return RelationshipCandidate(
                    source_id=f"news_{news.get('news_id', hash(news.get('title', '')))}",
                    source_type="NewsArticle",
                    source_data=news,
                    target_id=f"company_{company.get('company_id', hash(company.get('companyName', '')))}",
                    target_type="ReferenceCompany",
                    target_data=company,
                    relationship_type="HAS_IMPACT_ON",
                    confidence=analysis.get('confidence', 0),
                    reasoning=analysis.get('reasoning', '')
                )
            
            return None
            
        except Exception as e:
            print(f" 뉴스-기업 분석 실패: {e}")
            return None
    
    def _load_news_articles(self) -> List[Dict]:
        """뉴스 데이터 로드"""
        try:
            if self.neo4j_manager:
                # Neo4j에서 로드
                query = "MATCH (n:NewsArticle) RETURN n LIMIT 20"
                result = self.neo4j_manager.execute_query(query)
                return [record['n'] for record in result] if result else []
            else:
                # 파일에서 로드
                news_files = [
                    "data/processed/news_manufacturing_20250813.json",
                    "data/processed/news_financial_20250813.json",
                    "data/processed/news_policy_20250813.json"
                ]
                
                all_news = []
                for file_path in news_files:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_news.extend(json.load(f))
                
                return all_news[:15]  # 테스트용으로 15개만
                
        except Exception as e:
            print(f" 뉴스 로드 실패: {e}")
            return []
    
    def _load_macro_indicators(self) -> List[Dict]:
        """거시지표 데이터 로드"""
        try:
            if self.neo4j_manager:
                query = "MATCH (m:MacroIndicator) RETURN m"
                result = self.neo4j_manager.execute_query(query)
                return [record['m'] for record in result] if result else []
            else:
                # 기본 거시지표 데이터
                return [
                    {
                        "indicatorName": "한국은행 기준금리",
                        "currentValue": "3.50%",
                        "type": "금리",
                        "unit": "%"
                    },
                    {
                        "indicatorName": "원/달러 환율", 
                        "currentValue": "1,390.2원",
                        "type": "환율",
                        "unit": "원"
                    }
                ]
        except Exception as e:
            print(f" 거시지표 로드 실패: {e}")
            return []
    
    def _load_companies(self) -> List[Dict]:
        """기업 데이터 로드"""
        try:
            if self.neo4j_manager:
                query = "MATCH (c:ReferenceCompany) RETURN c LIMIT 10"
                result = self.neo4j_manager.execute_query(query)
                return [record['c'] for record in result] if result else []
            else:
                # 기본 제조업 기업 데이터
                return [
                    {
                        "companyName": "현대모비스",
                        "sector": "자동차부품",
                        "mainBusiness": "자동차 부품 제조",
                        "revenue": "대기업",
                        "location": "서울"
                    },
                    {
                        "companyName": "동국제강",
                        "sector": "철강",
                        "mainBusiness": "철강 제조", 
                        "revenue": "대기업",
                        "location": "경기"
                    }
                ]
        except Exception as e:
            print(f" 기업 로드 실패: {e}")
            return []
    
    def _create_relationships_in_neo4j(self, relationships: List[RelationshipCandidate]) -> int:
        """Neo4j에 관계 생성"""
        if not self.neo4j_manager or not relationships:
            return 0
        
        created_count = 0
        for rel in relationships:
            try:
                # 소스와 타겟 노드 존재 확인 및 관계 생성
                query = """
                MATCH (source), (target)
                WHERE (source:NewsArticle AND source.title = $source_title)
                  AND ((target:MacroIndicator AND target.indicatorName = $target_name)
                       OR (target:ReferenceCompany AND target.companyName = $target_name))
                CREATE (source)-[r:HAS_IMPACT_ON {
                    impactScore: $impact_score,
                    confidence: $confidence,
                    rationale: $reasoning,
                    createdAt: datetime()
                }]->(target)
                RETURN count(r) as created
                """
                
                params = {
                    "source_title": rel.source_data.get('title', ''),
                    "target_name": rel.target_data.get('indicatorName', rel.target_data.get('companyName', '')),
                    "impact_score": rel.confidence,
                    "confidence": rel.confidence,
                    "reasoning": rel.reasoning
                }
                
                result = self.neo4j_manager.execute_query(query, params)
                if result and result[0].get('created', 0) > 0:
                    created_count += 1
                    
            except Exception as e:
                print(f" 관계 생성 실패: {e}")
                continue
        
        return created_count

if __name__ == "__main__":
    generator = EnhancedRelationshipGenerator()
    result = generator.create_news_impact_relationships()
    print(f" 관계 생성 완료: {result}")