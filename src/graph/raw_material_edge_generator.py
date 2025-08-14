#!/usr/bin/env python3
"""
KB Fortress AI - Raw Material Edge Generator
원자재 기반 복합 엣지 생성 시스템
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.dirname(__file__))

from src.graph.neo4j_manager import Neo4jManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

class RawMaterialEdgeGenerator:
    """원자재 기반 엣지 생성기"""
    
    def __init__(self):
        # Neo4j 연결
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = 'ehdgusdl11!'
        self.neo4j_manager = Neo4jManager()
        
        # LLM 설정
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=google_api_key
            )
        else:
            self.llm = None
            print("️ LLM 없이 진행 (기본 규칙 기반)")
    
    def generate_all_raw_material_edges(self) -> Dict[str, Any]:
        """모든 원자재 관련 엣지 생성"""
        print(" 원자재 기반 엣지 생성 시작...")
        
        results = {
            "company_raw_material_edges": 0,
            "news_raw_material_edges": 0,
            "raw_material_correlation_edges": 0,
            "supply_chain_edges": 0,
            "total_edges": 0
        }
        
        # 1. 기업 ↔ 원자재 의존도 엣지
        results["company_raw_material_edges"] = self._create_company_raw_material_edges()
        
        # 2. 뉴스 → 원자재 영향 엣지  
        results["news_raw_material_edges"] = self._create_news_raw_material_edges()
        
        # 3. 원자재 간 상관관계 엣지
        results["raw_material_correlation_edges"] = self._create_raw_material_correlation_edges()
        
        # 4. 공급망 연쇄 엣지
        results["supply_chain_edges"] = self._create_supply_chain_edges()
        
        results["total_edges"] = sum([
            results["company_raw_material_edges"],
            results["news_raw_material_edges"], 
            results["raw_material_correlation_edges"],
            results["supply_chain_edges"]
        ])
        
        print(f" 원자재 엣지 생성 완료: 총 {results['total_edges']}개")
        return results
    
    def _create_company_raw_material_edges(self) -> int:
        """기업 ↔ 원자재 의존도 엣지 생성"""
        print(" 기업-원자재 의존도 엣지 생성 중...")
        
        # 업종별 원자재 의존도 매핑 (정교화)
        industry_dependency_map = {
            "자동차부품": {
                "철강가격지수": {"dependency": "HIGH", "cost_ratio": 0.35, "risk_multiplier": 1.4},
                "알루미늄선물가격": {"dependency": "MEDIUM", "cost_ratio": 0.15, "risk_multiplier": 1.2},
                "석유화학가격지수": {"dependency": "MEDIUM", "cost_ratio": 0.20, "risk_multiplier": 1.1}
            },
            "전자부품": {
                "비철금속가격지수": {"dependency": "HIGH", "cost_ratio": 0.30, "risk_multiplier": 1.5},
                "반도체소재가격지수": {"dependency": "EXTREME", "cost_ratio": 0.45, "risk_multiplier": 2.0},
                "희토류가격지수": {"dependency": "HIGH", "cost_ratio": 0.25, "risk_multiplier": 1.6}
            },
            "화학제품": {
                "석유화학가격지수": {"dependency": "EXTREME", "cost_ratio": 0.50, "risk_multiplier": 1.8},
                "원유도입단가": {"dependency": "HIGH", "cost_ratio": 0.40, "risk_multiplier": 1.6}
            },
            "섬유제조": {
                "섬유원료가격지수": {"dependency": "HIGH", "cost_ratio": 0.40, "risk_multiplier": 1.3},
                "석유화학가격지수": {"dependency": "MEDIUM", "cost_ratio": 0.20, "risk_multiplier": 1.1}
            },
            "기계제조": {
                "철강가격지수": {"dependency": "HIGH", "cost_ratio": 0.30, "risk_multiplier": 1.3},
                "비철금속가격지수": {"dependency": "MEDIUM", "cost_ratio": 0.20, "risk_multiplier": 1.2}
            }
        }
        
        total_edges = 0
        
        for industry, materials in industry_dependency_map.items():
            for material_name, dependency_info in materials.items():
                
                edge_query = """
                MATCH (company:UserCompany), (material:MacroIndicator {indicatorName: $material_name})
                WHERE company.industryDescription CONTAINS $industry
                MERGE (company)-[r:IS_DEPENDENT_ON]->(material)
                SET r.dependencyLevel = $dependency_level,
                    r.costRatio = $cost_ratio,
                    r.riskMultiplier = $risk_multiplier,
                    r.industryType = $industry,
                    r.edgeType = 'RAW_MATERIAL_DEPENDENCY',
                    r.lastUpdated = datetime(),
                    r.confidence = 0.9
                RETURN count(r) as created
                """
                
                try:
                    result = self.neo4j_manager.execute_query(edge_query, {
                        "material_name": material_name,
                        "industry": industry,
                        "dependency_level": dependency_info["dependency"],
                        "cost_ratio": dependency_info["cost_ratio"],
                        "risk_multiplier": dependency_info["risk_multiplier"]
                    })
                    
                    if result:
                        created = result[0].get('created', 0)
                        total_edges += created
                        print(f"   {industry} → {material_name}: {created}개")
                        
                except Exception as e:
                    print(f"   {industry} → {material_name} 실패: {e}")
        
        return total_edges
    
    def _create_news_raw_material_edges(self) -> int:
        """뉴스 → 원자재 영향 엣지 생성"""
        print(" 뉴스-원자재 영향 엣지 생성 중...")
        
        # 뉴스와 원자재 쌍 조회
        query = """
        MATCH (news:NewsArticle), (material:MacroIndicator)
        WHERE material.category IN ['METALS', 'CHEMICALS', 'ENERGY', 'AGRICULTURE']
        RETURN news.title as news_title,
               news.content as news_content,
               material.indicatorName as material_name,
               material.category as material_category
        LIMIT 50
        """
        
        pairs = self.neo4j_manager.execute_query(query)
        total_edges = 0
        
        for pair in pairs:
            # LLM으로 영향 관계 분석
            impact_analysis = self._analyze_news_material_impact(
                pair['news_title'], 
                pair['news_content'],
                pair['material_name'],
                pair['material_category']
            )
            
            if impact_analysis and impact_analysis['has_impact']:
                edge_query = """
                MATCH (news:NewsArticle {title: $news_title}), 
                      (material:MacroIndicator {indicatorName: $material_name})
                MERGE (news)-[r:AFFECTS_PRICE]->(material)
                SET r.impactDirection = $impact_direction,
                    r.impactMagnitude = $impact_magnitude,
                    r.timeHorizon = $time_horizon,
                    r.confidence = $confidence,
                    r.reasoning = $reasoning,
                    r.edgeType = 'NEWS_MATERIAL_IMPACT',
                    r.lastUpdated = datetime()
                RETURN count(r) as created
                """
                
                try:
                    result = self.neo4j_manager.execute_query(edge_query, {
                        "news_title": pair['news_title'],
                        "material_name": pair['material_name'],
                        "impact_direction": impact_analysis['direction'],
                        "impact_magnitude": impact_analysis['magnitude'],
                        "time_horizon": impact_analysis['time_horizon'],
                        "confidence": impact_analysis['confidence'],
                        "reasoning": impact_analysis['reasoning']
                    })
                    
                    if result:
                        created = result[0].get('created', 0)
                        total_edges += created
                        print(f"   {pair['news_title'][:30]}... → {pair['material_name']}")
                        
                except Exception as e:
                    print(f"   뉴스-원자재 엣지 생성 실패: {e}")
        
        return total_edges
    
    def _analyze_news_material_impact(self, news_title: str, news_content: str, 
                                    material_name: str, material_category: str) -> Optional[Dict[str, Any]]:
        """LLM으로 뉴스-원자재 영향 분석"""
        if not self.llm:
            return None
        
        prompt = ChatPromptTemplate.from_template("""
        당신은 원자재 시장 전문가입니다. 다음 뉴스가 특정 원자재 가격에 미치는 영향을 분석하세요.

        === 뉴스 정보 ===
        제목: {news_title}
        내용: {news_content}

        === 원자재 정보 ===
        원자재명: {material_name}
        카테고리: {material_category}

        다음 기준으로 분석하세요:
        1. 이 뉴스가 해당 원자재 가격에 영향을 미치는가? (YES/NO)
        2. 영향 방향: POSITIVE(가격상승) or NEGATIVE(가격하락)
        3. 영향 크기: 0.0-1.0 (0: 무영향, 1.0: 극대영향)
        4. 시간 범위: SHORT_TERM(1개월), MEDIUM_TERM(3개월), LONG_TERM(6개월+)
        5. 신뢰도: 0.0-1.0
        6. 근거: 간단한 설명

        JSON 형식으로 답변하세요:
        {{
            "has_impact": true/false,
            "direction": "POSITIVE/NEGATIVE",
            "magnitude": 0.0-1.0,
            "time_horizon": "SHORT_TERM/MEDIUM_TERM/LONG_TERM",
            "confidence": 0.0-1.0,
            "reasoning": "근거 설명"
        }}
        """)
        
        try:
            response = self.llm.invoke([
                HumanMessage(content=prompt.format(
                    news_title=news_title,
                    news_content=news_content or "내용 없음",
                    material_name=material_name,
                    material_category=material_category
                ))
            ])
            
            import json
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            print(f"LLM 분석 실패: {e}")
            return None
    
    def _create_raw_material_correlation_edges(self) -> int:
        """원자재 간 상관관계 엣지 생성"""
        print(" 원자재 상관관계 엣지 생성 중...")
        
        # 원자재 간 상관관계 정의
        correlations = [
            {
                "material1": "철강가격지수", 
                "material2": "비철금속가격지수",
                "correlation": 0.7,
                "type": "INDUSTRIAL_METALS"
            },
            {
                "material1": "원유도입단가",
                "material2": "석유화학가격지수", 
                "correlation": 0.9,
                "type": "OIL_DERIVATIVES"
            },
            {
                "material1": "석유화학가격지수",
                "material2": "플라스틱원료지수",
                "correlation": 0.8,
                "type": "CHEMICAL_CHAIN"
            }
        ]
        
        total_edges = 0
        
        for corr in correlations:
            edge_query = """
            MATCH (m1:MacroIndicator {indicatorName: $material1}),
                  (m2:MacroIndicator {indicatorName: $material2})
            MERGE (m1)-[r:CORRELATED_WITH]->(m2)
            SET r.correlationCoeff = $correlation,
                r.correlationType = $correlation_type,
                r.edgeType = 'MATERIAL_CORRELATION',
                r.lastUpdated = datetime()
            MERGE (m2)-[r2:CORRELATED_WITH]->(m1)
            SET r2.correlationCoeff = $correlation,
                r2.correlationType = $correlation_type,
                r2.edgeType = 'MATERIAL_CORRELATION',
                r2.lastUpdated = datetime()
            RETURN count(r) + count(r2) as created
            """
            
            try:
                result = self.neo4j_manager.execute_query(edge_query, {
                    "material1": corr["material1"],
                    "material2": corr["material2"],
                    "correlation": corr["correlation"],
                    "correlation_type": corr["type"]
                })
                
                if result:
                    created = result[0].get('created', 0)
                    total_edges += created
                    print(f"   {corr['material1']} ↔ {corr['material2']}: {created}개")
                    
            except Exception as e:
                print(f"   상관관계 엣지 실패: {e}")
        
        return total_edges
    
    def _create_supply_chain_edges(self) -> int:
        """공급망 연쇄 엣지 생성"""
        print("️ 공급망 연쇄 엣지 생성 중...")
        
        # 환율 → 수입원자재 → 기업 체인
        chain_query = """
        MATCH (exchange:MacroIndicator {indicatorName: '원/달러 환율'}),
              (material:MacroIndicator),
              (company:UserCompany)
        WHERE material.category IN ['METALS', 'ENERGY', 'CHEMICALS']
          AND EXISTS((company)-[:IS_DEPENDENT_ON]->(material))
        MERGE (exchange)-[r1:AFFECTS_IMPORT_COST]->(material)
        SET r1.impactType = 'CURRENCY_EFFECT',
            r1.multiplier = 1.0,
            r1.edgeType = 'SUPPLY_CHAIN',
            r1.lastUpdated = datetime()
        MERGE (material)-[r2:INCREASES_PRODUCTION_COST]->(company)
        SET r2.impactType = 'RAW_MATERIAL_COST',
            r2.edgeType = 'SUPPLY_CHAIN',
            r2.lastUpdated = datetime()
        RETURN count(r1) + count(r2) as created
        """
        
        try:
            result = self.neo4j_manager.execute_query(chain_query)
            created = result[0].get('created', 0) if result else 0
            print(f"   공급망 연쇄 엣지: {created}개")
            return created
            
        except Exception as e:
            print(f"   공급망 엣지 실패: {e}")
            return 0
    
    def get_raw_material_graph_summary(self) -> Dict[str, Any]:
        """원자재 그래프 구조 요약"""
        
        summary_query = """
        // 전체 엣지 타입별 카운트
        MATCH ()-[r]->()
        WHERE r.edgeType CONTAINS 'RAW_MATERIAL' OR r.edgeType CONTAINS 'MATERIAL'
        RETURN r.edgeType as edge_type, count(r) as count
        ORDER BY count DESC
        """
        
        edge_counts = self.neo4j_manager.execute_query(summary_query)
        
        # 멀티홉 경로 샘플
        multihop_query = """
        MATCH path = (news:NewsArticle)-[r1:AFFECTS_PRICE]->(material:MacroIndicator)
                     <-[r2:IS_DEPENDENT_ON]-(company:UserCompany)
        RETURN news.title as news,
               material.indicatorName as material,
               company.companyName as company,
               r1.impactDirection as impact,
               r2.dependencyLevel as dependency
        LIMIT 5
        """
        
        sample_paths = self.neo4j_manager.execute_query(multihop_query)
        
        return {
            "edge_type_counts": edge_counts,
            "sample_multihop_paths": sample_paths,
            "total_raw_material_edges": sum([edge['count'] for edge in edge_counts])
        }
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """원자재 엣지 생성 메인 실행"""
    print("=== KB Fortress AI 원자재 엣지 생성기 ===")
    
    generator = RawMaterialEdgeGenerator()
    
    try:
        # 1. 모든 원자재 엣지 생성
        results = generator.generate_all_raw_material_edges()
        
        print(f"\n{'='*60}")
        print("️ 원자재 엣지 생성 결과")
        print(f"{'='*60}")
        print(f"기업-원자재 의존도: {results['company_raw_material_edges']}개")
        print(f"뉴스-원자재 영향: {results['news_raw_material_edges']}개")
        print(f"원자재 상관관계: {results['raw_material_correlation_edges']}개")
        print(f"공급망 연쇄: {results['supply_chain_edges']}개")
        print(f"총 엣지: {results['total_edges']}개")
        
        # 2. 그래프 구조 요약
        summary = generator.get_raw_material_graph_summary()
        
        print(f"\n 원자재 그래프 구조:")
        for edge_info in summary['edge_type_counts']:
            print(f"  {edge_info['edge_type']}: {edge_info['count']}개")
        
        print(f"\n 멀티홉 경로 샘플:")
        for path in summary['sample_multihop_paths']:
            print(f"   {path['news'][:30]}...")
            print(f"    → {path['material']} ({path['impact']})")
            print(f"    → {path['company']} ({path['dependency']} 의존)")
            print()
        
    except Exception as e:
        print(f" 원자재 엣지 생성 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        generator.cleanup()

if __name__ == "__main__":
    main()