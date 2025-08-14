#!/usr/bin/env python3
"""
Text-to-Cypher Engine for KB Fortress AI
자연어 입력을 Neo4j Cypher 쿼리로 변환하는 시스템
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import google.generativeai as genai

# 환경변수 설정
if not os.getenv('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = 'AIzaSyDGYyMpF8gTOg6ps7PJAg1VAZNRJLAUiYA'

@dataclass
class CompanyInfo:
    """사용자 입력으로부터 추출된 기업 정보"""
    company_name: str
    industry: str = ""
    location: str = ""
    revenue: int = 0
    employees: int = 0
    debt_amount: int = 0
    variable_rate_debt: int = 0
    export_amount: int = 0
    business_description: str = ""
    founded_year: int = 0
    confidence_score: float = 0.0
    extracted_keywords: List[str] = None

@dataclass
class CypherQuery:
    """생성된 Cypher 쿼리 정보"""
    query: str
    parameters: Dict[str, Any]
    query_type: str
    description: str
    confidence: float
    timestamp: datetime

class TextToCypherEngine:
    """자연어를 Cypher 쿼리로 변환하는 엔진"""
    
    def __init__(self):
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print(" Text-to-Cypher 엔진 초기화 완료")
        
        # 산업 분류 매핑
        self.industry_mapping = {
            "자동차": "자동차부품 제조업",
            "자동차부품": "자동차부품 제조업", 
            "부품": "자동차부품 제조업",
            "철강": "철강제조업",
            "강철": "철강제조업",
            "금속": "금속가공업",
            "화학": "화학제품 제조업",
            "화학제품": "화학제품 제조업",
            "플라스틱": "플라스틱제품 제조업",
            "전자": "전자부품 제조업",
            "전기": "전기장비 제조업",
            "기계": "기계제조업",
            "섬유": "섬유제품 제조업",
            "식품": "식품제조업",
            "제약": "의약품 제조업",
            "의약품": "의약품 제조업"
        }
        
        # 매출 규모 추정 (단위: 원)
        self.revenue_keywords = {
            "대기업": 500000000000,  # 5000억
            "중견기업": 100000000000,  # 1000억
            "중소기업": 30000000000,   # 300억
            "소기업": 10000000000,    # 100억
            "스타트업": 2000000000,   # 20억
            "벤처기업": 5000000000    # 50억
        }
    
    def extract_company_info(self, user_input: str) -> CompanyInfo:
        """자연어 입력에서 기업 정보 추출"""
        print(f" 기업 정보 추출 중: '{user_input[:50]}...'")
        
        # LLM을 활용한 구조화된 정보 추출
        extraction_prompt = f"""
다음 사용자 입력에서 기업 정보를 정확하게 추출하여 JSON 형식으로 반환해주세요.

사용자 입력: "{user_input}"

추출해야 할 정보:
1. company_name: 기업명 (필수)
2. industry: 산업/업종 (예: 자동차부품 제조업, 철강제조업)
3. location: 위치 (시/도 단위)
4. revenue: 연매출 (숫자만, 원 단위)
5. employees: 직원 수 (숫자만)
6. debt_amount: 부채 규모 (숫자만, 원 단위)
7. export_amount: 수출 규모 (숫자만, 원 단위)
8. business_description: 사업 설명
9. founded_year: 설립연도 (숫자만)

응답 형식 (JSON만):
{{
    "company_name": "기업명",
    "industry": "업종",
    "location": "위치",
    "revenue": 숫자,
    "employees": 숫자,
    "debt_amount": 숫자,
    "variable_rate_debt": 숫자,
    "export_amount": 숫자,
    "business_description": "설명",
    "founded_year": 숫자,
    "confidence_score": 0.9,
    "extracted_keywords": ["키워드1", "키워드2"]
}}

