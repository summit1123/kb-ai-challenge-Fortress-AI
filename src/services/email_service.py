#!/usr/bin/env python3
"""
KB Fortress AI - Email Notification Service
이메일 알림 발송 서비스
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
import json

class EmailService:
    """이메일 알림 서비스"""
    
    def __init__(self):
        # Gmail SMTP 설정 (시간상 이슈로 직접 연결은 못했습니다 ㅜㅜ)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("KB_EMAIL", "kb.fortress.ai@gmail.com")
        self.sender_password = os.getenv("KB_EMAIL_PASSWORD", "your_app_password")
        self.sender_name = "KB Fortress AI"
        
    def send_initial_analysis_report(self, company_data: Dict, analysis_results: Dict, recipient_email: str):
        """초기 분석 보고서 이메일 발송"""
        
        subject = f"[KB Fortress AI] {company_data['company_name']} 초기 리스크 분석 보고서"
        
        # HTML 이메일 템플릿
        html_body = self._generate_initial_report_html(company_data, analysis_results)
        
        return self._send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_body=html_body,
            email_type="initial_analysis"
        )
    
    def send_risk_alert(self, company_data: Dict, risk_event: Dict, analysis_results: Dict, recipient_email: str):
        """리스크 경고 알림 이메일 발송"""
        
        risk_level = risk_event.get('severity', 'MEDIUM')
        emoji = "" if risk_level == "HIGH" else "" if risk_level == "MEDIUM" else ""
        
        subject = f"{emoji} [KB Fortress AI] {company_data['company_name']} 긴급 리스크 알림"
        
        html_body = self._generate_risk_alert_html(company_data, risk_event, analysis_results)
        
        return self._send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_body=html_body,
            email_type="risk_alert"
        )
    
    def _generate_initial_report_html(self, company_data: Dict, analysis_results: Dict) -> str:
        """초기 분석 보고서 HTML 생성"""
        
        # 리스크 점수 계산
        risk_score = analysis_results.get('overall_risk_score', 0.65)
        risk_level = "HIGH" if risk_score >= 0.7 else "MEDIUM" if risk_score >= 0.4 else "LOW"
        risk_color = "#e74c3c" if risk_level == "HIGH" else "#f39c12" if risk_level == "MEDIUM" else "#27ae60"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .risk-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background: {risk_color}; }}
        .section {{ margin: 30px 0; padding: 20px; border-left: 4px solid #667eea; background: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 15px 10px 0; padding: 10px 15px; background: white; border-radius: 8px; border: 1px solid #e1e1e1; }}
        .recommendation {{ background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 10px 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> KB Fortress AI</h1>
            <h2>{company_data['company_name']} 초기 리스크 분석 보고서</h2>
            <p>등록일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h3> 종합 리스크 등급</h3>
                <div class="risk-badge">{risk_level}</div>
                <p>현재 {company_data['company_name']}의 종합 리스크 점수는 <strong>{risk_score:.1%}</strong>입니다.</p>
            </div>
            
            <div class="section">
                <h3> 기업 정보 요약</h3>
                <div class="metric"> 위치: {company_data.get('location', 'N/A')}</div>
                <div class="metric"> 업종: {company_data.get('industry_description', 'N/A')}</div>
                <div class="metric"> 매출: {company_data.get('revenue', 0)}억원</div>
                <div class="metric"> 직원: {company_data.get('employee_count', 0)}명</div>
                <div class="metric"> 수출비중: {company_data.get('export_ratio', 0)}%</div>
                <div class="metric"> 변동금리: {company_data.get('variable_debt_ratio', 0)}%</div>
            </div>
            
            <div class="section">
                <h3>️ 주요 리스크 요인</h3>
                {self._format_risk_factors(analysis_results.get('risk_factors', []))}
            </div>
            
            <div class="section">
                <h3> 추천 KB 금융상품</h3>
                {self._format_kb_products(analysis_results.get('kb_products', []))}
            </div>
            
            <div class="section">
                <h3>️ 활용 가능한 정부 지원정책</h3>
                {self._format_policies(analysis_results.get('policies', []))}
            </div>
            
            <div class="section">
                <h3> 실행 계획</h3>
                <div class="recommendation">
                    <strong>1. 즉시 실행</strong><br>
                    • KB 고정금리 전환대출 상담 예약<br>
                    • 정부 지원사업 신청 준비
                </div>
                <div class="recommendation">
                    <strong>2. 1개월 내</strong><br>
                    • 환헤지 상품 도입 검토<br>
                    • 원자재 조달 다변화 계획 수립
                </div>
                <div class="recommendation">
                    <strong>3. 3개월 내</strong><br>
                    • 재무구조 개선 로드맵 실행<br>
                    • 리스크 관리 체계 구축
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="btn"> KB 전문가 상담 예약</a>
                <a href="#" class="btn"> 상세 분석 보고서 다운로드</a>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>KB Fortress AI 자동 모니터링 서비스</strong></p>
            <p>앞으로 금융시장 변동 시 실시간 알림을 받으실 수 있습니다.</p>
            <p>문의: 1599-KB24 | support@kb-fortress.ai</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_risk_alert_html(self, company_data: Dict, risk_event: Dict, analysis_results: Dict) -> str:
        """리스크 알림 HTML 생성"""
        
        event_title = risk_event.get('title', '금융시장 변동')
        impact_amount = analysis_results.get('estimated_impact', {}).get('monthly_amount', 0)
        impact_direction = "증가" if impact_amount > 0 else "절감" if impact_amount < 0 else "변화 없음"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 700px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .alert-header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 25px; text-align: center; }}
        .content {{ padding: 25px; }}
        .event-box {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .impact-box {{ background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .action-box {{ background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #e74c3c; color: white; text-decoration: none; border-radius: 6px; margin: 5px; }}
        .urgent {{ font-weight: bold; color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="alert-header">
            <h1> 긴급 리스크 알림</h1>
            <h2>{company_data['company_name']}</h2>
            <p>{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 발생</p>
        </div>
        
        <div class="content">
            <div class="event-box">
                <h3> 발생 이벤트</h3>
                <p><strong>{event_title}</strong></p>
                <p>{risk_event.get('description', '금융시장에 중요한 변동이 발생했습니다.')}</p>
            </div>
            
            <div class="impact-box">
                <h3> 예상 영향</h3>
                <p class="urgent">월 예상 영향: {abs(impact_amount):,}만원 {impact_direction}</p>
                <p>{analysis_results.get('impact_rationale', '변동금리 대출로 인한 이자부담 변화가 예상됩니다.')}</p>
            </div>
            
            <div class="action-box">
                <h3> 권장 조치사항</h3>
                <ul>
                    {self._format_action_items(analysis_results.get('recommended_actions', []))}
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="btn"> 긴급 상담 신청</a>
                <a href="#" class="btn"> 상세 분석 보기</a>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666;">
            <p>KB Fortress AI 자동 모니터링 시스템 | 알림 설정 변경: support@kb-fortress.ai</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _format_risk_factors(self, risk_factors: List[Dict]) -> str:
        """리스크 요인 HTML 포맷팅"""
        if not risk_factors:
            return "<p>현재 특별한 리스크 요인이 감지되지 않았습니다.</p>"
        
        html = "<ul>"
        for factor in risk_factors:
            level = factor.get('level', 'MEDIUM')
            emoji = "" if level == "HIGH" else "" if level == "MEDIUM" else ""
            html += f"<li>{emoji} <strong>{factor.get('name', 'N/A')}</strong>: {factor.get('description', 'N/A')}</li>"
        html += "</ul>"
        return html
    
    def _format_kb_products(self, kb_products: List[Dict]) -> str:
        """KB 상품 HTML 포맷팅"""
        if not kb_products:
            return "<p>현재 추천할 수 있는 KB 상품이 없습니다.</p>"
        
        html = "<ul>"
        for product in kb_products[:3]:  # 상위 3개만
            score = product.get('eligibility_score', 0)
            html += f"<li><strong>{product.get('product_name', 'N/A')}</strong> (적합도: {score:.1%})<br>"
            html += f"<small>{product.get('description', 'KB 제조업 전용 금융상품입니다.')}</small></li>"
        html += "</ul>"
        return html
    
    def _format_policies(self, policies: List[Dict]) -> str:
        """정책 HTML 포맷팅"""
        if not policies:
            return "<p>현재 신청 가능한 정부 지원정책이 없습니다.</p>"
        
        html = "<ul>"
        for policy in policies[:3]:  # 상위 3개만
            html += f"<li><strong>{policy.get('policy_name', 'N/A')}</strong><br>"
            html += f"<small>지원분야: {policy.get('support_field', 'N/A')}</small></li>"
        html += "</ul>"
        return html
    
    def _format_action_items(self, actions: List[str]) -> str:
        """권장 조치사항 HTML 포맷팅"""
        if not actions:
            return "<li>전문가 상담을 통해 맞춤형 대응방안을 수립하세요.</li>"
        
        html = ""
        for action in actions:
            html += f"<li>{action}</li>"
        return html
    
    def _send_email(self, recipient_email: str, subject: str, html_body: str, email_type: str = "general") -> bool:
        """실제 이메일 발송"""
        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            # HTML 파트 추가
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f" 이메일 발송 성공: {recipient_email} ({email_type})")
            return True
            
        except Exception as e:
            print(f" 이메일 발송 실패: {str(e)}")
            return False
    
    def test_email_service(self):
        """이메일 서비스 테스트"""
        test_company_data = {
            'company_name': '테스트제조',
            'location': '서울시',
            'industry_description': '기계제조업',
            'revenue': 200,
            'employee_count': 80,
            'export_ratio': 30,
            'variable_debt_ratio': 70
        }
        
        test_analysis_results = {
            'overall_risk_score': 0.65,
            'risk_factors': [
                {'name': '금리 리스크', 'level': 'HIGH', 'description': '변동금리 대출 비중이 높음'},
                {'name': '환율 리스크', 'level': 'MEDIUM', 'description': '수출 비중으로 인한 환율 노출'}
            ],
            'kb_products': [
                {'product_name': 'KB 고정금리 전환대출', 'eligibility_score': 0.9, 'description': '변동금리를 고정금리로 전환'},
                {'product_name': 'KB 수출기업 환헤지', 'eligibility_score': 0.75, 'description': '환율 변동 리스크 헤지'}
            ],
            'policies': [
                {'policy_name': '중소기업 기술개발자금 지원', 'support_field': '제조업 R&D'}
            ]
        }
        
        # 테스트 이메일 발송
        return self.send_initial_analysis_report(
            company_data=test_company_data,
            analysis_results=test_analysis_results,
            recipient_email="test@example.com"  # 실제 테스트할 이메일로 변경
        )

def main():
    """이메일 서비스 테스트"""
    email_service = EmailService()
    result = email_service.test_email_service()
    print(f"테스트 결과: {'성공' if result else '실패'}")

if __name__ == "__main__":
    main()