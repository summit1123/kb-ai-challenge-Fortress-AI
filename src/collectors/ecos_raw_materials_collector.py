#!/usr/bin/env python3
"""
KB Fortress AI - ECOS Raw Materials Collector
ECOS API에서 실제 원자재 가격 데이터 수집 및 Neo4j 저장
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'graph'))
sys.path.append(os.path.dirname(__file__))

from ecos_collector import ECOSAPICollector
from neo4j_manager import Neo4jManager

class ECOSRawMaterialsCollector:
    """ECOS API 기반 실제 원자재 데이터 수집기"""
    
    def __init__(self):
        # ECOS API 수집기
        self.ecos_collector = ECOSAPICollector()
        
        # Neo4j 연결
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = 'ehdgusdl11!'
        self.neo4j_manager = Neo4jManager()
        
        # 원자재 지표 매핑 (업종별 영향도)
        self.raw_material_mapping = {
            "steel_price_index": {
                "category": "METALS",
                "volatility": "HIGH",
                "impact_industries": ["자동차부품", "기계제조", "금속가공", "조선"],
                "risk_multiplier": 1.2
            },
            "petrochemical_price_index": {
                "category": "CHEMICALS", 
                "volatility": "HIGH",
                "impact_industries": ["플라스틱제품", "화학제품", "자동차부품", "포장재"],
                "risk_multiplier": 1.1
            },
            "nonferrous_metal_price_index": {
                "category": "METALS",
                "volatility": "HIGH", 
                "impact_industries": ["전자부품", "전선케이블", "기계제조"],
                "risk_multiplier": 1.3
            },
            "oil_import_price": {
                "category": "ENERGY",
                "volatility": "EXTREME",
                "impact_industries": ["플라스틱제품", "화학제품", "운송업", "제조업"],
                "risk_multiplier": 1.5
            },
            "textile_material_price_index": {
                "category": "TEXTILES",
                "volatility": "MEDIUM",
                "impact_industries": ["섬유제조", "의류제조", "인테리어"],
                "risk_multiplier": 0.8
            },
            "agricultural_product_price_index": {
                "category": "AGRICULTURE",
                "volatility": "MEDIUM",
                "impact_industries": ["식품제조", "사료제조", "화학제품"],
                "risk_multiplier": 0.7
            }
        }
    
    def collect_and_store_real_raw_materials(self, days_back: int = 30) -> Dict[str, Any]:
        """ECOS API에서 실제 원자재 데이터 수집 및 Neo4j 저장"""
        print(" ECOS API에서 실제 원자재 데이터 수집 시작...")
        
        # 원자재 지표만 필터링
        raw_material_keys = list(self.raw_material_mapping.keys())
        
        # ECOS에서 데이터 수집
        all_data = {}
        for indicator_key in raw_material_keys:
            if indicator_key in self.ecos_collector.indicators:
                print(f" 수집 중: {self.ecos_collector.indicators[indicator_key]['name']}")
                
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
                
                data = self.ecos_collector.get_indicator_data(indicator_key, start_date, end_date)
                if data:
                    # 변화율 계산
                    data_with_rates = self.ecos_collector.calculate_change_rates(data)
                    all_data[indicator_key] = data_with_rates
        
        # Neo4j에 저장
        stored_count = 0
        relationship_count = 0
        
        for indicator_key, data_list in all_data.items():
            if data_list:
                # 최신 데이터로 MacroIndicator 노드 생성/업데이트
                latest_data = data_list[-1]
                mapping_info = self.raw_material_mapping[indicator_key]
                
                success = self._create_or_update_macro_indicator(latest_data, mapping_info)
                if success:
                    stored_count += 1
                    
                    # 기업과의 관계 생성
                    relationships = self._create_raw_material_relationships(latest_data, mapping_info)
                    relationship_count += relationships
        
        result = {
            "success": True,
            "collected_indicators": len(all_data),
            "stored_indicators": stored_count,
            "created_relationships": relationship_count,
            "data_summary": self._generate_summary(all_data),
            "collection_date": datetime.now().isoformat()
        }
        
        print(f" ECOS 원자재 데이터 수집 완료: {stored_count}개 지표, {relationship_count}개 관계")
        return result
    
    def _create_or_update_macro_indicator(self, latest_data: Dict[str, Any], 
                                        mapping_info: Dict[str, Any]) -> bool:
        """MacroIndicator 노드 생성 또는 업데이트"""
        
        # 기존 노드 확인
        check_query = """
        MATCH (m:MacroIndicator {indicatorName: $indicator_name})
        RETURN m.indicatorName as indicator
        """
        
        existing = self.neo4j_manager.execute_query(
            check_query, 
            {'indicator_name': latest_data['indicator_name']}
        )
        
        if existing:
            # 기존 노드 업데이트
            update_query = """
            MATCH (m:MacroIndicator {indicatorName: $indicator_name})
            SET m.value = $value,
                m.changeRate = $change_rate,
                m.lastUpdated = datetime(),
                m.volatility = $volatility,
                m.category = $category,
                m.riskMultiplier = $risk_multiplier,
                m.impactIndustries = $impact_industries,
                m.dataSource = 'ECOS_API',
                m.collectedDate = $collected_date
            RETURN m.indicatorName as indicator
            """
            
            result = self.neo4j_manager.execute_query(update_query, {
                'indicator_name': latest_data['indicator_name'],
                'value': latest_data['value'],
                'change_rate': latest_data.get('change_rate', 0.0),
                'volatility': mapping_info['volatility'],
                'category': mapping_info['category'],
                'risk_multiplier': mapping_info['risk_multiplier'],
                'impact_industries': mapping_info['impact_industries'],
                'collected_date': latest_data['collected_at']
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
                category: $category,
                volatility: $volatility,
                riskMultiplier: $risk_multiplier,
                impactIndustries: $impact_industries,
                dataSource: 'ECOS_API',
                statCode: $stat_code,
                lastUpdated: datetime(),
                createdAt: datetime(),
                collectedDate: $collected_date
            })
            RETURN m.indicatorName as indicator
            """
            
            result = self.neo4j_manager.execute_query(create_query, {
                'indicator_name': latest_data['indicator_name'],
                'value': latest_data['value'],
                'change_rate': latest_data.get('change_rate', 0.0),
                'unit': latest_data['unit'],
                'category': mapping_info['category'],
                'volatility': mapping_info['volatility'],
                'risk_multiplier': mapping_info['risk_multiplier'],
                'impact_industries': mapping_info['impact_industries'],
                'stat_code': latest_data['stat_code'],
                'collected_date': latest_data['collected_at']
            })
            
            return len(result) > 0
    
    def _create_raw_material_relationships(self, latest_data: Dict[str, Any], 
                                         mapping_info: Dict[str, Any]) -> int:
        """원자재와 기업 간 관계 생성"""
        
        total_relationships = 0
        
        for industry in mapping_info['impact_industries']:
            # 해당 업종의 모든 기업과 원자재 연결
            relationship_query = """
            MATCH (u:UserCompany), (m:MacroIndicator {indicatorName: $indicator_name})
            WHERE u.industryDescription CONTAINS $industry
            MERGE (u)-[r:IS_EXPOSED_TO]->(m)
            SET r.exposureLevel = CASE 
                    WHEN m.volatility = 'EXTREME' THEN 'HIGH'
                    WHEN m.volatility = 'HIGH' THEN 'HIGH'  
                    WHEN m.volatility = 'MEDIUM' THEN 'MEDIUM'
                    ELSE 'LOW'
                END,
                r.rationale = $rationale,
                r.riskType = 'RAW_MATERIALS',
                r.industryImpact = $industry,
                r.riskMultiplier = $risk_multiplier,
                r.lastUpdated = datetime()
            RETURN count(r) as created
            """
            
            try:
                result = self.neo4j_manager.execute_query(relationship_query, {
                    'indicator_name': latest_data['indicator_name'],
                    'industry': industry,
                    'rationale': f'{industry} 업종의 주요 원자재 의존도',
                    'risk_multiplier': mapping_info['risk_multiplier']
                })
                
                if result:
                    created = result[0].get('created', 0)
                    total_relationships += created
                    print(f" {industry} - {latest_data['indicator_name']}: {created}개 관계 생성")
                    
            except Exception as e:
                print(f" {industry} - {latest_data['indicator_name']} 관계 생성 실패: {e}")
        
        return total_relationships
    
    def _generate_summary(self, all_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """수집 결과 요약 생성"""
        summary = {
            "total_indicators": len(all_data),
            "indicators": {},
            "price_changes": {
                "rising": [],
                "falling": [],
                "stable": []
            },
            "high_volatility": []
        }
        
        for indicator_key, data_list in all_data.items():
            if data_list:
                latest = data_list[-1]
                change_rate = latest.get('change_rate', 0)
                
                indicator_summary = {
                    "name": latest['indicator_name'],
                    "current_value": latest['value'],
                    "change_rate": change_rate,
                    "unit": latest['unit'],
                    "volatility": self.raw_material_mapping[indicator_key]['volatility']
                }
                
                summary["indicators"][indicator_key] = indicator_summary
                
                # 가격 변동 분류
                if change_rate > 1.0:
                    summary["price_changes"]["rising"].append(indicator_summary)
                elif change_rate < -1.0:
                    summary["price_changes"]["falling"].append(indicator_summary)
                else:
                    summary["price_changes"]["stable"].append(indicator_summary)
                
                # 고변동성 지표
                if self.raw_material_mapping[indicator_key]['volatility'] in ['HIGH', 'EXTREME']:
                    summary["high_volatility"].append(indicator_summary)
        
        return summary
    
    def get_raw_materials_dashboard(self) -> Dict[str, Any]:
        """원자재 현황 대시보드 데이터"""
        dashboard_query = """
        MATCH (m:MacroIndicator)
        WHERE m.dataSource = 'ECOS_API'
        RETURN m.indicatorName as name,
               m.value as value,
               m.changeRate as change,
               m.volatility as volatility,
               m.category as category,
               m.unit as unit,
               m.riskMultiplier as risk_multiplier
        ORDER BY m.changeRate DESC
        """
        
        results = self.neo4j_manager.execute_query(dashboard_query)
        
        dashboard = {
            "total_materials": len(results),
            "materials_by_category": {},
            "price_alerts": [],
            "risk_materials": [],
            "materials": results
        }
        
        # 카테고리별 분류
        for material in results:
            category = material.get('category', 'OTHER')
            if category not in dashboard["materials_by_category"]:
                dashboard["materials_by_category"][category] = []
            dashboard["materials_by_category"][category].append(material)
            
            # 가격 급등/급락 알림
            change = material.get('change', 0)
            if abs(change) > 3.0:  # 3% 이상 변동
                dashboard["price_alerts"].append({
                    "material": material['name'],
                    "change": change,
                    "type": "급등" if change > 0 else "급락"
                })
            
            # 고위험 원자재
            risk_multiplier = material.get('risk_multiplier', 1.0)
            if risk_multiplier > 1.2:
                dashboard["risk_materials"].append(material)
        
        return dashboard
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """ECOS 원자재 데이터 수집 메인 실행"""
    print("=== KB Fortress AI ECOS 원자재 데이터 수집기 ===")
    
    collector = ECOSRawMaterialsCollector()
    
    try:
        # 1. 실제 원자재 데이터 수집 및 저장
        result = collector.collect_and_store_real_raw_materials(days_back=30)
        
        if result["success"]:
            print(f"\n{'='*60}")
            print(" ECOS 원자재 데이터 수집 완료")
            print(f"{'='*60}")
            print(f"수집된 지표: {result['collected_indicators']}개")
            print(f"저장된 지표: {result['stored_indicators']}개")
            print(f"생성된 관계: {result['created_relationships']}개")
            
            # 가격 변동 현황
            summary = result['data_summary']
            print(f"\n 가격 변동 현황:")
            print(f"  상승: {len(summary['price_changes']['rising'])}개")
            print(f"  하락: {len(summary['price_changes']['falling'])}개")
            print(f"  안정: {len(summary['price_changes']['stable'])}개")
            print(f"  고변동성: {len(summary['high_volatility'])}개")
            
            # 주요 변동 원자재
            print(f"\n 주요 원자재 현황:")
            for key, info in summary['indicators'].items():
                change_emoji = "" if info['change_rate'] > 0 else "" if info['change_rate'] < 0 else "️"
                print(f"{change_emoji} {info['name']}: {info['current_value']} {info['unit']} ({info['change_rate']:+.2f}%)")
            
            # 2. 대시보드 데이터 생성
            dashboard = collector.get_raw_materials_dashboard()
            
            print(f"\n 가격 급변동 알림: {len(dashboard['price_alerts'])}개")
            for alert in dashboard['price_alerts']:
                print(f"  {alert['type']}: {alert['material']} ({alert['change']:+.1f}%)")
            
            print(f"\n️ 고위험 원자재: {len(dashboard['risk_materials'])}개")
            for risk_material in dashboard['risk_materials']:
                print(f"  {risk_material['name']} (위험배수: {risk_material['risk_multiplier']:.1f})")
            
        else:
            print(" 원자재 데이터 수집 실패")
        
    except Exception as e:
        print(f" ECOS 원자재 데이터 수집 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        collector.cleanup()

if __name__ == "__main__":
    main()