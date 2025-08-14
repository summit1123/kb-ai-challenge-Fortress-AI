#!/usr/bin/env python3
"""
KB Fortress AI - Enhanced Relationship Management
리포트 및 이벤트 추적을 위한 고급 관계 관리
"""

import os
import sys
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__)))
from neo4j_manager import Neo4jManager

class EnhancedRelationshipManager:
    """고급 관계 관리자"""
    
    def __init__(self):
        # Neo4j 연결
        os.environ['NEO4J_URI'] = 'neo4j://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = r'ehdgusdl11!'
        self.neo4j_manager = Neo4jManager()
        
    def create_initial_report_relationship(self, company_name: str, report_data: Dict[str, Any]) -> bool:
        """최초 분석 리포트 관계 생성"""
        
        # 먼저 AnalysisReport 노드 생성
        create_report_query = """
        CREATE (ar:AnalysisReport {
            reportId: $report_id,
            reportType: 'INITIAL',
            generatedAt: datetime(),
            reportPath: $report_path,
            riskLevel: $risk_level,
            companyName: $company_name,
            summary: $summary,
            confidence: $confidence
        })
        RETURN ar.reportId as reportId
        """
        
        report_id = f"initial_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # AnalysisReport 노드 생성
            self.neo4j_manager.execute_query(create_report_query, {
                'report_id': report_id,
                'report_path': report_data.get('report_path', ''),
                'risk_level': report_data.get('risk_level', 'MEDIUM'),
                'company_name': company_name,
                'summary': report_data.get('summary', '초기 분석 완료')[:500],  # 500자 제한
                'confidence': report_data.get('confidence', 0.8)
            })
            
            # UserCompany와 관계 생성
            create_relationship_query = """
            MATCH (u:UserCompany {companyName: $company_name}), 
                  (ar:AnalysisReport {reportId: $report_id})
            CREATE (u)-[:HAS_INITIAL_REPORT {
                generatedAt: datetime(),
                reportType: 'INITIAL',
                accessCount: 0,
                lastAccessed: null
            }]->(ar)
            RETURN count(*) as created
            """
            
            result = self.neo4j_manager.execute_query(create_relationship_query, {
                'company_name': company_name,
                'report_id': report_id
            })
            
            success = result[0]['created'] > 0 if result else False
            print(f" {company_name} 최초 분석 리포트 관계 생성: {report_id}")
            
            return success
            
        except Exception as e:
            print(f" 최초 리포트 관계 생성 실패: {e}")
            return False
    
    def create_alert_report_relationship(self, company_name: str, event_data: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """알림 리포트 관계 생성"""
        
        # 먼저 RiskEvent 노드 생성 (없다면)
        create_event_query = """
        MERGE (re:RiskEvent {
            eventId: $event_id,
            eventType: $event_type,
            title: $title,
            description: $description,
            severity: $severity,
            occurredAt: datetime()
        })
        RETURN re.eventId as eventId
        """
        
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        try:
            # RiskEvent 노드 생성
            self.neo4j_manager.execute_query(create_event_query, {
                'event_id': event_id,
                'event_type': event_data.get('event_type', 'MARKET_CHANGE'),
                'title': event_data.get('title', ''),
                'description': event_data.get('description', ''),
                'severity': event_data.get('severity', 'MEDIUM')
            })
            
            # AlertReport 노드 생성
            alert_id = f"alert_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            create_alert_query = """
            CREATE (ar:AlertReport {
                alertId: $alert_id,
                reportType: 'ALERT',
                generatedAt: datetime(),
                reportPath: $report_path,
                triggeredBy: $triggered_by,
                severity: $severity,
                companyName: $company_name,
                estimatedImpact: $estimated_impact,
                actionRequired: $action_required
            })
            RETURN ar.alertId as alertId
            """
            
            self.neo4j_manager.execute_query(create_alert_query, {
                'alert_id': alert_id,
                'report_path': alert_data.get('report_path', ''),
                'triggered_by': event_data.get('title', ''),
                'severity': event_data.get('severity', 'MEDIUM'),
                'company_name': company_name,
                'estimated_impact': alert_data.get('estimated_impact', '분석 중'),
                'action_required': alert_data.get('action_required', '전문가 상담 권장')
            })
            
            # UserCompany - AlertReport 관계
            create_alert_relationship_query = """
            MATCH (u:UserCompany {companyName: $company_name}), 
                  (ar:AlertReport {alertId: $alert_id})
            CREATE (u)-[:RECEIVED_ALERT {
                receivedAt: datetime(),
                isRead: false,
                urgency: $urgency,
                responseDeadline: datetime() + duration('P7D')  // 7일 후
            }]->(ar)
            RETURN count(*) as created
            """
            
            self.neo4j_manager.execute_query(create_alert_relationship_query, {
                'company_name': company_name,
                'alert_id': alert_id,
                'urgency': 'HIGH' if event_data.get('severity') == 'HIGH' else 'MEDIUM'
            })
            
            # RiskEvent - UserCompany 영향 관계
            create_impact_query = """
            MATCH (re:RiskEvent {eventId: $event_id}), 
                  (u:UserCompany {companyName: $company_name})
            CREATE (re)-[:AFFECTS {
                impactLevel: $impact_level,
                estimatedCost: $estimated_cost,
                rationale: $rationale,
                affectedAt: datetime()
            }]->(u)
            RETURN count(*) as created
            """
            
            self.neo4j_manager.execute_query(create_impact_query, {
                'event_id': event_id,
                'company_name': company_name,
                'impact_level': alert_data.get('impact_level', 'MEDIUM'),
                'estimated_cost': alert_data.get('estimated_cost', 0),
                'rationale': alert_data.get('rationale', '리스크 요인에 노출됨')
            })
            
            print(f" {company_name} 알림 리포트 관계 생성: {alert_id}")
            return True
            
        except Exception as e:
            print(f" 알림 리포트 관계 생성 실패: {e}")
            return False
    
    def get_company_report_history(self, company_name: str) -> Dict[str, Any]:
        """기업의 모든 리포트 이력 조회"""
        
        query = """
        MATCH (u:UserCompany {companyName: $company_name})
        
        // 최초 분석 리포트
        OPTIONAL MATCH (u)-[r1:HAS_INITIAL_REPORT]->(ir:AnalysisReport)
        
        // 알림 리포트들
        OPTIONAL MATCH (u)-[r2:RECEIVED_ALERT]->(ar:AlertReport)
        
        RETURN u.companyName as companyName,
               collect(DISTINCT {
                   type: 'INITIAL',
                   reportId: ir.reportId,
                   generatedAt: ir.generatedAt,
                   reportPath: ir.reportPath,
                   riskLevel: ir.riskLevel,
                   accessCount: r1.accessCount
               }) as initialReports,
               collect(DISTINCT {
                   type: 'ALERT', 
                   alertId: ar.alertId,
                   generatedAt: ar.generatedAt,
                   reportPath: ar.reportPath,
                   triggeredBy: ar.triggeredBy,
                   severity: ar.severity,
                   isRead: r2.isRead,
                   urgency: r2.urgency
               }) as alertReports
        """
        
        try:
            result = self.neo4j_manager.execute_query(query, {'company_name': company_name})
            
            if result:
                data = result[0]
                return {
                    "company_name": data['companyName'],
                    "initial_reports": [r for r in data['initialReports'] if r['reportId']],
                    "alert_reports": [r for r in data['alertReports'] if r['alertId']],
                    "total_reports": len([r for r in data['initialReports'] if r['reportId']]) + 
                                   len([r for r in data['alertReports'] if r['alertId']])
                }
            else:
                return {"company_name": company_name, "initial_reports": [], "alert_reports": [], "total_reports": 0}
                
        except Exception as e:
            print(f" 리포트 이력 조회 실패: {e}")
            return {"error": str(e)}
    
    def mark_alert_as_read(self, company_name: str, alert_id: str) -> bool:
        """알림을 읽음으로 표시"""
        
        query = """
        MATCH (u:UserCompany {companyName: $company_name})-[r:RECEIVED_ALERT]->(ar:AlertReport {alertId: $alert_id})
        SET r.isRead = true, r.readAt = datetime()
        RETURN count(*) as updated
        """
        
        try:
            result = self.neo4j_manager.execute_query(query, {
                'company_name': company_name,
                'alert_id': alert_id
            })
            
            success = result[0]['updated'] > 0 if result else False
            if success:
                print(f" 알림 읽음 처리: {alert_id}")
            
            return success
            
        except Exception as e:
            print(f" 알림 읽음 처리 실패: {e}")
            return False
    
    def get_unread_alerts_count(self, company_name: str) -> int:
        """읽지 않은 알림 개수 조회"""
        
        query = """
        MATCH (u:UserCompany {companyName: $company_name})-[r:RECEIVED_ALERT]->(ar:AlertReport)
        WHERE r.isRead = false
        RETURN count(*) as unreadCount
        """
        
        try:
            result = self.neo4j_manager.execute_query(query, {'company_name': company_name})
            return result[0]['unreadCount'] if result else 0
            
        except Exception as e:
            print(f" 읽지 않은 알림 조회 실패: {e}")
            return 0
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'neo4j_manager') and self.neo4j_manager:
            self.neo4j_manager.close()

def main():
    """Enhanced Relationship Manager 테스트"""
    print("=== KB Fortress AI Enhanced Relationship Manager 테스트 ===")
    
    manager = EnhancedRelationshipManager()
    
    try:
        # 1. 최초 분석 리포트 관계 생성 테스트
        test_company = "혁신제조"
        
        initial_report_data = {
            'report_path': 'reports/혁신제조_initial_20250814.html',
            'risk_level': 'MEDIUM',
            'summary': '혁신제조의 초기 리스크 분석이 완료되었습니다. 주요 리스크는 금리 및 환율 변동입니다.',
            'confidence': 0.85
        }
        
        print(f"\n1. {test_company} 최초 분석 리포트 관계 생성...")
        result1 = manager.create_initial_report_relationship(test_company, initial_report_data)
        print(f"결과: {'성공' if result1 else '실패'}")
        
        # 2. 알림 리포트 관계 생성 테스트
        event_data = {
            'title': '한국은행 기준금리 0.25%p 인상',
            'description': '기준금리가 기존 3.5%에서 3.75%로 인상되었습니다.',
            'severity': 'HIGH',
            'event_type': 'INTEREST_RATE_CHANGE'
        }
        
        alert_data = {
            'report_path': 'reports/혁신제조_alert_20250814.html',
            'estimated_impact': '월 추가 이자부담 약 180만원 예상',
            'action_required': 'KB 고정금리 전환대출 상담 권장',
            'impact_level': 'HIGH',
            'estimated_cost': 1800000,  # 월 180만원
            'rationale': '변동금리 대출 80% 보유로 인한 직접적 영향'
        }
        
        print(f"\n2. {test_company} 알림 리포트 관계 생성...")
        result2 = manager.create_alert_report_relationship(test_company, event_data, alert_data)
        print(f"결과: {'성공' if result2 else '실패'}")
        
        # 3. 리포트 이력 조회 테스트
        print(f"\n3. {test_company} 리포트 이력 조회...")
        history = manager.get_company_report_history(test_company)
        
        if 'error' not in history:
            print(f" 총 리포트: {history['total_reports']}개")
            print(f"   - 최초 분석: {len(history['initial_reports'])}개")
            print(f"   - 알림 리포트: {len(history['alert_reports'])}개")
            
            # 읽지 않은 알림 개수
            unread_count = manager.get_unread_alerts_count(test_company)
            print(f"   - 읽지 않은 알림: {unread_count}개")
        else:
            print(f" 조회 실패: {history['error']}")
            
    except Exception as e:
        print(f" 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()