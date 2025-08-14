import json
import os
from typing import List, Dict, Any
from neo4j_manager import Neo4jManager
from schema import KB_Product, NodeType
from datetime import datetime

class KBProductLoader:
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
    
    def load_kb_products_from_json(self, json_path: str = "data/raw/kb_actual_products.json") -> List[KB_Product]:
        """JSON 파일에서 KB 상품 데이터 로드"""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        
        kb_products = []
        for product_data in products_data:
            # 데이터 정제
            kb_product = KB_Product(
                node_id=f"kb_product_{len(kb_products)+1:03d}",
                node_type=NodeType.KB_PRODUCT.value,
                created_at=datetime.now(),
                product_name=product_data.get("product_name", ""),
                product_type=product_data.get("product_type", ""),
                target_customer=product_data.get("target_customer", ""),
                loan_limit=product_data.get("loan_limit", ""),
                interest_rate=product_data.get("interest_rate", ""),
                collateral=product_data.get("collateral", ""),
                credit_grade_min=product_data.get("credit_grade_min", ""),
                loan_period=product_data.get("loan_period", ""),
                special_conditions=product_data.get("special_conditions", ""),
                description=product_data.get("description", "")[:500]  # 설명은 500자로 제한
            )
            kb_products.append(kb_product)
        
        print(f"JSON에서 {len(kb_products)}개 KB 상품 로드 완료")
        return kb_products
    
    def create_kb_product_nodes(self, kb_products: List[KB_Product]) -> bool:
        """KB 상품 노드를 Neo4j에 생성"""
        try:
            create_query = """
            CREATE (p:KB_Product {
                nodeId: $nodeId,
                nodeType: $nodeType,
                createdAt: $createdAt,
                productName: $productName,
                productType: $productType,
                targetCustomer: $targetCustomer,
                loanLimit: $loanLimit,
                interestRate: $interestRate,
                collateral: $collateral,
                creditGradeMin: $creditGradeMin,
                loanPeriod: $loanPeriod,
                specialConditions: $specialConditions,
                description: $description
            })
            """
            
            success_count = 0
            for product in kb_products:
                try:
                    product_dict = product.to_dict()
                    self.neo4j_manager.execute_query(create_query, product_dict)
                    success_count += 1
                except Exception as e:
                    print(f"상품 생성 실패: {product.product_name} - {e}")
            
            print(f" {success_count}/{len(kb_products)}개 KB 상품 노드 생성 완료")
            return success_count == len(kb_products)
            
        except Exception as e:
            print(f" KB 상품 노드 생성 오류: {e}")
            return False
    
    def create_sample_company_node(self):
        """샘플 기업 노드 생성 (테스트용)"""
        create_company_query = """
        CREATE (c:Company {
            nodeId: "company_daehan_precision",
            nodeType: "Company",
            createdAt: $createdAt,
            companyName: "대한정밀",
            industryCode: "C28",
            location: "경기도 안산시",
            revenueRange: "50억~100억",
            debtInfo: "총 부채 15억원 (변동금리 대출 10억원)",
            employeeCount: 45,
            establishmentYear: 2010,
            businessType: "자동차부품 제조업"
        })
        """
        
        try:
            self.neo4j_manager.execute_query(create_company_query, {
                "createdAt": datetime.now().isoformat()
            })
            print(" 샘플 기업 노드 생성 완료: 대한정밀")
            return True
        except Exception as e:
            print(f" 샘플 기업 노드 생성 실패: {e}")
            return False
    
    def create_eligibility_relationships(self):
        """기업과 KB 상품 간 자격 관계 생성"""
        # 대한정밀이 자격을 갖춘 상품들과 연결
        eligible_products = [
            ("KB 중소기업 우대대출", 0.9, "매출규모 및 업력 조건 충족"),
            ("KB 수출기업 우대대출", 0.7, "자동차부품 수출실적 보유"),
            ("KB 플러스론", 0.8, "신용등급 및 담보 조건 양호"),
            ("정책자금대출", 0.9, "중소기업 정책자금 대상")
        ]
        
        create_relationship_query = """
        MATCH (c:Company {nodeId: "company_daehan_precision"})
        MATCH (p:KB_Product {productName: $productName})
        CREATE (c)-[r:IS_ELIGIBLE_FOR {
            eligibilityScore: $eligibilityScore,
            matchingConditions: $matchingConditions,
            recommendationReason: $recommendationReason,
            createdAt: $createdAt
        }]->(p)
        """
        
        success_count = 0
        for product_name, score, reason in eligible_products:
            try:
                self.neo4j_manager.execute_query(create_relationship_query, {
                    "productName": product_name,
                    "eligibilityScore": score,
                    "matchingConditions": reason,
                    "recommendationReason": f"대한정밀의 {reason}으로 추천",
                    "createdAt": datetime.now().isoformat()
                })
                success_count += 1
                print(f" 자격 관계 생성: 대한정밀 → {product_name}")
            except Exception as e:
                print(f" 자격 관계 생성 실패: {product_name} - {e}")
        
        print(f"총 {success_count}개 자격 관계 생성 완료")
        return success_count
    
    def verify_data_loading(self):
        """데이터 로딩 검증"""
        stats_queries = {
            "KB 상품 수": "MATCH (p:KB_Product) RETURN count(p) as count",
            "기업 수": "MATCH (c:Company) RETURN count(c) as count",
            "자격 관계 수": "MATCH ()-[r:IS_ELIGIBLE_FOR]->() RETURN count(r) as count"
        }
        
        print("\n=== 데이터 로딩 검증 ===")
        for description, query in stats_queries.items():
            try:
                result = self.neo4j_manager.execute_query(query)
                count = result[0]["count"] if result else 0
                print(f"{description}: {count}개")
            except Exception as e:
                print(f"{description} 조회 실패: {e}")
        
        # 샘플 상품 목록 조회
        sample_query = """
        MATCH (p:KB_Product)
        RETURN p.productName as name, p.productType as type, p.targetCustomer as target
        LIMIT 5
        """
        
        try:
            results = self.neo4j_manager.execute_query(sample_query)
            print("\n샘플 상품 목록:")
            for result in results:
                print(f"  - {result['name']} ({result['type']}) - {result['target']}")
        except Exception as e:
            print(f"샘플 상품 조회 실패: {e}")
    
    def run_full_loading_process(self):
        """전체 데이터 로딩 프로세스 실행"""
        print("=== KB 상품 데이터 로딩 시작 ===")
        
        try:
            # 1. JSON에서 KB 상품 데이터 로드
            kb_products = self.load_kb_products_from_json()
            
            # 2. KB 상품 노드 생성
            if self.create_kb_product_nodes(kb_products):
                print(" KB 상품 노드 생성 성공")
            else:
                print(" KB 상품 노드 생성 실패")
                return False
            
            # 3. 샘플 기업 노드 생성
            if self.create_sample_company_node():
                print(" 샘플 기업 노드 생성 성공")
            else:
                print(" 샘플 기업 노드 생성 실패")
            
            # 4. 자격 관계 생성
            relationship_count = self.create_eligibility_relationships()
            if relationship_count > 0:
                print(" 자격 관계 생성 성공")
            else:
                print(" 자격 관계 생성 실패")
            
            # 5. 데이터 로딩 검증
            self.verify_data_loading()
            
            print("\n=== KB 상품 데이터 로딩 완료 ===")
            return True
            
        except Exception as e:
            print(f" 데이터 로딩 프로세스 오류: {e}")
            return False
        finally:
            self.neo4j_manager.close()

def main():
    loader = KBProductLoader()
    loader.run_full_loading_process()

if __name__ == "__main__":
    main()