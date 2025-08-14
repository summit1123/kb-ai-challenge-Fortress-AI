#!/usr/bin/env python3
"""
KB Fortress AI - Main Service
통합 에이전트 + 웹 인터페이스 + 알림 시스템
"""

import os
import sys
from typing import Dict, Any
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'graph'))

from agents.kb_fortress_unified_agent import KBFortressUnifiedAgent
from agents.ultimate_multihop_analyzer import UltimateMultihopAnalyzer
from services.simple_notification import SimpleNotificationService
from graph.enhanced_relationships import EnhancedRelationshipManager

class KBFortressMainService:
    """KB Fortress AI 메인 서비스"""
    
    def __init__(self):
        self.unified_agent = KBFortressUnifiedAgent()
        self.multihop_analyzer = UltimateMultihopAnalyzer()
        self.notification_service = SimpleNotificationService()
        self.relationship_manager = EnhancedRelationshipManager()
        
        print(" KB Fortress AI 메인 서비스 초기화 완료 (멀티홉 분석 포함)")
    
    def register_company_and_analyze(self, company_form_data: Dict[str, Any]) -> Dict[str, Any]:
        """기업 등록 및 초기 분석"""
        print(f" {company_form_data['company_name']} 기업 등록 및 분석 시작...")
        
        # 폼 데이터를 에이전트 입력 형태로 변환
        agent_input = self._convert_form_to_agent_input(company_form_data)
        
        # 통합 에이전트로 처리
        agent_result = self.unified_agent.process_request(agent_input)
        
        # 멀티홉 위험 분석 추가 실행
        multihop_assessment = self.multihop_analyzer.analyze_company_multihop_risks(
            company_form_data['company_name']
        )
        
        if agent_result["success"]:
            # 알림 발송
            notification_result = self.notification_service.send_initial_analysis(
                company_data=company_form_data,
                analysis_results=agent_result["analysis_results"]
            )
            
            # Neo4j에 초기 리포트 관계 생성
            report_data = {
                'report_path': notification_result["html_report"],
                'risk_level': agent_result["analysis_results"].get("overall_risk_level", "MEDIUM"),
                'summary': agent_result["final_report"][:500],
                'confidence': agent_result.get("confidence_score", 0.8)
            }
            
            relationship_created = self.relationship_manager.create_initial_report_relationship(
                company_form_data["company_name"],
                report_data
            )
            
            return {
                "success": True,
                "company_name": company_form_data["company_name"],
                "node_id": agent_result.get("company_node_id"),
                "final_report": agent_result["final_report"],
                "html_report_path": notification_result["html_report"],
                "report_relationship_created": relationship_created,
                "message": f"{company_form_data['company_name']} 등록 및 분석이 완료되었습니다.",
                # 기업 데이터 추가
                "company_data": company_form_data,
                # 구조화된 분석 결과 추가
                "analysis_results": agent_result.get("analysis_results", {}),
                "risk_assessment": agent_result.get("risk_assessment", {}),
                "section_explanations": agent_result.get("section_explanations", {}),
                "graph_paths": agent_result.get("graph_paths", {}),
                "confidence_score": agent_result.get("confidence_score", 0.8),
                #  멀티홉 분석 결과 추가
                "multihop_analysis": {
                    "composite_risk_score": multihop_assessment.composite_risk_score,
                    "risk_paths_count": len(multihop_assessment.risk_paths),
                    "primary_risk_factors": multihop_assessment.primary_risk_factors,
                    "recommended_solutions": multihop_assessment.recommended_solutions,
                    "risk_mitigation_strategies": multihop_assessment.risk_mitigation_strategies,
                    "detailed_report": self.multihop_analyzer.generate_analysis_report(multihop_assessment)
                }
            }
        else:
            return {
                "success": False,
                "error": agent_result.get("error", "알 수 없는 오류") if 'agent_result' in locals() else "분석 중 오류 발생",
                "message": "기업 등록에 실패했습니다.",
                "multihop_analysis": {
                    "composite_risk_score": multihop_assessment.composite_risk_score if 'multihop_assessment' in locals() else 0,
                    "risk_paths_count": len(multihop_assessment.risk_paths) if 'multihop_assessment' in locals() else 0,
                    "primary_risk_factors": multihop_assessment.primary_risk_factors if 'multihop_assessment' in locals() else [],
                    "recommended_solutions": multihop_assessment.recommended_solutions if 'multihop_assessment' in locals() else [],
                    "risk_mitigation_strategies": multihop_assessment.risk_mitigation_strategies if 'multihop_assessment' in locals() else [],
                    "detailed_report": "분석 실패로 인해 상세 보고서를 생성할 수 없습니다."
                }
            }
    
    def simulate_risk_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """리스크 이벤트 시뮬레이션 (실제로는 자동 감지)"""
        print(f" 리스크 이벤트 시뮬레이션: {event_data.get('title', 'N/A')}")
        
        # 모든 UserCompany 조회
        user_companies = self._get_all_user_companies()
        
        affected_companies = []
        
        for company in user_companies:
            # 각 기업별 이벤트 영향 분석
            analysis_query = f"{company['companyName']}에 대한 {event_data['title']}의 영향을 분석해주세요"
            
            agent_result = self.unified_agent.process_request(analysis_query)
            
            if agent_result["success"]:
                # 리스크 알림 발송
                notification_result = self.notification_service.send_risk_alert(
                    company_data=company,
                    risk_event=event_data,
                    analysis_results={"impact_summary": agent_result["final_report"][:200]}
                )
                
                # Neo4j에 알림 리포트 관계 생성
                alert_data = {
                    'report_path': notification_result["alert_report"],
                    'estimated_impact': agent_result["analysis_results"].get("estimated_impact", "분석 중"),
                    'action_required': agent_result["analysis_results"].get("recommended_actions", ["전문가 상담 권장"])[0] if agent_result["analysis_results"].get("recommended_actions") else "전문가 상담 권장",
                    'impact_level': event_data.get('severity', 'MEDIUM'),
                    'estimated_cost': agent_result["analysis_results"].get("estimated_monthly_cost", 0),
                    'rationale': agent_result["final_report"][:200]
                }
                
                alert_relationship_created = self.relationship_manager.create_alert_report_relationship(
                    company['companyName'],
                    event_data,
                    alert_data
                )
                
                affected_companies.append({
                    "company_name": company['companyName'],
                    "impact_analysis": agent_result["final_report"],
                    "alert_report": notification_result["alert_report"],
                    "alert_relationship_created": alert_relationship_created
                })
        
        return {
            "success": True,
            "event": event_data["title"],
            "affected_companies": len(affected_companies),
            "company_reports": affected_companies,
            "message": f"{len(affected_companies)}개 기업에 리스크 알림을 발송했습니다."
        }
    
    def query_company_analysis(self, company_name: str, question: str) -> Dict[str, Any]:
        """기업별 분석 질의"""
        print(f" {company_name} 분석 질의: '{question}'")
        
        # 통합 에이전트로 질의 처리
        full_query = f"{company_name}에 대해 {question}"
        agent_result = self.unified_agent.process_request(full_query)
        
        return {
            "success": agent_result["success"],
            "company_name": company_name,
            "question": question,
            "analysis_report": agent_result.get("final_report", "분석 실패"),
            "confidence_score": agent_result.get("confidence_score", 0.0),
            "message": "분석이 완료되었습니다." if agent_result["success"] else "분석에 실패했습니다."
        }
    
    def _convert_form_to_agent_input(self, form_data: Dict[str, Any]) -> str:
        """웹 폼 데이터를 에이전트 입력으로 변환"""
        return f"""회사명: {form_data.get('company_name', '')}
업종: {form_data.get('industry_code', '')}
위치: {form_data.get('location', '')}
매출: {form_data.get('annual_revenue', 0)}억원
직원: {form_data.get('employee_count', 0)}명
부채: {form_data.get('total_debt', 0)}억원
변동금리대출비중: {form_data.get('variable_debt_ratio', 70)}%
수출비중: {form_data.get('export_ratio', 20)}%"""
    
    def _get_all_user_companies(self) -> list:
        """모든 UserCompany 조회"""
        query = """
        MATCH (u:UserCompany)
        RETURN u.companyName as companyName,
               u.industryDescription as industry,
               u.location as location,
               u.revenue as revenue,
               u.notificationEmail as email
        """
        
        return self.unified_agent.neo4j_manager.execute_query(query)
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 현황 조회"""
        # Neo4j 연결 상태 확인
        try:
            node_count_query = """
            MATCH (n) RETURN count(n) as total_nodes
            """
            node_result = self.unified_agent.neo4j_manager.execute_query(node_count_query)
            total_nodes = node_result[0]['total_nodes'] if node_result else 0
            
            # UserCompany 개수
            user_company_query = """
            MATCH (u:UserCompany) RETURN count(u) as user_companies
            """
            user_result = self.unified_agent.neo4j_manager.execute_query(user_company_query)
            user_companies = user_result[0]['user_companies'] if user_result else 0
            
            return {
                "system_status": "HEALTHY",
                "neo4j_connected": True,
                "total_nodes": total_nodes,
                "registered_companies": user_companies,
                "last_updated": datetime.now().isoformat(),
                "message": "시스템이 정상적으로 작동 중입니다."
            }
            
        except Exception as e:
            return {
                "system_status": "ERROR",
                "neo4j_connected": False,
                "error": str(e),
                "message": "시스템에 오류가 발생했습니다."
            }
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'unified_agent') and self.unified_agent:
            self.unified_agent.cleanup()
        if hasattr(self, 'relationship_manager') and self.relationship_manager:
            self.relationship_manager.cleanup()

def main():
    """메인 서비스 테스트"""
    print("=== KB Fortress AI 메인 서비스 테스트 ===")
    
    service = KBFortressMainService()
    
    try:
        # 1. 시스템 상태 확인
        status = service.get_system_status()
        print(f" 시스템 상태: {status['system_status']}")
        print(f" 총 노드 수: {status.get('total_nodes', 0)}")
        print(f" 등록 기업 수: {status.get('registered_companies', 0)}")
        
        # 2. 테스트 기업 등록
        test_company_data = {
            "company_name": "혁신제조",
            "industry_code": "기계제조업",
            "location": "경기도 수원시",
            "annual_revenue": 150,
            "employee_count": 60,
            "total_debt": 40,
            "variable_debt_ratio": 80,
            "export_ratio": 35,
            "notification_email": "ceo@innovation.com"
        }
        
        print(f"\n 테스트 기업 등록: {test_company_data['company_name']}")
        registration_result = service.register_company_and_analyze(test_company_data)
        
        if registration_result["success"]:
            print(f" 등록 성공: {registration_result['message']}")
            print(f" HTML 보고서: {registration_result['html_report_path']}")
            
            # 3. 추가 질의 테스트
            print(f"\n 추가 분석 테스트")
            query_result = service.query_company_analysis(
                test_company_data['company_name'],
                "현재 가장 큰 리스크 요인은 무엇인가요?"
            )
            
            if query_result["success"]:
                print(f" 질의 성공 (신뢰도: {query_result['confidence_score']:.2f})")
            
            # 4. 리스크 이벤트 시뮬레이션
            print(f"\n 리스크 이벤트 시뮬레이션")
            test_event = {
                "title": "한국은행 기준금리 0.5%p 인상",
                "severity": "HIGH",
                "description": "기준금리가 3.5%에서 4.0%로 인상되었습니다."
            }
            
            event_result = service.simulate_risk_event(test_event)
            
            if event_result["success"]:
                print(f" 이벤트 처리 완료: {event_result['message']}")
                for company_report in event_result["company_reports"]:
                    print(f"    {company_report['company_name']}: {company_report['alert_report']}")
        else:
            print(f" 등록 실패: {registration_result['error']}")
        
    except Exception as e:
        print(f" 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        service.cleanup()

if __name__ == "__main__":
    main()