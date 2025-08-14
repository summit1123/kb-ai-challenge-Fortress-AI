#!/usr/bin/env python3
"""
Dynamic UserCompany Creation System for KB Fortress AI
사용자 입력으로부터 동적으로 UserCompany 노드를 생성하고 모든 관계를 연결하는 시스템
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
from neo4j_manager import Neo4jManager
# from kb_text_to_cypher_agent import TextToCypherEngine, CompanyInfo, CypherQuery

# 간단한 데이터 클래스 정의
@dataclass
class CompanyInfo:
    company_name: str
    industry: str
    location: str
    revenue: int
    employees: int
    debt: int
    
@dataclass 
class CypherQuery:
    query: str
    parameters: dict

class TextToCypherEngine:
    """간단한 TextToCypher 엔진 mock"""
    def extract_company_info(self, text: str) -> CompanyInfo:
        # 간단한 파싱 로직
        import re
        
        name_match = re.search(r'(?:회사명|기업명|제조기업명):\s*([^\n]+)', text)
        industry_match = re.search(r'(?:업종|제조분야|제조업분야):\s*([^\n]+)', text)
        location_match = re.search(r'(?:위치|소재지|생산기지):\s*([^\n]+)', text)
        revenue_match = re.search(r'(?:매출|연매출):\s*(\d+)', text)
        employees_match = re.search(r'(?:직원|직원수):\s*(\d+)', text)  
        debt_match = re.search(r'(?:부채|총부채):\s*(\d+)', text)
        
        return CompanyInfo(
            company_name=name_match.group(1).strip() if name_match else "테스트기업",
            industry=industry_match.group(1).strip() if industry_match else "제조업",
            location=location_match.group(1).strip() if location_match else "경기도",
            revenue=int(revenue_match.group(1)) if revenue_match else 100,
            employees=int(employees_match.group(1)) if employees_match else 50,
            debt=int(debt_match.group(1)) if debt_match else 30
        )
    
    def generate_user_company_creation_query(self, info: CompanyInfo) -> CypherQuery:
        query = f"""
        CREATE (u:UserCompany {{
            nodeId: '{info.company_name.replace(' ', '_').lower()}_' + toString(timestamp()),
            companyName: $company_name,
            industryDescription: $industry,
            location: $location,
            revenue: $revenue,
            employeeCount: $employees,
            debtAmount: $debt,
            createdAt: datetime()
        }})
        RETURN u.nodeId as nodeId
        """
        return CypherQuery(
            query=query,
            parameters={
                'company_name': info.company_name,
                'industry': info.industry,
                'location': info.location,
                'revenue': info.revenue,
                'employees': info.employees,
                'debt': info.debt
            }
        )
    
    def generate_relationship_queries(self, company_name: str) -> List[CypherQuery]:
        return []  # 관계 생성은 단순화

@dataclass
class CreationResult:
    """UserCompany 생성 결과"""
    success: bool
    company_name: str
    node_id: Optional[str] = None
    created_relationships: Dict[str, int] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 0.0

class DynamicUserCompanyManager:
    """동적 UserCompany 노드 생성 및 관리 시스템"""
    
    def __init__(self):
        # 환경변수 설정
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'  
        os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'
        
        self.neo4j_manager = Neo4jManager()
        self.text_to_cypher = TextToCypherEngine()
        
        print(" 동적 UserCompany 관리자 초기화 완료")
        
    def create_user_company_from_input(self, user_input: str) -> CreationResult:
        """사용자 입력으로부터 UserCompany 노드 및 모든 관계 생성"""
        start_time = datetime.now()
        
        print(f"️  사용자 입력으로부터 UserCompany 생성 시작...")
        print(f"입력: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")
        
        try:
            # 1. 기업 정보 추출
            company_info = self.text_to_cypher.extract_company_info(user_input)
            print(f" 추출된 기업: {company_info.company_name} ({company_info.industry})")
            
            # 2. 기존 UserCompany 중복 확인
            if self._check_existing_user_company(company_info.company_name):
                return CreationResult(
                    success=False,
                    company_name=company_info.company_name,
                    error_message=f"UserCompany '{company_info.company_name}'이 이미 존재합니다.",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 3. UserCompany 노드 생성
            creation_query = self.text_to_cypher.generate_user_company_creation_query(company_info)
            node_result = self._execute_cypher_query(creation_query)
            
            if not node_result['success']:
                return CreationResult(
                    success=False,
                    company_name=company_info.company_name,
                    error_message=f"UserCompany 노드 생성 실패: {node_result['error']}",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 노드 ID 추출
            node_id = node_result['results'][0]['nodeId'] if node_result['results'] else None
            print(f" UserCompany 노드 생성 완료: {node_id}")
            
            # 4. 관계 생성
            relationship_queries = self.text_to_cypher.generate_relationship_queries(company_info.company_name)
            relationship_counts = {}
            
            for rel_query in relationship_queries:
                print(f" {rel_query.description} 진행 중...")
                rel_result = self._execute_cypher_query(rel_query)
                
                if rel_result['success'] and rel_result['results']:
                    count = rel_result['results'][0].get('relationships_created', 0)
                    relationship_counts[rel_query.query_type] = count
                    print(f"    {count}개 관계 생성 완료")
                else:
                    relationship_counts[rel_query.query_type] = 0
                    print(f"   ️ 관계 생성 실패: {rel_result.get('error', '알 수 없는 오류')}")
            
            # 5. 생성 결과 요약
            total_relationships = sum(relationship_counts.values())
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f" '{company_info.company_name}' UserCompany 생성 완료!")
            print(f"   - 노드 ID: {node_id}")
            print(f"   - 총 관계: {total_relationships}개")
            print(f"   - 실행 시간: {execution_time:.2f}초")
            
            return CreationResult(
                success=True,
                company_name=company_info.company_name,
                node_id=node_id,
                created_relationships=relationship_counts,
                execution_time=execution_time,
                confidence_score=company_info.confidence_score
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f" UserCompany 생성 실패: {e}")
            
            return CreationResult(
                success=False,
                company_name=getattr(company_info, 'company_name', '알 수 없음'),
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _check_existing_user_company(self, company_name: str) -> bool:
        """기존 UserCompany 노드 존재 여부 확인"""
        check_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        RETURN u.companyName as companyName
        """
        
        try:
            results = self.neo4j_manager.execute_query(check_query, {'companyName': company_name})
            return len(results) > 0
        except Exception as e:
            print(f"️ 중복 확인 실패: {e}")
            return False
    
    def _execute_cypher_query(self, cypher_query: CypherQuery) -> Dict[str, Any]:
        """Cypher 쿼리 실행 및 결과 반환"""
        try:
            results = self.neo4j_manager.execute_query(cypher_query.query, cypher_query.parameters)
            return {
                'success': True,
                'results': results,
                'query_type': cypher_query.query_type,
                'description': cypher_query.description
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query_type': cypher_query.query_type,
                'description': cypher_query.description
            }
    
    def get_user_company_analysis(self, company_name: str) -> Dict[str, Any]:
        """생성된 UserCompany의 분석 데이터 조회"""
        print(f" {company_name} 분석 데이터 조회...")
        
        analysis_queries = {
            "basic_info": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})
                RETURN u.companyName as companyName,
                       u.industryDescription as industry,
                       u.location as location,
                       u.revenue as revenue,
                       u.employeeCount as employees,
                       u.nodeId as nodeId,
                       u.createdAt as createdAt
                """,
                "description": "기본 정보"
            },
            
            "macro_exposure": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_EXPOSED_TO]->(m:MacroIndicator)
                RETURN m.indicatorName as indicator,
                       m.value as value,
                       r.exposureLevel as level
                ORDER BY 
                  CASE r.exposureLevel 
                    WHEN 'HIGH' THEN 3 
                    WHEN 'MEDIUM' THEN 2 
                    ELSE 1 
                  END DESC
                """,
                "description": "거시경제 노출도"
            },
            
            "kb_products": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(k:KB_Product)
                RETURN k.productName as product,
                       k.productType as type,
                       r.eligibilityScore as score
                ORDER BY r.eligibilityScore DESC
                LIMIT 10
                """,
                "description": "KB 추천상품"
            },
            
            "policies": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[r:IS_ELIGIBLE_FOR]->(p:Policy)
                RETURN p.policyName as policy,
                       p.supportField as field,
                       r.eligibilityScore as score
                ORDER BY r.eligibilityScore DESC
                LIMIT 5
                """,
                "description": "정부 정책"
            },
            
            "similar_companies": {
                "query": """
                MATCH (u:UserCompany {companyName: $companyName})-[s:SIMILAR_TO]->(r:ReferenceCompany)
                RETURN r.companyName as similar_company,
                       r.sector as sector,
                       s.similarityScore as similarity
                ORDER BY s.similarityScore DESC
                LIMIT 5
                """,
                "description": "유사 기업"
            }
        }
        
        analysis_result = {
            "company_name": company_name,
            "analysis_timestamp": datetime.now(),
            "analyses": {}
        }
        
        for analysis_name, query_info in analysis_queries.items():
            try:
                results = self.neo4j_manager.execute_query(
                    query_info["query"], 
                    {'companyName': company_name}
                )
                
                analysis_result["analyses"][analysis_name] = {
                    "description": query_info["description"],
                    "count": len(results),
                    "data": results
                }
                
                print(f"    {query_info['description']}: {len(results)}개")
                
            except Exception as e:
                analysis_result["analyses"][analysis_name] = {
                    "description": query_info["description"],
                    "error": str(e),
                    "count": 0,
                    "data": []
                }
                print(f"    {query_info['description']} 실패: {e}")
        
        return analysis_result
    
    def delete_user_company(self, company_name: str) -> bool:
        """UserCompany 노드 및 모든 관계 삭제"""
        print(f"️ {company_name} UserCompany 삭제 중...")
        
        delete_query = """
        MATCH (u:UserCompany {companyName: $companyName})
        DETACH DELETE u
        RETURN count(u) as deleted_count
        """
        
        try:
            results = self.neo4j_manager.execute_query(delete_query, {'companyName': company_name})
            deleted_count = results[0]['deleted_count'] if results else 0
            
            if deleted_count > 0:
                print(f" {company_name} UserCompany 삭제 완료")
                return True
            else:
                print(f"️ {company_name} UserCompany를 찾을 수 없습니다")
                return False
                
        except Exception as e:
            print(f" {company_name} UserCompany 삭제 실패: {e}")
            return False
    
    def list_all_user_companies(self) -> List[Dict[str, Any]]:
        """모든 UserCompany 목록 조회"""
        list_query = """
        MATCH (u:UserCompany)
        RETURN u.companyName as companyName,
               u.industryDescription as industry,
               u.location as location,
               u.revenue as revenue,
               u.nodeId as nodeId,
               u.createdAt as createdAt
        ORDER BY u.createdAt DESC
        """
        
        try:
            results = self.neo4j_manager.execute_query(list_query)
            print(f" 총 {len(results)}개 UserCompany 발견")
            return results
        except Exception as e:
            print(f" UserCompany 목록 조회 실패: {e}")
            return []
    
    def save_creation_log(self, creation_result: CreationResult, output_dir: str = None) -> str:
        """UserCompany 생성 로그 저장"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "data", "creation_logs")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_name_safe = creation_result.company_name.replace(' ', '_')
        file_path = os.path.join(output_dir, f"create_{company_name_safe}_{timestamp}.json")
        
        # JSON 직렬화
        log_data = {
            "creation_result": {
                "success": creation_result.success,
                "company_name": creation_result.company_name,
                "node_id": creation_result.node_id,
                "created_relationships": creation_result.created_relationships,
                "error_message": creation_result.error_message,
                "execution_time": creation_result.execution_time,
                "confidence_score": creation_result.confidence_score
            },
            "timestamp": datetime.now().isoformat(),
            "system_version": "dynamic_user_company_v1.0"
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f" 생성 로그 저장: {file_path}")
        return file_path
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """Dynamic UserCompany 시스템 테스트"""
    print("=== KB Fortress AI Dynamic UserCompany 시스템 테스트 ===")
    
    manager = DynamicUserCompanyManager()
    
    try:
        # 테스트 시나리오
        test_scenarios = [
            "우리는 테크스틸이고 섬유제조업을 합니다. 부산에 위치하고 직원 60명, 매출 150억원입니다.",
            "KB화학은 화학제품을 만드는 회사입니다. 울산에 있고 직원 200명, 연매출 500억원 규모입니다.",
        ]
        
        creation_results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*60}")
            print(f"테스트 시나리오 {i}")
            print(f"{'='*60}")
            
            # UserCompany 생성
            result = manager.create_user_company_from_input(scenario)
            creation_results.append(result)
            
            if result.success:
                # 생성 로그 저장
                log_path = manager.save_creation_log(result)
                
                # 분석 데이터 조회
                analysis = manager.get_user_company_analysis(result.company_name)
                print(f"\n {result.company_name} 분석 요약:")
                for analysis_name, analysis_data in analysis.get("analyses", {}).items():
                    count = analysis_data.get("count", 0)
                    desc = analysis_data.get("description", analysis_name)
                    print(f"   - {desc}: {count}개")
                
            else:
                print(f" 생성 실패: {result.error_message}")
            
            print(f"\n실행 시간: {result.execution_time:.2f}초")
        
        # 전체 UserCompany 목록 조회
        print(f"\n{'='*60}")
        print("전체 UserCompany 목록")
        print(f"{'='*60}")
        all_companies = manager.list_all_user_companies()
        for company in all_companies:
            print(f"- {company['companyName']} ({company.get('industry', 'N/A')}) | {company.get('nodeId', 'N/A')}")
        
        # 성공 통계
        successful_creations = [r for r in creation_results if r.success]
        print(f"\n 테스트 완료!")
        print(f"성공: {len(successful_creations)}/{len(creation_results)}")
        print(f"평균 실행 시간: {sum(r.execution_time for r in creation_results)/len(creation_results):.2f}초")
        
    except Exception as e:
        print(f" 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()