#!/usr/bin/env python3
"""
KB Fortress AI - 간단한 알림 서비스
파일 기반 보고서 생성 + 콘솔 출력
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

class SimpleNotificationService:
    """간단한 파일 기반 알림 서비스"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def send_initial_analysis(self, company_data: Dict, analysis_results: Dict):
        """초기 분석 결과 알림"""
        company_name = company_data.get('company_name', '알 수 없는 기업')
        
        # 콘솔 출력
        print(f"\n" + "="*60)
        print(f" {company_name} 초기 분석 완료!")
        print("="*60)
        print(f" 리스크 등급: {self._get_risk_level(analysis_results)}")
        print(f" 추천 KB 상품: {len(analysis_results.get('kb_products', []))}개")
        print(f"️ 적용 가능 정책: {len(analysis_results.get('policies', []))}개")
        
        # HTML 보고서 생성
        report_path = self._generate_html_report(company_data, analysis_results, "initial")
        print(f" 상세 보고서: {report_path}")
        print("="*60)
        
        # JSON 데이터도 저장 (백업용)
        json_path = self._save_json_data(company_data, analysis_results, "initial")
        
        return {
            "success": True,
            "html_report": report_path,
            "json_data": json_path,
            "message": f"{company_name} 초기 분석이 완료되었습니다."
        }
    
    def send_risk_alert(self, company_data: Dict, risk_event: Dict, analysis_results: Dict):
        """리스크 경고 알림"""
        company_name = company_data.get('company_name', '알 수 없는 기업')
        event_title = risk_event.get('title', '금융시장 변동')
        
        # 콘솔 경고 출력
        print(f"\n" + ""*20)
        print(f" 긴급 리스크 알림: {company_name}")
        print(""*20)
        print(f" 이벤트: {event_title}")
        print(f"️ 영향도: {risk_event.get('severity', 'MEDIUM')}")
        print(f" 예상 영향: {analysis_results.get('estimated_impact', 'N/A')}")
        print(""*20)
        
        # 알림 보고서 생성
        report_path = self._generate_alert_html(company_data, risk_event, analysis_results)
        print(f" 알림 보고서: {report_path}")
        print(""*20)
        
        return {
            "success": True,
            "alert_report": report_path,
            "message": f"{company_name}에 대한 리스크 알림이 생성되었습니다."
        }
    
    def _generate_html_report(self, company_data: Dict, analysis_results: Dict, report_type: str) -> str:
        """간단한 HTML 보고서 생성"""
        company_name = company_data.get('company_name', '알 수 없는 기업')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_{report_type}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        risk_level = self._get_risk_level(analysis_results)
        risk_color = "#e74c3c" if risk_level == "HIGH" else "#f39c12" if risk_level == "MEDIUM" else "#27ae60"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{company_name} 분석 보고서</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .risk-badge {{ background: {risk_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }}
        .metric {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #667eea; }}
        .recommendation {{ background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1> KB Fortress AI</h1>
        <h2>{company_name} 분석 보고서</h2>
        <p>{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
    </div>
    
    <div class="section">
        <h3> 리스크 등급</h3>
        <span class="risk-badge">{risk_level}</span>
    </div>
    
    <div class="section">
        <h3> 기업 정보</h3>
        <div class="metric"> 위치: {company_data.get('location', 'N/A')}</div>
        <div class="metric"> 업종: {company_data.get('industry_description', 'N/A')}</div>
        <div class="metric"> 매출: {company_data.get('revenue', 0):,}억원</div>
        <div class="metric"> 직원: {company_data.get('employee_count', 0):,}명</div>
        <div class="metric"> 수출비중: {company_data.get('export_ratio', 0)}%</div>
    </div>
    
    <div class="section">
        <h3> 추천 KB 금융상품</h3>
        {self._format_kb_products_simple(analysis_results.get('kb_products', []))}
    </div>
    
    <div class="section">
        <h3>️ 적용 가능한 정부 정책</h3>
        {self._format_policies_simple(analysis_results.get('policies', []))}
    </div>
    
    <div class="section">
        <h3> 권장 조치사항</h3>
        <div class="recommendation">
            <strong>즉시 실행:</strong> KB 전문가 상담 예약 (1599-KB24)
        </div>
        <div class="recommendation">
            <strong>1개월 내:</strong> 추천 금융상품 검토 및 신청
        </div>
        <div class="recommendation">
            <strong>3개월 내:</strong> 리스크 관리 체계 구축
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
        <p>KB Fortress AI 자동 생성 보고서</p>
        <p>문의: support@kb-fortress.ai</p>
    </div>
</body>
</html>
        """
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_alert_html(self, company_data: Dict, risk_event: Dict, analysis_results: Dict) -> str:
        """리스크 알림 HTML 생성"""
        company_name = company_data.get('company_name', '알 수 없는 기업')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_alert_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        event_title = risk_event.get('title', '금융시장 변동')
        severity = risk_event.get('severity', 'MEDIUM')
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{company_name} 긴급 리스크 알림</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; }}
        .alert-header {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 25px; border-radius: 10px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .event-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
        .impact-box {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }}
        .action-box {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="alert-header">
        <h1> 긴급 리스크 알림</h1>
        <h2>{company_name}</h2>
        <p>{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
    </div>
    
    <div class="section">
        <div class="event-box">
            <h3> 발생 이벤트</h3>
            <p><strong>{event_title}</strong></p>
            <p>심각도: <strong>{severity}</strong></p>
        </div>
        
        <div class="impact-box">
            <h3> 예상 영향</h3>
            <p>{analysis_results.get('impact_summary', '금융시장 변동으로 인한 영향이 예상됩니다.')}</p>
        </div>
        
        <div class="action-box">
            <h3> 권장 조치사항</h3>
            <ul>
                <li>KB 전문가 긴급 상담 요청 (1599-KB24)</li>
                <li>변동금리 대출 고정금리 전환 검토</li>
                <li>유동성 확보 방안 점검</li>
            </ul>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
        <p>KB Fortress AI 자동 경고 시스템</p>
    </div>
</body>
</html>
        """
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _save_json_data(self, company_data: Dict, analysis_results: Dict, report_type: str) -> str:
        """JSON 데이터 저장"""
        company_name = company_data.get('company_name', '알 수 없는 기업')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_{report_type}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "company_data": company_data,
            "analysis_results": analysis_results,
            "report_type": report_type
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath
    
    def _get_risk_level(self, analysis_results: Dict) -> str:
        """리스크 레벨 계산"""
        macro_risks = analysis_results.get('macro_exposure', [])
        high_risks = [r for r in macro_risks if r.get('level') == 'HIGH']
        
        if len(high_risks) >= 2:
            return "HIGH"
        elif len(high_risks) >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _format_kb_products_simple(self, kb_products: list) -> str:
        """KB 상품 간단 포맷팅"""
        if not kb_products:
            return "<p>추천 상품이 없습니다.</p>"
        
        html = "<ul>"
        for product in kb_products[:3]:
            name = product.get('product', product.get('product_name', 'KB 금융상품'))
            score = product.get('score', product.get('eligibility_score', 0))
            html += f"<li><strong>{name}</strong> (적합도: {score:.1%})</li>"
        html += "</ul>"
        return html
    
    def _format_policies_simple(self, policies: list) -> str:
        """정책 간단 포맷팅"""
        if not policies:
            return "<p>적용 가능한 정책이 없습니다.</p>"
        
        html = "<ul>"
        for policy in policies[:3]:
            name = policy.get('policy', policy.get('policy_name', '정부 지원정책'))
            field = policy.get('field', policy.get('support_field', ''))
            html += f"<li><strong>{name}</strong>"
            if field:
                html += f" ({field})"
            html += "</li>"
        html += "</ul>"
        return html

def main():
    """간단한 알림 서비스 테스트"""
    notification = SimpleNotificationService()
    
    # 테스트 데이터
    test_company = {
        'company_name': '테스트제조',
        'location': '경기도 화성시',
        'industry_description': '자동차부품제조업',
        'revenue': 300,
        'employee_count': 120,
        'export_ratio': 20
    }
    
    test_analysis = {
        'macro_exposure': [
            {'indicator': '기준금리', 'level': 'HIGH'},
            {'indicator': '원달러환율', 'level': 'MEDIUM'}
        ],
        'kb_products': [
            {'product': 'KB 고정금리 전환대출', 'score': 0.9},
            {'product': 'KB 수출기업 환헤지', 'score': 0.7}
        ],
        'policies': [
            {'policy': '중소기업 기술개발자금', 'field': '제조업'}
        ]
    }
    
    # 초기 분석 알림 테스트
    result = notification.send_initial_analysis(test_company, test_analysis)
    print(f" 테스트 완료: {result['message']}")

if __name__ == "__main__":
    main()