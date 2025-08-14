#!/usr/bin/env python3
"""
KB Fortress AI - Raw Materials Price Collector
원자재 가격 데이터 수집기 (LME, 국내 원자재 가격)
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
from neo4j_manager import Neo4jManager

class RawMaterialsCollector:
    """원자재 가격 수집기"""
    
    def __init__(self):
        # Neo4j 연결
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'
        self.neo4j_manager = Neo4jManager()
        
        # 원자재 가격 매핑 (실제로는 API에서 가져와야 함)
        self.raw_materials_data = self._get_sample_raw_materials_data()
        
    def _get_sample_raw_materials_data(self) -> List[Dict[str, Any]]:
        """샘플 원자재 가격 데이터 (실제 서비스에서는 API 연동)"""
        return [
            {
                "material_name": "철강가격지수",
                "indicator_name": "철강가격지수",
                "current_value": 156.8,
                "change_rate": 2.3,
                "unit": "지수",
                "description": "국내 철강 종합가격지수",
                "impact_industries": ["자동차부품", "기계제조", "금속가공"],
                "volatility": "HIGH"
            },
            {
                "material_name": "구리가격",
                "indicator_name": "구리선물가격", 
                "current_value": 8250.0,
                "change_rate": -1.2,
                "unit": "USD/톤",
                "description": "LME 구리 선물 가격",
                "impact_industries": ["전자부품", "전선케이블", "기계제조"],
                "volatility": "HIGH"
            },
            {
                "material_name": "알루미늄가격",
                "indicator_name": "알루미늄선물가격",
                "current_value": 2180.0,
                "change_rate": 0.8,
                "unit": "USD/톤", 
                "description": "LME 알루미늄 선물 가격",
                "impact_industries": ["자동차부품", "항공우주", "포장재"],
                "volatility": "MEDIUM"
            },
            {
                "material_name": "플라스틱원료",
                "indicator_name": "석유화학가격지수",
                "current_value": 142.5,
                "change_rate": 3.1,
                "unit": "지수",
                "description": "국내 석유화학 제품 종합가격지수",
                "impact_industries": ["플라스틱제품", "자동차부품", "포장재"],
                "volatility": "HIGH"
            },
            {
                "material_name": "화학소재",
                "indicator_name": "화학소재가격지수",
                "current_value": 128.9,
                "change_rate": 1.7,
                "unit": "지수",
                "description": "정밀화학 및 특수소재 가격지수",
                "impact_industries": ["화학제품", "전자부품", "섬유제조"],
                "volatility": "MEDIUM"
            },
            {
                "material_name": "반도체소재",
                "indicator_name": "반도체소재가격지수",
                "current_value": 189.3,
                "change_rate": 4.2,
                "unit": "지수",
                "description": "반도체 제조용 핵심 소재 가격지수",
                "impact_industries": ["반도체", "전자부품", "디스플레이"],
                "volatility": "EXTREME"
            },
            {
                "material_name": "섬유원료",
                "indicator_name": "섬유원료가격지수",
                "current_value": 98.7,
                "change_rate": -0.5,
                "unit": "지수",
                "description": "면화, 폴리에스터 등 섬유 원료 가격지수",
                "impact_industries": ["섬유제조", "의류제조", "인테리어"],
                "volatility": "LOW"
            }
        ]
    
    def collect_and_store_raw_materials(self):
        """원자재 데이터 수집 및 Neo4j 저장"""
        print(" 원자재 가격 데이터 수집 및 저장 시작...")
        
        created_count = 0
        
        for material in self.raw_materials_data:
            try:
                # MacroIndicator 노드로 저장
                result = self._create_macro_indicator_node(material)
                if result:
                    created_count += 1
                    print(f" {material['indicator_name']} 저장 완료")
                    
            except Exception as e:
                print(f" {material['indicator_name']} 저장 실패: {e}")
        
        print(f" 원자재 데이터 저장 완료: {created_count}개")
        return created_count
    
    def _create_macro_indicator_node(self, material_data: Dict[str, Any]) -> bool:
        """MacroIndicator 노드 생성"""
        
        # 기존 노드 확인
        check_query = """
        MATCH (m:MacroIndicator {indicatorName: $indicator_name})
        RETURN m.indicatorName as indicator
        """
        
        existing = self.neo4j_manager.execute_query(
            check_query, 
            {'indicator_name': material_data['indicator_name']}
        )
        
        if existing:
            # 기존 노드가 있으면 업데이트
            update_query = """
            MATCH (m:MacroIndicator {indicatorName: $indicator_name})
            SET m.value = $value,
                m.changeRate = $change_rate,
                m.lastUpdated = datetime(),
                m.volatility = $volatility,
                m.description = $description
            RETURN m.indicatorName as indicator
            """
            
            result = self.neo4j_manager.execute_query(update_query, {
                'indicator_name': material_data['indicator_name'],
                'value': material_data['current_value'],
                'change_rate': material_data['change_rate'],
                'volatility': material_data['volatility'],
                'description': material_data['description']
            })
            
            return len(result) > 0
        else:
            # 새 노드 생성
            create_query = """
            CREATE (m:MacroIndicator {
                indicatorName: $indicator_name,
                value: $value,
                changeRate: $change_rate,
                unit: $unit,
                description: $description,
                category: 'RAW_MATERIALS',
                volatility: $volatility,
                impactIndustries: $impact_industries,
                lastUpdated: datetime(),
                createdAt: datetime()
            })
            RETURN m.indicatorName as indicator
            """
            
            result = self.neo4j_manager.execute_query(create_query, {
                'indicator_name': material_data['indicator_name'],
                'value': material_data['current_value'],
                'change_rate': material_data['change_rate'],
                'unit': material_data['unit'],
                'description': material_data['description'],
                'volatility': material_data['volatility'],
                'impact_industries': material_data['impact_industries']
            })
            
            return len(result) > 0
    
    def create_raw_material_relationships(self):
        """원자재와 기업 간 관계 생성"""
        print(" 원자재-기업 관계 생성 중...")
        
        # 업종별 원자재 의존도 매핑
        industry_material_mapping = {
            "자동차부품": ["철강가격지수", "알루미늄선물가격", "석유화학가격지수"],
            "전자부품": ["구리선물가격", "반도체소재가격지수", "화학소재가격지수"],
            "화학제품": ["화학소재가격지수", "석유화학가격지수"],
            "섬유제조": ["섬유원료가격지수", "화학소재가격지수"],
            "기계제조": ["철강가격지수", "구리선물가격", "알루미늄선물가격"],
            "금속가공": ["철강가격지수", "구리선물가격", "알루미늄선물가격"],
            "플라스틱제품": ["석유화학가격지수"],
            "반도체": ["반도체소재가격지수", "화학소재가격지수"]
        }
        
        total_relationships = 0
        
        for industry, materials in industry_material_mapping.items():
            for material in materials:
                # 해당 업종의 모든 기업과 원자재 연결
                relationship_query = """
                MATCH (u:UserCompany), (m:MacroIndicator {indicatorName: $material})
                WHERE u.industryDescription CONTAINS $industry
                CREATE (u)-[:IS_EXPOSED_TO {
                    exposureLevel: CASE 
                        WHEN m.volatility = 'EXTREME' THEN 'HIGH'
                        WHEN m.volatility = 'HIGH' THEN 'HIGH'  
                        WHEN m.volatility = 'MEDIUM' THEN 'MEDIUM'
                        ELSE 'LOW'
                    END,
                    rationale: '업종별 주요 원자재 의존',
                    riskType: 'RAW_MATERIALS',
                    createdAt: datetime()
                }]->(m)
                RETURN count(*) as created
                """
                
                try:
                    result = self.neo4j_manager.execute_query(relationship_query, {
                        'industry': industry,
                        'material': material
                    })
                    
                    if result:
                        created = result[0].get('created', 0)
                        total_relationships += created
                        print(f" {industry} - {material}: {created}개 관계 생성")
                        
                except Exception as e:
                    print(f" {industry} - {material} 관계 생성 실패: {e}")
        
        print(f" 원자재 관계 생성 완료: 총 {total_relationships}개")
        return total_relationships
    
    def get_raw_materials_summary(self) -> Dict[str, Any]:
        """원자재 현황 요약"""
        summary_query = """
        MATCH (m:MacroIndicator)
        WHERE m.category = 'RAW_MATERIALS'
        RETURN m.indicatorName as material,
               m.value as value,
               m.changeRate as change,
               m.volatility as volatility,
               m.unit as unit
        ORDER BY m.changeRate DESC
        """
        
        results = self.neo4j_manager.execute_query(summary_query)
        
        summary = {
            "total_materials": len(results),
            "rising_materials": [r for r in results if r['change'] > 0],
            "falling_materials": [r for r in results if r['change'] < 0],
            "high_volatility": [r for r in results if r['volatility'] == 'HIGH'],
            "materials": results
        }
        
        return summary
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """원자재 데이터 수집 메인 실행"""
    print("=== KB Fortress AI 원자재 데이터 수집기 ===")
    
    collector = RawMaterialsCollector()
    
    try:
        # 1. 원자재 데이터 수집 및 저장
        created_count = collector.collect_and_store_raw_materials()
        
        # 2. 기업-원자재 관계 생성
        relationship_count = collector.create_raw_material_relationships()
        
        # 3. 현황 요약
        summary = collector.get_raw_materials_summary()
        
        print(f"\n{'='*50}")
        print(" 원자재 데이터 수집 완료")
        print(f"{'='*50}")
        print(f"생성된 원자재: {created_count}개")
        print(f"생성된 관계: {relationship_count}개")
        print(f"상승 원자재: {len(summary['rising_materials'])}개")
        print(f"하락 원자재: {len(summary['falling_materials'])}개")
        print(f"고변동성: {len(summary['high_volatility'])}개")
        print(f"{'='*50}")
        
        # 상위 변동 원자재 출력
        print("\n 주요 변동 원자재:")
        for material in summary['materials'][:5]:
            change_emoji = "" if material['change'] > 0 else ""
            print(f"{change_emoji} {material['material']}: {material['change']:+.1f}% ({material['value']}{material['unit']})")
        
    except Exception as e:
        print(f" 원자재 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        collector.cleanup()

if __name__ == "__main__":
    main()