#!/usr/bin/env python3
"""
소규모 배치로 나누어 그래프 구축
타임아웃 방지를 위해 매우 작은 단위로 처리
"""

import json
import os
import sys
import time
from typing import Dict, List, Any

sys.path.append('/Users/gimdonghyeon/Desktop/kb-ai-challenge')

from src.graph.llm_graph_transformer import LLMGraphTransformer
from src.graph.neo4j_manager import Neo4jManager

class SmallBatchGraphBuilder:
    """소규모 배치 그래프 구축기"""
    
    def __init__(self):
        self.transformer = LLMGraphTransformer()
        print(" Neo4j 연결 성공!")
        
    def load_data_by_type(self, data_type: str) -> List[Dict]:
        """데이터 타입별로 로드"""
        data_dir = "data"
        
        if data_type == "companies":
            company_files = [f for f in os.listdir(f"{data_dir}/raw") if f.startswith("company_data_") and f.endswith(".json")]
            if company_files:
                with open(f"{data_dir}/raw/{sorted(company_files)[-1]}", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("companies", [])
                    
        elif data_type == "kb_products":
            with open(f"{data_dir}/raw/kb_actual_products.json", 'r', encoding='utf-8') as f:
                return json.load(f)
                
        elif data_type == "macro_indicators":
            with open(f"{data_dir}/raw/ecos_latest_indicators.json", 'r', encoding='utf-8') as f:
                ecos_data = json.load(f)
                return list(ecos_data.values())
                
        elif data_type == "policies":
            policy_files = [f for f in os.listdir(f"{data_dir}/raw") if f.startswith("policy_data_") and f.endswith(".json")]
            if policy_files:
                with open(f"{data_dir}/raw/{sorted(policy_files)[-1]}", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("policies", [])
                    
        elif data_type == "news":
            all_news = []
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
                        all_news.extend(json.load(f))
            return all_news
            
        return []
    
    def process_small_batch(self, batch_data: Dict[str, Any], batch_name: str) -> Dict[str, Any]:
        """작은 배치 처리"""
        print(f"\n {batch_name} 처리 중...")
        
        try:
            # LLM 추출
            result = self.transformer.extract_graph_elements(batch_data)
            
            if result and 'nodes' in result:
                # 즉시 Neo4j에 저장
                if result['nodes']:
                    node_counts = self.transformer.create_nodes_in_neo4j(result['nodes'])
                    print(f"   노드 {len(result['nodes'])}개 생성: {node_counts}")
                    
                if result.get('relationships'):
                    rel_counts = self.transformer.create_relationships_in_neo4j(result['relationships'])
                    print(f"   관계 {len(result['relationships'])}개 생성: {rel_counts}")
                    
                return result
            else:
                print(f"  ️  결과 없음")
                return {"nodes": [], "relationships": []}
                
        except Exception as e:
            print(f"   오류: {e}")
            return {"nodes": [], "relationships": []}
    
    def build_incrementally(self):
        """점진적 그래프 구축"""
        print(" 소규모 배치 단위 그래프 구축 시작")
        
        total_nodes = 0
        total_relationships = 0
        
        # 1. 거시경제지표 (2개)
        macro_data = self.load_data_by_type("macro_indicators")
        if macro_data:
            result = self.process_small_batch(
                {"거시경제지표": macro_data}, 
                "거시경제지표 (2개)"
            )
            total_nodes += len(result.get('nodes', []))
            total_relationships += len(result.get('relationships', []))
            time.sleep(3)
        
        # 2. 기업 데이터 (4개씩 처리)
        companies = self.load_data_by_type("companies")
        for i in range(0, len(companies), 4):
            batch = companies[i:i+4]
            result = self.process_small_batch(
                {"기업정보": batch},
                f"기업 배치 {i//4 + 1} ({len(batch)}개)"
            )
            total_nodes += len(result.get('nodes', []))
            total_relationships += len(result.get('relationships', []))
            time.sleep(3)
        
        # 3. KB 상품 (5개씩 처리)
        kb_products = self.load_data_by_type("kb_products")
        for i in range(0, len(kb_products), 5):
            batch = kb_products[i:i+5]
            result = self.process_small_batch(
                {"KB금융상품": batch},
                f"KB상품 배치 {i//5 + 1} ({len(batch)}개)"
            )
            total_nodes += len(result.get('nodes', []))
            total_relationships += len(result.get('relationships', []))
            time.sleep(3)
        
        # 4. 정책 데이터 (10개씩 처리)
        policies = self.load_data_by_type("policies")
        for i in range(0, len(policies), 10):
            batch = policies[i:i+10]
            result = self.process_small_batch(
                {"정책데이터": batch},
                f"정책 배치 {i//10 + 1} ({len(batch)}개)"
            )
            total_nodes += len(result.get('nodes', []))
            total_relationships += len(result.get('relationships', []))
            time.sleep(3)
        
        # 5. 뉴스 데이터 (10개씩 처리)
        news = self.load_data_by_type("news")
        for i in range(0, len(news), 10):
            batch = news[i:i+10]
            result = self.process_small_batch(
                {"뉴스_데이터": batch},
                f"뉴스 배치 {i//10 + 1} ({len(batch)}개)"
            )
            total_nodes += len(result.get('nodes', []))
            total_relationships += len(result.get('relationships', []))
            time.sleep(3)
        
        # 최종 검증
        print("\n 최종 Neo4j 검증...")
        try:
            node_query = "MATCH (n) RETURN labels(n) as labels, count(n) as count"
            node_results = self.transformer.neo4j_manager.execute_query(node_query)
            
            rel_query = "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count"
            rel_results = self.transformer.neo4j_manager.execute_query(rel_query)
            
            print("\n Neo4j 최종 현황:")
            print("노드:")
            for result in node_results:
                print(f"  {result['labels']}: {result['count']}개")
            
            print("\n관계:")
            for result in rel_results:
                print(f"  {result['type']}: {result['count']}개")
                
        except Exception as e:
            print(f"검증 오류: {e}")
        
        print(f"\n 전체 구축 완료!")
        print(f"  - 총 노드: {total_nodes}개 추출")
        print(f"  - 총 관계: {total_relationships}개 추출")
        
        # 보고서 저장
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report = {
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "extracted_nodes": total_nodes,
            "extracted_relationships": total_relationships,
            "final_neo4j_state": {
                "nodes": {str(r['labels']): r['count'] for r in node_results},
                "relationships": {r['type']: r['count'] for r in rel_results}
            }
        }
        
        os.makedirs("results", exist_ok=True)
        with open(f"results/incremental_build_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report

if __name__ == "__main__":
    builder = SmallBatchGraphBuilder()
    report = builder.build_incrementally()
    
    # Neo4j 연결 종료
    if builder.transformer.neo4j_manager:
        builder.transformer.neo4j_manager.close()