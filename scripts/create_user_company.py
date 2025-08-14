#!/usr/bin/env python3
"""
UserCompany 생성 및 분석 시스템
사용자 기업 정보를 입력받아 분석 가능한 노드 생성
"""

import os
import sys
from typing import Dict, List
from datetime import datetime

sys.path.append('/Users/gimdonghyeon/Desktop/kb-ai-challenge')

os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
os.environ['NEO4J_USER'] = 'neo4j'
os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'

from src.graph.neo4j_manager import Neo4jManager

class UserCompanyAnalyzer:
    def __init__(self):
        self.manager = Neo4jManager()
        print(" UserCompany 분석 시스템 준비 완료")
    
    def create_user_company(self, user_input: Dict) -> str:
        """사용자 기업 노드 생성"""
        company_id = f"user_company_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # UserCompany 노드 생성
        query = """
        CREATE (u:UserCompany {
            nodeId: $nodeId,
            companyName: $companyName,
            industryDescription: $industryDescription,
            revenue: $revenue,
            employeeCount: $employeeCount,
            debtAmount: $debtAmount,
            variableRateDebt: $variableRateDebt,
            exportAmount: $exportAmount,
            location: $location,
            inputMethod: 'text',
            createdAt: datetime()
        })
        RETURN u
        """
        
        params = {
            "nodeId": company_id,
            "companyName": user_input.get('company_name', '미입력'),
            "industryDescription": user_input.get('industry', ''),
            "revenue": user_input.get('revenue', 0),
            "employeeCount": user_input.get('employees', 0),
            "debtAmount": user_input.get('debt_amount', 0),
            "variableRateDebt": user_input.get('variable_rate_debt', 0),
            "exportAmount": user_input.get('export_amount', 0),
            "location": user_input.get('location', '')
        }
        
        self.manager.execute_query(query, params)
        print(f" UserCompany 생성: {params['companyName']}")
        
        return company_id
    
    def match_similar_companies(self, user_company_id: str):
        """유사한 ReferenceCompany 매칭"""
        
        # 1. 업종 키워드 기반 매칭
        match_query = """
        MATCH (u:UserCompany {nodeId: $userCompanyId})
        MATCH (r:ReferenceCompany)
        WITH u, r,
             CASE 
                WHEN u.industryDescription CONTAINS '자동차' AND r.sector = 'automotive_parts' THEN 0.8
                WHEN u.industryDescription CONTAINS '철강' AND r.sector = 'steel' THEN 0.8
                WHEN u.industryDescription CONTAINS '화학' AND r.sector = 'chemicals' THEN 0.8
                ELSE 0.3
             END as sectorScore,
             ABS(u.revenue - r.revenue) / r.revenue as revenueDiff
        WITH u, r, 
             sectorScore,
             CASE WHEN revenueDiff < 0.5 THEN 0.2 ELSE 0.0 END as revenueScore,
             sectorScore + (1 - revenueDiff) * 0.2 as totalScore
        WHERE totalScore > 0.3
        MERGE (u)-[s:SIMILAR_TO]->(r)
        SET s.similarityScore = totalScore,
            s.matchingFactors = ['sector: ' + r.sector, 'revenue_diff: ' + toString(revenueDiff)]
        RETURN u.companyName as userCompany, r.companyName as similarCompany, s.similarityScore as score
        ORDER BY score DESC
        """
        
        results = self.manager.execute_query(match_query, {"userCompanyId": user_company_id})
        
        print("\n 유사 기업 매칭 결과:")
        for result in results:
            print(f"  {result['userCompany']} ↔ {result['similarCompany']} (유사도: {result['score']:.2f})")
    
    def analyze_user_company_risks(self, user_company_id: str):
        """UserCompany 리스크 분석"""
        
        # 1. 유사 기업의 리스크 패턴 상속
        risk_query = """
        MATCH (u:UserCompany {nodeId: $userCompanyId})-[s:SIMILAR_TO]->(r:ReferenceCompany)
        MATCH (r)-[e:IS_EXPOSED_TO]->(m:MacroIndicator)
        WITH u, m, MAX(s.similarityScore * 
             CASE e.exposureLevel 
                WHEN 'HIGH' THEN 0.9 
                WHEN 'MEDIUM' THEN 0.6 
                ELSE 0.3 
             END) as riskScore
        MERGE (u)-[ue:IS_EXPOSED_TO]->(m)
        SET ue.exposureLevel = CASE 
                WHEN riskScore > 0.7 THEN 'HIGH'
                WHEN riskScore > 0.4 THEN 'MEDIUM'
                ELSE 'LOW'
            END,
            ue.rationale = '유사 기업 패턴 기반 리스크 분석',
            ue.riskType = CASE 
                WHEN m.indicatorName CONTAINS '금리' THEN 'interest_rate'
                WHEN m.indicatorName CONTAINS '환율' THEN 'exchange_rate'
                ELSE 'other'
            END
        RETURN u.companyName as company, m.indicatorName as indicator, ue.exposureLevel as level
        """
        
        results = self.manager.execute_query(risk_query, {"userCompanyId": user_company_id})
        
        print("\n️  리스크 노출 분석:")
        for result in results:
            print(f"  {result['company']} → {result['indicator']} (노출도: {result['level']})")
    
    def recommend_solutions(self, user_company_id: str):
        """UserCompany를 위한 솔루션 추천"""
        
        # 1. 정책 추천
        policy_query = """
        MATCH (u:UserCompany {nodeId: $userCompanyId})-[:SIMILAR_TO]->(r:ReferenceCompany)
        MATCH (r)-[e:IS_ELIGIBLE_FOR]->(p:Policy)
        WITH u, p, MAX(e.eligibilityScore) as maxScore
        WHERE maxScore > 0.5
        MERGE (u)-[ue:IS_ELIGIBLE_FOR]->(p)
        SET ue.eligibilityScore = maxScore * 0.8,
            ue.recommendationReason = '유사 기업 적격 정책'
        RETURN p.policyName as policy, ue.eligibilityScore as score
        ORDER BY score DESC
        LIMIT 5
        """
        
        policies = self.manager.execute_query(policy_query, {"userCompanyId": user_company_id})
        
        print("\n 추천 정책:")
        for p in policies:
            print(f"  - {p['policy']} (적합도: {p['score']:.2f})")
        
        # 2. KB 상품 추천
        product_query = """
        MATCH (u:UserCompany {nodeId: $userCompanyId})-[:IS_EXPOSED_TO]->(m:MacroIndicator)
        WHERE u.variableRateDebt > 0
        MATCH (k:KB_Product)
        WHERE (m.indicatorName CONTAINS '금리' AND k.productName CONTAINS '금리') OR
              (m.indicatorName CONTAINS '환율' AND k.productName CONTAINS '수출')
        WITH u, k, COUNT(m) as riskCount
        MERGE (u)-[r:IS_ELIGIBLE_FOR]->(k)
        SET r.eligibilityScore = 0.7 + (riskCount * 0.1),
            r.recommendationReason = '리스크 헤지 상품'
        RETURN k.productName as product, r.eligibilityScore as score
        ORDER BY score DESC
        LIMIT 5
        """
        
        products = self.manager.execute_query(product_query, {"userCompanyId": user_company_id})
        
        print("\n 추천 KB 상품:")
        for p in products:
            print(f"  - {p['product']} (적합도: {p['score']:.2f})")
    
    def create_analysis_view(self, user_company_id: str):
        """분석 결과 시각화 쿼리 생성"""
        
        print(f"\n 시각화를 위한 Cypher 쿼리:")
        print(f"""
MATCH (u:UserCompany {{nodeId: '{user_company_id}'}})
OPTIONAL MATCH (u)-[s:SIMILAR_TO]->(r:ReferenceCompany)
OPTIONAL MATCH (u)-[e:IS_EXPOSED_TO]->(m:MacroIndicator)
OPTIONAL MATCH (u)-[el:IS_ELIGIBLE_FOR]->(solution)
OPTIONAL MATCH (n:NewsArticle)-[i:HAS_IMPACT_ON]->(u)
RETURN u, s, r, e, m, el, solution, i, n
        """)

