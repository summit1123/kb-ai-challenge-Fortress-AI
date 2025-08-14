#!/usr/bin/env python3
"""
뉴스-원자재 영향 엣지 생성기
뉴스가 원자재 가격에 미치는 영향을 LLM으로 분석하여 엣지 생성
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.dirname(__file__))

from src.graph.neo4j_manager import Neo4jManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import json

class NewsRawMaterialEdgeCreator:
    """뉴스-원자재 영향 엣지 생성기"""
    
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
            print(" LLM 연결 성공")
        else:
            self.llm = None
            print(" LLM 없이 진행 (기본 규칙 기반)")
    
    def create_news_raw_material_edges(self) -> int:
        """뉴스-원자재 영향 엣지 생성"""
        print(" 뉴스-원자재 영향 엣지 생성 시작...")
        
        # 뉴스와 원자재 쌍 조회
        query = """
        MATCH (news:NewsArticle), (material:MacroIndicator)
        WHERE material.category = 'RAW_MATERIALS' OR material.indicatorName CONTAINS '가격지수' OR material.indicatorName CONTAINS '선물가격'
        RETURN news.title as news_title,
               news.summary as news_summary,
               news.publisher as news_publisher,
               material.indicatorName as material_name,
               material.category as material_category,
               material.value as material_value
        LIMIT 50
        """
        
        pairs = self.neo4j_manager.execute_query(query)
        print(f" 분석할 뉴스-원자재 쌍: {len(pairs)}개")
        
        total_edges = 0
        processed = 0
        
        for pair in pairs:
            processed += 1
            print(f" 진행: {processed}/{len(pairs)} - {pair['news_title'][:30]}... → {pair['material_name']}")
            
            # LLM으로 영향 관계 분석
            impact_analysis = self._analyze_news_material_impact(
                pair['news_title'], 
                pair.get('news_summary', ''),
                pair['material_name'],
                pair.get('material_category', 'RAW_MATERIALS')
            )
            
            if impact_analysis and impact_analysis.get('has_impact', False):
                # 엣지 생성
                success = self._create_impact_edge(
                    pair['news_title'],
                    pair['material_name'], 
                    impact_analysis
                )
                
                if success:
                    total_edges += 1
                    print(f"   엣지 생성: {impact_analysis['direction']} 영향 (신뢰도: {impact_analysis['confidence']:.2f})")
                else:
                    print(f"   엣지 생성 실패")
            else:
                print(f"  ️ 영향 없음")
        
        print(f" 뉴스-원자재 엣지 생성 완료: {total_edges}개")
        return total_edges
    
    def _analyze_news_material_impact(self, news_title: str, news_summary: str, 
                                    material_name: str, material_category: str) -> Optional[Dict[str, Any]]:
        """LLM으로 뉴스-원자재 영향 분석"""
        if not self.llm:
            # LLM 없을 때 기본 규칙 기반 분석
            return self._rule_based_impact_analysis(news_title, material_name)
        
        prompt = ChatPromptTemplate.from_template("""
        당신은 원자재 시장 전문가입니다. 뉴스가 원자재 가격에 미치는 영향을 분석하세요.

        === 뉴스 정보 ===
        제목: {news_title}
        요약: {news_summary}

        === 원자재 정보 ===
        원자재명: {material_name}
        카테고리: {material_category}

        다음 기준으로 분석하세요:
        1. 이 뉴스가 해당 원자재 가격에 영향을 미치는가?
        2. 영향 방향: POSITIVE(가격상승) or NEGATIVE(가격하락)
        3. 영향 크기: 0.1-1.0 (0.1: 미미한 영향, 1.0: 극대 영향)
        4. 시간 범위: SHORT_TERM(1개월), MEDIUM_TERM(3개월), LONG_TERM(6개월+)
        5. 신뢰도: 0.5-1.0
        6. 근거: 간단한 설명

        반드시 JSON 형식으로만 답변하세요:
        {{
            "has_impact": true/false,
            "direction": "POSITIVE/NEGATIVE",
            "magnitude": 0.1-1.0,
            "time_horizon": "SHORT_TERM/MEDIUM_TERM/LONG_TERM", 
            "confidence": 0.5-1.0,
            "reasoning": "영향 분석 근거"
        }}
        """)
        
        try:
            response = self.llm.invoke([
                HumanMessage(content=prompt.format(
                    news_title=news_title,
                    news_summary=news_summary or "요약 없음",
                    material_name=material_name,
                    material_category=material_category
                ))
            ])
            
            # JSON 파싱
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"   LLM 분석 실패: {e}")
            return self._rule_based_impact_analysis(news_title, material_name)
    
    def _rule_based_impact_analysis(self, news_title: str, material_name: str) -> Dict[str, Any]:
        """규칙 기반 영향 분석 (LLM 없을 때)"""
        news_lower = news_title.lower()
        material_lower = material_name.lower()
        
        # 기본 키워드 매칭
        impact_keywords = {
            '철강': ['철강', '철', '스틸', '제철', '조선', '자동차'],
            '알루미늄': ['알루미늄', '항공', '자동차', '포장'],
            '구리': ['구리', '전자', '전선', '건설'],
            '석유화학': ['석유', '화학', '플라스틱', '원유', '정유'],
            '반도체': ['반도체', '실리콘', '전자', 'IT'],
            '섬유': ['섬유', '의류', '면화', '폴리에스터']
        }
        
        # 영향 방향 키워드
        positive_keywords = ['상승', '인상', '증가', '급등', '강세', '부족', '공급부족']
        negative_keywords = ['하락', '인하', '감소', '급락', '약세', '과잉', '공급과잉']
        
        has_impact = False
        direction = "POSITIVE"
        magnitude = 0.3
        
        # 원자재별 키워드 매칭
        for material_key, keywords in impact_keywords.items():
            if any(keyword in material_lower for keyword in keywords):
                if any(keyword in news_lower for keyword in keywords):
                    has_impact = True
                    break
        
        # 일반적인 경제 뉴스도 체크
        general_keywords = ['금리', '환율', '인플레이션', '경기', '무역', '수출', '수입']
        if any(keyword in news_lower for keyword in general_keywords):
            has_impact = True
            magnitude = 0.5
        
        # 방향 결정
        if any(keyword in news_lower for keyword in positive_keywords):
            direction = "POSITIVE"
        elif any(keyword in news_lower for keyword in negative_keywords):
            direction = "NEGATIVE"
        
        return {
            "has_impact": has_impact,
            "direction": direction,
            "magnitude": magnitude,
            "time_horizon": "MEDIUM_TERM",
            "confidence": 0.6,
            "reasoning": "키워드 기반 자동 분석"
        }
    
    def _create_impact_edge(self, news_title: str, material_name: str, 
                          impact_analysis: Dict[str, Any]) -> bool:
        """영향 엣지 생성"""
        
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
            r.createdAt = datetime(),
            r.lastUpdated = datetime()
        RETURN count(r) as created
        """
        
        try:
            result = self.neo4j_manager.execute_query(edge_query, {
                "news_title": news_title,
                "material_name": material_name,
                "impact_direction": impact_analysis['direction'],
                "impact_magnitude": impact_analysis['magnitude'],
                "time_horizon": impact_analysis['time_horizon'],
                "confidence": impact_analysis['confidence'],
                "reasoning": impact_analysis['reasoning']
            })
            
            return result and result[0].get('created', 0) > 0
            
        except Exception as e:
            print(f"   엣지 생성 실패: {e}")
            return False
    
    def get_news_material_summary(self) -> Dict[str, Any]:
        """뉴스-원자재 관계 요약"""
        
        summary_query = """
        MATCH (news:NewsArticle)-[r:AFFECTS_PRICE]->(material:MacroIndicator)
        RETURN material.indicatorName as material,
               count(r) as news_count,
               avg(r.impactMagnitude) as avg_magnitude,
               avg(r.confidence) as avg_confidence,
               collect(r.impactDirection) as directions
        ORDER BY news_count DESC
        """
        
        results = self.neo4j_manager.execute_query(summary_query)
        
        return {
            "total_materials_with_news": len(results),
            "material_impact_summary": results
        }
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """뉴스-원자재 엣지 생성 메인 실행"""
    print("=== 뉴스-원자재 영향 엣지 생성기 ===")
    
    creator = NewsRawMaterialEdgeCreator()
    
    try:
        # 1. 뉴스-원자재 영향 엣지 생성
        edge_count = creator.create_news_raw_material_edges()
        
        # 2. 결과 요약
        summary = creator.get_news_material_summary()
        
        print(f"\n{'='*50}")
        print(" 뉴스-원자재 엣지 생성 결과")
        print(f"{'='*50}")
        print(f"생성된 엣지: {edge_count}개")
        print(f"영향받는 원자재: {summary['total_materials_with_news']}개")
        
        print(f"\n 원자재별 뉴스 영향 현황:")
        for material_info in summary['material_impact_summary']:
            directions = material_info['directions']
            positive_count = directions.count('POSITIVE')
            negative_count = directions.count('NEGATIVE')
            
            print(f"  {material_info['material']}: {material_info['news_count']}개 뉴스")
            print(f"    - 상승영향: {positive_count}개, 하락영향: {negative_count}개")
            print(f"    - 평균 영향도: {material_info['avg_magnitude']:.2f}")
            print(f"    - 평균 신뢰도: {material_info['avg_confidence']:.2f}")
        
    except Exception as e:
        print(f" 뉴스-원자재 엣지 생성 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        creator.cleanup()

if __name__ == "__main__":
    main()