정보가 명시되지 않은 경우 기본값 사용:
- 숫자 필드: 0
- 문자 필드: ""
- variable_rate_debt는 debt_amount와 동일하게 설정
"""
        
        try:
            response = self.model.generate_content(extraction_prompt)
            
            # JSON 추출
            json_text = self._extract_json_from_response(response.text)
            if not json_text:
                raise ValueError("LLM 응답에서 JSON을 찾을 수 없습니다")
            
            extracted_data = json.loads(json_text)
            
            # 산업 분류 매핑 적용
            industry = extracted_data.get('industry', '')
            for keyword, mapped_industry in self.industry_mapping.items():
                if keyword in industry or keyword in user_input:
                    extracted_data['industry'] = mapped_industry
                    break
            
            # CompanyInfo 객체 생성
            company_info = CompanyInfo(**{
                k: v for k, v in extracted_data.items() 
                if k in CompanyInfo.__dataclass_fields__
            })
            
            # 매출 규모 추정 보완
            if company_info.revenue == 0:
                for keyword, revenue in self.revenue_keywords.items():
                    if keyword in user_input:
                        company_info.revenue = revenue
                        break
                
                # 직원 수로 매출 추정 (없는 경우)
                if company_info.revenue == 0 and company_info.employees > 0:
                    company_info.revenue = company_info.employees * 250000000  # 직원당 2.5억 가정
            
            # 변동금리 대출 기본 설정
            if company_info.variable_rate_debt == 0 and company_info.debt_amount > 0:
                company_info.variable_rate_debt = company_info.debt_amount
            
            print(f" 정보 추출 완료: {company_info.company_name} ({company_info.industry})")
            return company_info
            
        except Exception as e:
            print(f" 정보 추출 실패: {e}")
            # 기본 정보로 폴백
            return self._extract_basic_info(user_input)
    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """LLM 응답에서 JSON 부분만 추출"""
        # JSON 블록 패턴 매칭
        json_patterns = [
            r'```json\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'\{.*\}',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return match.group(1) if len(match.groups()) > 0 else match.group(0)
        
        return None
    
    def _extract_basic_info(self, user_input: str) -> CompanyInfo:
        """기본적인 규칙 기반 정보 추출 (폴백)"""
        company_name = "추출된기업명"
        industry = ""
        location = ""
        
        # 기업명 추출 (간단한 패턴)
        name_patterns = [
            r'우리는 (\w+)이고',
            r'우리는 (\w+)입니다',
            r'회사는 (\w+)이고',
            r'(\w+)에서',
            r'(\w+)은?는',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input)
            if match:
                company_name = match.group(1)
                break
        
        # 산업 추출
        for keyword, mapped_industry in self.industry_mapping.items():
            if keyword in user_input:
                industry = mapped_industry
                break
        
        # 위치 추출
        location_patterns = [
            r'(서울|부산|대구|인천|광주|대전|울산|세종)',
            r'(경기|강원|충북|충남|전북|전남|경북|경남|제주)도?',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, user_input)
            if match:
                location = match.group(1)
                break
        
        return CompanyInfo(
            company_name=company_name,
            industry=industry,
            location=location,
            confidence_score=0.3  # 낮은 신뢰도
        )
    
    def generate_user_company_creation_query(self, company_info: CompanyInfo) -> CypherQuery:
        """UserCompany 생성 Cypher 쿼리 생성"""
        print(f" {company_info.company_name} UserCompany 생성 쿼리 작성 중...")
        
        # 고유 nodeId 생성
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        node_id = f"user_company_{timestamp}"
        
        # Cypher 쿼리 생성
        query = """
        CREATE (u:UserCompany {
            nodeId: $nodeId,
            companyName: $companyName,
            industryDescription: $industry,
            location: $location,
            revenue: $revenue,
            employeeCount: $employees,
            debtAmount: $debtAmount,
            variableRateDebt: $variableRateDebt,
            exportAmount: $exportAmount,
            businessDescription: $businessDescription,
            foundedYear: $foundedYear,
            createdAt: datetime(),
            dataSource: 'user_input'
        })
        RETURN u.nodeId as nodeId, u.companyName as companyName
        """
        
        parameters = {
            'nodeId': node_id,
            'companyName': company_info.company_name,
            'industry': company_info.industry,
            'location': company_info.location,
            'revenue': company_info.revenue,
            'employees': company_info.employees,
            'debtAmount': company_info.debt_amount,
            'variableRateDebt': company_info.variable_rate_debt,
            'exportAmount': company_info.export_amount,
            'businessDescription': company_info.business_description,
            'foundedYear': company_info.founded_year
        }
        
        return CypherQuery(
            query=query.strip(),
            parameters=parameters,
            query_type="CREATE_USER_COMPANY",
            description=f"{company_info.company_name} UserCompany 노드 생성",
            confidence=company_info.confidence_score,
            timestamp=datetime.now()
        )
    
    def generate_relationship_queries(self, company_name: str) -> List[CypherQuery]:
        """UserCompany와 다른 노드들 간의 관계 생성 쿼리들"""
        print(f" {company_name} 관계 생성 쿼리들 작성 중...")
        
        queries = []
        
        # 1. MacroIndicator와 IS_EXPOSED_TO 관계
        macro_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        MATCH (m:MacroIndicator)
        CREATE (u)-[r:IS_EXPOSED_TO {
            exposureLevel: 'HIGH',
            rationale: '일반 노출',
            riskType: '기타',
            createdAt: datetime()
        }]->(m)
        RETURN count(r) as relationships_created
        """
        
        queries.append(CypherQuery(
            query=macro_query.strip(),
            parameters={'companyName': company_name},
            query_type="CREATE_MACRO_RELATIONSHIPS",
            description="거시경제지표 노출 관계 생성",
            confidence=0.9,
            timestamp=datetime.now()
        ))
        
        # 2. KB_Product와 IS_ELIGIBLE_FOR 관계
        kb_product_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        MATCH (k:KB_Product)
        WHERE k.productType = '운전자금' OR k.productType = '시설자금'
        CREATE (u)-[r:IS_ELIGIBLE_FOR {
            eligibilityScore: 0.8,
            urgency: 'MEDIUM',
            expectedBenefit: '금융비용 절감',
            createdAt: datetime()
        }]->(k)
        RETURN count(r) as relationships_created
        """
        
        queries.append(CypherQuery(
            query=kb_product_query.strip(),
            parameters={'companyName': company_name},
            query_type="CREATE_KB_PRODUCT_RELATIONSHIPS",
            description="KB 금융상품 적합성 관계 생성",
            confidence=0.8,
            timestamp=datetime.now()
        ))
        
        # 3. Policy와 IS_ELIGIBLE_FOR 관계
        policy_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        MATCH (p:Policy)
        CREATE (u)-[r:IS_ELIGIBLE_FOR {
            eligibilityScore: 0.75,
            actionRequired: '신청 검토',
            createdAt: datetime()
        }]->(p)
        RETURN count(r) as relationships_created
        """
        
        queries.append(CypherQuery(
            query=policy_query.strip(),
            parameters={'companyName': company_name},
            query_type="CREATE_POLICY_RELATIONSHIPS",
            description="정부 정책 적합성 관계 생성",
            confidence=0.7,
            timestamp=datetime.now()
        ))
        
        # 4. ReferenceCompany와 SIMILAR_TO 관계
        similar_company_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        MATCH (r:ReferenceCompany)
        WHERE r.sector = 'automotive_parts' OR r.sector = 'steel' OR r.sector = 'chemicals'
        CREATE (u)-[s:SIMILAR_TO {
            similarityScore: 0.7,
            comparisonBasis: 'industry_sector',
            createdAt: datetime()
        }]->(r)
        RETURN count(s) as relationships_created
        """
        
        queries.append(CypherQuery(
            query=similar_company_query.strip(),
            parameters={'companyName': company_name},
            query_type="CREATE_SIMILAR_COMPANY_RELATIONSHIPS",
            description="유사 기업 관계 생성",
            confidence=0.6,
            timestamp=datetime.now()
        ))
        
        return queries
    
    def convert_natural_language_to_analysis_query(self, user_question: str, company_name: str) -> CypherQuery:
        """자연어 질문을 분석용 Cypher 쿼리로 변환"""
        print(f" 질문 분석 중: '{user_question[:30]}...'")
        
        # 질문 유형 분류
        query_type = self._classify_question_type(user_question)
        
        if query_type == "risk_analysis":
            return self._generate_risk_analysis_query(company_name)
        elif query_type == "product_recommendation":
            return self._generate_product_recommendation_query(company_name)
        elif query_type == "policy_opportunities":
            return self._generate_policy_opportunities_query(company_name)
        elif query_type == "company_comparison":
            return self._generate_company_comparison_query(company_name)
        elif query_type == "news_impact":
            return self._generate_news_impact_query(company_name)
        else:
            return self._generate_general_analysis_query(company_name)
    
    def _classify_question_type(self, question: str) -> str:
        """질문 유형 분류"""
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ['리스크', '위험', '금리', '환율', '위기']):
            return "risk_analysis"
        elif any(keyword in question_lower for keyword in ['상품', '대출', 'kb', '금융', '추천']):
            return "product_recommendation"
        elif any(keyword in question_lower for keyword in ['정책', '지원', '보조금', '정부']):
            return "policy_opportunities"
        elif any(keyword in question_lower for keyword in ['비교', '경쟁사', '유사', '벤치마킹']):
            return "company_comparison"
        elif any(keyword in question_lower for keyword in ['뉴스', '영향', '시장', '동향']):
            return "news_impact"
        else:
            return "general_analysis"
    
    def _generate_risk_analysis_query(self, company_name: str) -> CypherQuery:
        """리스크 분석 쿼리 생성"""
        query = """
        MATCH (u:UserCompany {companyName: $companyName})-[r:IS_EXPOSED_TO]->(m:MacroIndicator)
        RETURN m.indicatorName as indicator,
               m.value as currentValue,
               m.changeRate as changeRate,
               r.exposureLevel as exposureLevel,
               r.rationale as rationale
        ORDER BY 
          CASE r.exposureLevel 
            WHEN 'HIGH' THEN 3 
            WHEN 'MEDIUM' THEN 2 
            ELSE 1 
          END DESC
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="RISK_ANALYSIS",
            description=f"{company_name} 리스크 노출 분석",
            confidence=0.9,
            timestamp=datetime.now()
        )
    
    def _generate_product_recommendation_query(self, company_name: str) -> CypherQuery:
        """상품 추천 쿼리 생성"""
        query = """
        MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(k:KB_Product)
        RETURN k.productName as productName,
               k.productType as productType,
               k.interestRate as interestRate,
               r.eligibilityScore as eligibilityScore,
               r.expectedBenefit as expectedBenefit
        ORDER BY r.eligibilityScore DESC
        LIMIT 10
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="PRODUCT_RECOMMENDATION", 
            description=f"{company_name} KB 금융상품 추천",
            confidence=0.8,
            timestamp=datetime.now()
        )
    
    def _generate_policy_opportunities_query(self, company_name: str) -> CypherQuery:
        """정책 기회 쿼리 생성"""
        query = """
        MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(p:Policy)
        RETURN p.policyName as policyName,
               p.issuingOrg as issuingOrg,
               p.supportField as supportField,
               r.eligibilityScore as eligibilityScore
        ORDER BY r.eligibilityScore DESC
        LIMIT 10
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="POLICY_OPPORTUNITIES",
            description=f"{company_name} 정부 정책 기회 분석",
            confidence=0.7,
            timestamp=datetime.now()
        )
    
    def _generate_company_comparison_query(self, company_name: str) -> CypherQuery:
        """기업 비교 쿼리 생성"""
        query = """
        MATCH (u:UserCompany {companyName: $companyName})-[s:SIMILAR_TO]->(r:ReferenceCompany)
        RETURN r.companyName as similarCompany,
               r.sector as sector,
               r.revenue as revenue,
               s.similarityScore as similarityScore
        ORDER BY s.similarityScore DESC
        LIMIT 10
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="COMPANY_COMPARISON",
            description=f"{company_name} 유사 기업 비교 분석",
            confidence=0.6,
            timestamp=datetime.now()
        )
    
    def _generate_news_impact_query(self, company_name: str) -> CypherQuery:
        """뉴스 영향 분석 쿼리 생성"""
        query = """
        MATCH (n:NewsArticle)-[i:HAS_IMPACT_ON]->(u:UserCompany {companyName: $companyName})
        WHERE n.publishDate > datetime() - duration({days: 30})
        RETURN n.title as newsTitle,
               n.publisher as publisher,
               n.publishDate as publishDate,
               i.impactScore as impactScore,
               i.impactDirection as impactDirection
        ORDER BY n.publishDate DESC
        LIMIT 10
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="NEWS_IMPACT",
            description=f"{company_name} 뉴스 영향 분석",
            confidence=0.5,
            timestamp=datetime.now()
        )
    
    def _generate_general_analysis_query(self, company_name: str) -> CypherQuery:
        """일반 분석 쿼리 생성"""
        query = """
        MATCH (u:UserCompany {companyName: $companyName})
        RETURN u.companyName as companyName,
               u.industryDescription as industry,
               u.revenue as revenue,
               u.employeeCount as employees,
               u.location as location
        """
        
        return CypherQuery(
            query=query.strip(),
            parameters={'companyName': company_name},
            query_type="GENERAL_ANALYSIS",
            description=f"{company_name} 기본 정보 조회",
            confidence=0.9,
            timestamp=datetime.now()
        )
    
    def save_queries_to_file(self, queries: List[CypherQuery], output_dir: str = None) -> str:
        """생성된 쿼리들을 파일로 저장"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "data", "cypher_queries")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_dir, f"generated_queries_{timestamp}.json")
        
        # JSON 직렬화를 위한 변환
        serializable_queries = []
        for query in queries:
            query_dict = asdict(query)
            query_dict['timestamp'] = query_dict['timestamp'].isoformat()
            serializable_queries.append(query_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_queries, f, ensure_ascii=False, indent=2)
        
        print(f" 쿼리 저장 완료: {file_path}")
        return file_path

def main():
    """Text-to-Cypher 시스템 테스트"""
    print("=== KB Fortress AI Text-to-Cypher 시스템 테스트 ===")
    
    try:
        engine = TextToCypherEngine()
        
        # 테스트 시나리오
        test_inputs = [
            "우리는 ABC제조이고 철강업을 합니다. 경기도에 위치하고 직원은 80명 정도입니다.",
            "삼성정밀은 자동차부품을 만드는 회사입니다. 대구에 있고 매출은 약 50억원입니다.",
            "우리 회사 금리 리스크가 궁금해요",
            "KB 대출 상품 추천해주세요",
            "정부 지원정책 있나요?",
            "경쟁사들과 비교하고 싶어요"
        ]
        
        all_queries = []
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n--- 테스트 {i}: {user_input} ---")
            
            if i <= 2:  # 기업 정보 추출 및 생성 쿼리
                # 1. 기업 정보 추출
                company_info = engine.extract_company_info(user_input)
                print(f"추출된 정보: {company_info.company_name} | {company_info.industry}")
                
                # 2. UserCompany 생성 쿼리
                creation_query = engine.generate_user_company_creation_query(company_info)
                all_queries.append(creation_query)
                
                # 3. 관계 생성 쿼리들
                relationship_queries = engine.generate_relationship_queries(company_info.company_name)
                all_queries.extend(relationship_queries)
                
                print(f" 생성된 쿼리: 1개 생성 + {len(relationship_queries)}개 관계")
                
            else:  # 분석 쿼리 (기본적으로 대한정밀 사용)
                analysis_query = engine.convert_natural_language_to_analysis_query(user_input, "대한정밀")
                all_queries.append(analysis_query)
                
                print(f" 분석 쿼리 생성: {analysis_query.query_type}")
        
        # 결과 저장
        saved_file = engine.save_queries_to_file(all_queries)
        
        print(f"\n Text-to-Cypher 테스트 완료!")
        print(f"총 {len(all_queries)}개 쿼리 생성")
        print(f"저장 위치: {saved_file}")
        
    except Exception as e:
        print(f" Text-to-Cypher 시스템 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()