# 사용 예시
def demo_user_company():
    """데모: 사용자 기업 생성 및 분석"""
    
    analyzer = UserCompanyAnalyzer()
    
    # 사용자 입력 예시 (대한정밀)
    user_input = {
        'company_name': '대한정밀',
        'industry': '자동차 부품 제조업',
        'revenue': 120000000000,  # 1200억
        'employees': 450,
        'debt_amount': 50000000000,  # 500억
        'variable_rate_debt': 40000000000,  # 400억 (80%)
        'export_amount': 48000000000,  # 480억 (40%)
        'location': '경기도 화성시'
    }
    
    print(" 사용자 기업 정보:")
    print(f"  기업명: {user_input['company_name']}")
    print(f"  업종: {user_input['industry']}")
    print(f"  매출: {user_input['revenue']:,}원")
    print(f"  변동금리부채: {user_input['variable_rate_debt']:,}원")
    
    # 1. UserCompany 생성
    company_id = analyzer.create_user_company(user_input)
    
    # 2. 유사 기업 매칭
    analyzer.match_similar_companies(company_id)
    
    # 3. 리스크 분석
    analyzer.analyze_user_company_risks(company_id)
    
    # 4. 솔루션 추천
    analyzer.recommend_solutions(company_id)
    
    # 5. 시각화 쿼리 제공
    analyzer.create_analysis_view(company_id)

