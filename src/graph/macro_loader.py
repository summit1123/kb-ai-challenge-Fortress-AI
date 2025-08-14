import json
import os
from typing import List, Dict, Any
from neo4j_manager import Neo4jManager
from schema import MacroIndicator, NodeType, Relationship, RelationshipType
from datetime import datetime

class MacroIndicatorLoader:
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
    
    def load_ecos_data(self, json_path: str = "data/raw/ecos_latest_indicators.json") -> List[MacroIndicator]:
        """ECOS 최신 지표 데이터를 MacroIndicator 객체로 변환"""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            ecos_data = json.load(f)
        
        macro_indicators = []
        for indicator_key, data in ecos_data.items():
            if data.get("value") is not None:
                # 날짜 파싱
                date_str = data.get("date", "")
                try:
                    if len(date_str) == 8:  # YYYYMMDD
                        indicator_date = datetime.strptime(date_str, "%Y%m%d")
                    else:
                        indicator_date = datetime.now()
                except:
                    indicator_date = datetime.now()
                
                macro_indicator = MacroIndicator(
                    node_id=f"indicator_{indicator_key}",
                    node_type=NodeType.MACRO_INDICATOR.value,
                    created_at=datetime.now(),
                    indicator_name=data.get("indicator_name", ""),
                    value=float(data.get("value", 0)),
                    change_rate=data.get("change_rate"),
                    date=indicator_date,
                    unit=data.get("unit", ""),
                    category="거시경제지표"
                )
                macro_indicators.append(macro_indicator)
        
        print(f"ECOS 데이터에서 {len(macro_indicators)}개 거시경제지표 변환 완료")
        return macro_indicators
    
    def create_macro_indicator_nodes(self, indicators: List[MacroIndicator]) -> bool:
        """거시경제지표 노드를 Neo4j에 생성"""
        try:
            create_query = """
            MERGE (m:MacroIndicator {nodeId: $nodeId})
            SET m.nodeType = $nodeType,
                m.createdAt = $createdAt,
                m.updatedAt = $updatedAt,
                m.indicatorName = $indicatorName,
                m.value = $value,
                m.changeRate = $changeRate,
                m.date = $date,
                m.unit = $unit,
                m.category = $category
            """
            
            success_count = 0
            for indicator in indicators:
                try:
                    indicator_dict = indicator.to_dict()
                    self.neo4j_manager.execute_query(create_query, indicator_dict)
                    success_count += 1
                except Exception as e:
                    print(f"지표 생성 실패: {indicator.indicator_name} - {e}")
            
            print(f" {success_count}/{len(indicators)}개 거시경제지표 노드 생성 완료")
            return success_count == len(indicators)
            
        except Exception as e:
            print(f" 거시경제지표 노드 생성 오류: {e}")
            return False
    
    def create_exposure_relationships(self):
        """기업과 거시경제지표 간 노출 관계 생성"""
        # 대한정밀이 노출되는 주요 지표들
        exposure_mappings = [
            ("indicator_base_rate", 0.9, "변동금리 대출 10억원으로 금리 변동에 직접적 영향"),
            ("indicator_usd_krw", 0.7, "자동차부품 수출업체로 환율 변동에 매출 영향"),
        ]
        
        create_relationship_query = """
        MATCH (c:Company {nodeId: "company_daehan_precision"})
        MATCH (m:MacroIndicator {nodeId: $indicatorId})
        MERGE (c)-[r:IS_EXPOSED_TO]->(m)
        SET r.exposureLevel = $exposureLevel,
            r.rationale = $rationale,
            r.createdAt = $createdAt
        """
        
        success_count = 0
        for indicator_id, exposure_level, rationale in exposure_mappings:
            try:
                self.neo4j_manager.execute_query(create_relationship_query, {
                    "indicatorId": indicator_id,
                    "exposureLevel": exposure_level,
                    "rationale": rationale,
                    "createdAt": datetime.now().isoformat()
                })
                success_count += 1
                print(f" 노출 관계 생성: 대한정밀 → {indicator_id}")
            except Exception as e:
                print(f" 노출 관계 생성 실패: {indicator_id} - {e}")
        
        print(f"총 {success_count}개 노출 관계 생성 완료")
        return success_count
    
    def simulate_impact_scenario(self):
        """금리 인상 시나리오 시뮬레이션"""
        # 기준금리 0.5%p 인상 가정
        scenario_query = """
        MATCH (c:Company {nodeId: "company_daehan_precision"})
        MATCH (m:MacroIndicator {nodeId: "indicator_base_rate"})
        CREATE (scenario:NewsArticle {
            nodeId: "news_rate_hike_scenario",
            nodeType: "NewsArticle",
            createdAt: $createdAt,
            title: "한국은행 기준금리 0.5%p 인상",
            publisher: "경제신문",
            publishDate: $publishDate,
            articleText: "한국은행이 물가 안정을 위해 기준금리를 0.5%포인트 인상했다. 이로 인해 변동금리 대출을 보유한 중소기업들의 이자 부담이 증가할 전망이다.",
            summary: "기준금리 0.5%p 인상으로 대출 이자 부담 증가",
            category: "금융정책",
            sentiment: "negative"
        })
        CREATE (scenario)-[impact:HAS_IMPACT_ON {
            impactScore: -0.8,
            rationale: "변동금리 대출 10억원 보유로 월 이자부담 320만원 증가 예상",
            sentiment: "negative",
            estimatedCost: 38400000,
            createdAt: $createdAt
        }]->(c)
        CREATE (scenario)-[triggers:HAS_IMPACT_ON {
            impactScore: 1.0,
            rationale: "기준금리 인상 발표",
            sentiment: "neutral",
            createdAt: $createdAt
        }]->(m)
        """
        
        try:
            self.neo4j_manager.execute_query(scenario_query, {
                "createdAt": datetime.now().isoformat(),
                "publishDate": datetime.now().isoformat()
            })
            print(" 금리 인상 시나리오 생성 완료")
            return True
        except Exception as e:
            print(f" 시나리오 생성 실패: {e}")
            return False
    
    def verify_graph_relationships(self):
        """그래프 관계 검증"""
        verification_queries = {
            "거시경제지표 수": "MATCH (m:MacroIndicator) RETURN count(m) as count",
            "노출 관계 수": "MATCH ()-[r:IS_EXPOSED_TO]->() RETURN count(r) as count",
            "영향 관계 수": "MATCH ()-[r:HAS_IMPACT_ON]->() RETURN count(r) as count",
            "뉴스 기사 수": "MATCH (n:NewsArticle) RETURN count(n) as count"
        }
        
        print("\n=== 그래프 관계 검증 ===")
        for description, query in verification_queries.items():
            try:
                result = self.neo4j_manager.execute_query(query)
                count = result[0]["count"] if result else 0
                print(f"{description}: {count}개")
            except Exception as e:
                print(f"{description} 조회 실패: {e}")
        
        # 대한정밀 관련 관계 조회
        company_relations_query = """
        MATCH (c:Company {nodeId: "company_daehan_precision"})-[r]->(target)
        RETURN type(r) as relationship_type, 
               labels(target)[0] as target_type,
               target.nodeId as target_id,
               r.exposureLevel as exposure_level,
               r.eligibilityScore as eligibility_score,
               r.impactScore as impact_score
        """
        
        try:
            results = self.neo4j_manager.execute_query(company_relations_query)
            print("\n대한정밀 관련 관계:")
            for result in results:
                rel_type = result['relationship_type']
                target_type = result['target_type']
                target_id = result['target_id']
                
                if result.get('exposure_level'):
                    print(f"  {rel_type} → {target_type} ({target_id}): 노출도 {result['exposure_level']}")
                elif result.get('eligibility_score'):
                    print(f"  {rel_type} → {target_type} ({target_id}): 자격점수 {result['eligibility_score']}")
                elif result.get('impact_score'):
                    print(f"  {rel_type} → {target_type} ({target_id}): 영향점수 {result['impact_score']}")
                else:
                    print(f"  {rel_type} → {target_type} ({target_id})")
        except Exception as e:
            print(f"관계 조회 실패: {e}")
    
    def run_full_macro_loading_process(self):
        """전체 거시경제지표 로딩 프로세스"""
        print("=== 거시경제지표 데이터 로딩 시작 ===")
        
        try:
            # 1. ECOS 데이터 로드
            indicators = self.load_ecos_data()
            
            # 2. 거시경제지표 노드 생성
            if self.create_macro_indicator_nodes(indicators):
                print(" 거시경제지표 노드 생성 성공")
            else:
                print(" 거시경제지표 노드 생성 실패")
                return False
            
            # 3. 노출 관계 생성
            exposure_count = self.create_exposure_relationships()
            if exposure_count > 0:
                print(" 노출 관계 생성 성공")
            
            # 4. 시나리오 시뮬레이션
            if self.simulate_impact_scenario():
                print(" 시나리오 시뮬레이션 성공")
            
            # 5. 관계 검증
            self.verify_graph_relationships()
            
            print("\n=== 거시경제지표 데이터 로딩 완료 ===")
            return True
            
        except Exception as e:
            print(f" 거시경제지표 로딩 프로세스 오류: {e}")
            return False
        finally:
            self.neo4j_manager.close()

def main():
    loader = MacroIndicatorLoader()
    loader.run_full_macro_loading_process()

if __name__ == "__main__":
    main()