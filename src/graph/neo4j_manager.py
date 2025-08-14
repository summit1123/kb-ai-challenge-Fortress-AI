import os
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import logging

class Neo4jManager:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        # 비밀번호 특수문자 처리
        raw_password = password or os.getenv("NEO4J_PASSWORD")
        self.password = raw_password if raw_password else None
        
        if not self.password:
            raise ValueError("Neo4j password not found in environment variables")
        
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Neo4j 데이터베이스 연결"""
        try:
            # neo4j 프로토콜 사용 (최신 버전 권장)
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # 연결 테스트
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"Neo4j 연결 성공: {self.uri}")
        except Exception as e:
            print(f"Neo4j 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
    
    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Cypher 쿼리 실행"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logging.error(f"쿼리 실행 오류: {e}")
            return []
    
    def create_constraints_and_indexes(self):
        """기본 제약조건 및 인덱스 생성"""
        constraints = [
            "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
            "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.policyId IS UNIQUE",
            "CREATE CONSTRAINT indicator_id IF NOT EXISTS FOR (m:MacroIndicator) REQUIRE m.indicatorId IS UNIQUE",
            "CREATE CONSTRAINT news_id IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.newsId IS UNIQUE",
            "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (k:KB_Product) REQUIRE k.productId IS UNIQUE"
        ]
        
        indexes = [
            "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.companyName)",
            "CREATE INDEX policy_name IF NOT EXISTS FOR (p:Policy) ON (p.policyName)",
            "CREATE INDEX indicator_name IF NOT EXISTS FOR (m:MacroIndicator) ON (m.indicatorName)",
            "CREATE INDEX product_name IF NOT EXISTS FOR (k:KB_Product) ON (k.productName)"
        ]
        
        for constraint in constraints:
            try:
                self.execute_query(constraint)
                print(f"제약조건 생성 성공: {constraint.split()[2]}")
            except Exception as e:
                print(f"제약조건 생성 실패: {e}")
        
        for index in indexes:
            try:
                self.execute_query(index)
                print(f"인덱스 생성 성공: {index.split()[2]}")
            except Exception as e:
                print(f"인덱스 생성 실패: {e}")
    
    def clear_database(self):
        """데이터베이스 초기화 (개발용)"""
        confirm = input("데이터베이스를 완전히 초기화하시겠습니까? (yes/no): ")
        if confirm.lower() == 'yes':
            self.execute_query("MATCH (n) DETACH DELETE n")
            print("데이터베이스 초기화 완료")
        else:
            print("초기화 취소됨")
    
    def get_stats(self) -> Dict:
        """데이터베이스 통계 조회"""
        stats_query = """
        MATCH (n)
        WITH labels(n) as labels
        UNWIND labels as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """
        
        results = self.execute_query(stats_query)
        return {result["label"]: result["count"] for result in results}
    
    def test_connection(self) -> bool:
        """연결 상태 테스트"""
        try:
            result = self.execute_query("RETURN 'connection_test' as test")
            return len(result) > 0 and result[0].get("test") == "connection_test"
        except:
            return False

def test_neo4j_connection():
    """Neo4j 연결 테스트 함수"""
    print("Neo4j 연결 테스트 시작...")
    
    try:
        manager = Neo4jManager()
        
        if manager.test_connection():
            print(" Neo4j 연결 테스트 성공")
            
            # 기본 제약조건 및 인덱스 생성
            manager.create_constraints_and_indexes()
            
            # 통계 조회
            stats = manager.get_stats()
            print(f"\n현재 데이터베이스 통계:")
            for label, count in stats.items():
                print(f"  {label}: {count}개")
            
            return True
        else:
            print(" Neo4j 연결 테스트 실패")
            return False
            
    except Exception as e:
        print(f" Neo4j 연결 오류: {e}")
        return False
    finally:
        if 'manager' in locals():
            manager.close()

if __name__ == "__main__":
    test_neo4j_connection()