def create_persona_1_company():
    """페르소나 1: 금리 민감 제조업체 생성"""
    
    analyzer = UserCompanyAnalyzer()
    
    # 페르소나 1: 대한정밀 (금리 민감 자동차부품 제조업체)
    user_input = {
        'company_name': '대한정밀',
        'industry': '자동차 부품 제조업 (현대자동차 1차 협력사)',
        'revenue': 30000000000,  # 300억
        'employees': 120,
        'debt_amount': 8000000000,  # 80억
        'variable_rate_debt': 8000000000,  # 80억 (100% 변동금리)
        'export_amount': 6000000000,  # 60억 (20%)
        'location': '경기도 화성시',
        'main_concern': '금리인상에 따른 이자부담 증가',
        'monthly_interest': 32000000,  # 월 3,200만원
        'fixed_cost_ratio': 0.65  # 고정비 65%
    }
    
    print("\n 페르소나 1: 금리 민감 제조업체")
    print("━" * 50)
    print(f" 기업 프로필:")
    print(f"  기업명: {user_input['company_name']}")
    print(f"  대표: 박철수 (52세)")
    print(f"  업종: {user_input['industry']}")
    print(f"  위치: {user_input['location']}")
    print(f"\n 재무 현황:")
    print(f"  연매출: {user_input['revenue']:,}원")
    print(f"  직원수: {user_input['employees']}명")
    print(f"  변동금리 대출: {user_input['variable_rate_debt']:,}원")
    print(f"  월 이자: {user_input['monthly_interest']:,}원")
    print(f"\n 주요 고민:")
    print(f"  '{user_input['main_concern']}'")
    print(f"  '금리 0.5% 상승 시 월 1,600만원 추가 부담'")
    print("━" * 50)
    
    # 1. UserCompany 생성
    company_id = analyzer.create_user_company(user_input)
    
    # 2. 유사 기업 매칭
    analyzer.match_similar_companies(company_id)
    
    # 3. 리스크 분석
    analyzer.analyze_user_company_risks(company_id)
    
    # 4. 솔루션 추천
    analyzer.recommend_solutions(company_id)
    
    # 5. 시각화 쿼리 제공
    analyzer.create_analysis_view(company_id)
    
    # 6. 맞춤형 분석 리포트
    print("\n 맞춤형 분석 리포트:")
    print("━" * 50)
    print("️  긴급도: 높음")
    print("\n1. 금리 리스크 분석")
    print("  - 현재 변동금리 노출도: 100%")
    print("  - 기준금리 0.25%p 인상 시: 월 800만원 추가")
    print("  - 기준금리 0.50%p 인상 시: 월 1,600만원 추가")
    print("\n2. 업종 특성 리스크")
    print("  - 자동차 산업 둔화로 납품단가 인하 압력")
    print("  - 고정비 비중 65%로 수익성 악화 위험")
    print("\n3. 즉시 실행 가능한 솔루션")
    print("   KB 금리스왑 상품으로 50% 헤지")
    print("   KB 중소기업 고정금리 대환대출 (3년 고정)")
    print("   정부 제조업 금리지원 프로그램 신청")
    print("━" * 50)
    
    return company_id

if __name__ == "__main__":
    # 기존 데모 대신 페르소나 1 생성
    create_persona_1_company()