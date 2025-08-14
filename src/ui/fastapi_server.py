#!/usr/bin/env python3
"""
KB Fortress AI - FastAPI Web Server
HTML 폼과 백엔드 시스템을 연결하는 FastAPI 웹서버
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from main_service import KBFortressMainService

# FastAPI 앱 생성
app = FastAPI(title="KB Fortress AI", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# KB Fortress AI 메인 서비스 (지연 초기화)
kb_service = None

# Pydantic 모델 정의
class CompanyRegistration(BaseModel):
    company_name: str
    industry_code: str
    location: str
    annual_revenue: float
    employee_count: int
    total_debt: float
    variable_debt_ratio: float = 70.0
    export_ratio: float = 20.0
    notification_email: Optional[str] = None
    raw_materials: Optional[list] = []

class RiskEvent(BaseModel):
    title: str
    severity: str = "MEDIUM"
    description: str

class CompanyQuery(BaseModel):
    company_name: str
    question: str

class AlertReadRequest(BaseModel):
    company_name: str
    alert_id: str

# 정적 파일 및 리포트 서빙
reports_dir = Path(__file__).parent.parent / "reports"
if reports_dir.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")

@app.get("/", response_class=HTMLResponse)
async def index():
    """메인 페이지 - 기업 등록 폼"""
    html_path = Path(__file__).parent / "company_registration.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # HTML의 JavaScript 부분을 실제 API 호출로 수정
    html_content = html_content.replace(
        'setTimeout(() => {',
        '''
        // 실제 서버로 데이터 전송
        fetch('/api/register_company', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert(' 기업 등록이 완료되었습니다!\\n\\n' + result.message + '\\n\\n초기 분석 보고서가 생성되었습니다.');
                
                // 보고서 보기 버튼 추가
                const reportBtn = document.createElement('button');
                reportBtn.textContent = ' 분석 보고서 보기';
                reportBtn.style.cssText = 'margin: 10px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;';
                reportBtn.onclick = () => window.open('/reports/' + result.report_filename, '_blank');
                document.querySelector('.submit-section').appendChild(reportBtn);
                
            } else {
                alert(' 등록 실패: ' + result.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(' 서버 오류가 발생했습니다: ' + error);
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = ' 기업 등록 및 초기 분석 시작';
        });
        
        /*setTimeout(() => {'''
    )
    
    return html_content

def get_kb_service():
    """KB 서비스 지연 초기화"""
    global kb_service
    if kb_service is None:
        print(" KB Fortress AI 서비스 초기화 중...")
        kb_service = KBFortressMainService()
    return kb_service

@app.post("/api/register_company")
async def register_company(company: CompanyRegistration):
    """기업 등록 API"""
    try:
        # Pydantic 모델을 dict로 변환
        company_data = company.dict()
        
        print(f" 기업 등록 요청: {company_data.get('company_name', 'N/A')}")
        
        # 메인 서비스로 처리 (지연 초기화)
        service = get_kb_service()
        result = service.register_company_and_analyze(company_data)
        
        if result["success"]:
            # HTML 보고서 파일명 추출
            report_path = result.get("html_report_path", "")
            report_filename = os.path.basename(report_path) if report_path else ""
            
            # 구조화된 분석 결과 포함
            analysis_results = result.get("analysis_results", {})
            risk_assessment = result.get("risk_assessment", {})
            
            return {
                "success": True,
                "message": result["message"],
                "company_name": result["company_name"],
                "node_id": result.get("node_id"),
                "report_filename": report_filename,
                "final_report": result["final_report"],
                "company_data": result.get("company_data", {}),
                "section_explanations": result.get("section_explanations", {}),
                "risk_assessment": result.get("risk_assessment", {}),
                "analysis_results": {
                    "overall_risk_level": risk_assessment.get("overall_risk_level", "MEDIUM"),
                    "risk_score": risk_assessment.get("risk_score", 0.5),
                    "kb_products": analysis_results.get("kb_products", []),
                    "policies": analysis_results.get("policies", []),
                    "news_impacts": analysis_results.get("news_impacts", []),
                    "macro_exposures": analysis_results.get("macro_exposure", []),
                    "key_risks": risk_assessment.get("key_risks", []),
                    "opportunities": risk_assessment.get("opportunities", []),
                    "graph_paths": result.get("graph_paths", {})
                },
                "confidence_score": result.get("confidence_score", 0.8),
                #  멀티홉 분석 결과 추가
                "multihop_analysis": result.get("multihop_analysis", {
                    "composite_risk_score": 0,
                    "risk_paths_count": 0,
                    "primary_risk_factors": [],
                    "recommended_solutions": [],
                    "risk_mitigation_strategies": [],
                    "detailed_report": "멀티홉 분석 결과 없음"
                })
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "알 수 없는 오류"))
            
    except Exception as e:
        print(f" API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query_company")
async def query_company(query: CompanyQuery):
    """기업 분석 질의 API"""
    try:
        print(f" 분석 질의: {query.company_name} - '{query.question}'")
        
        service = get_kb_service()
        result = service.query_company_analysis(query.company_name, query.question)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "분석 실패"))
            
        return {
            "success": result["success"],
            "company_name": result["company_name"],
            "question": result["question"],
            "analysis_report": result["analysis_report"],
            "confidence_score": result.get("confidence_score", 0.0),
            "message": result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" 질의 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate_risk")
async def simulate_risk(event: RiskEvent):
    """리스크 이벤트 시뮬레이션 API"""
    try:
        event_data = event.dict()
        
        print(f" 리스크 시뮬레이션: {event_data.get('title', 'N/A')}")
        
        service = get_kb_service()
        result = service.simulate_risk_event(event_data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "시뮬레이션 실패"))
            
        return {
            "success": result["success"],
            "event": result["event"],
            "affected_companies": result["affected_companies"],
            "message": result["message"],
            "company_reports": result.get("company_reports", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" 리스크 시뮬레이션 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system_status")
async def system_status():
    """시스템 상태 조회 API"""
    try:
        service = get_kb_service()
        status = service.get_system_status()
        return status
    except Exception as e:
        print(f" 상태 조회 API 오류: {e}")
        return {
            "system_status": "ERROR",
            "error": str(e),
            "message": "상태 조회 중 오류가 발생했습니다."
        }

@app.get("/api/analysis_details/{company_name}")
async def get_analysis_details(company_name: str):
    """기업 분석 상세 결과 조회 API"""
    try:
        # 통합 에이전트로 분석 데이터 조회
        query = f"{company_name}의 상세 분석 결과를 조회해주세요"
        service = get_kb_service()
        result = service.unified_agent.process_request(query)
        
        if result["success"]:
            return {
                "success": True,
                "company_name": company_name,
                "analysis_results": result.get("analysis_results", {}),
                "final_report": result.get("final_report", ""),
                "confidence_score": result.get("confidence_score", 0.85)
            }
        else:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
            
    except Exception as e:
        print(f" 분석 결과 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/company_report_history/{company_name}")
async def company_report_history(company_name: str):
    """기업별 리포트 이력 조회 API"""
    try:
        service = get_kb_service()
        history = service.relationship_manager.get_company_report_history(company_name)
        return history
    except Exception as e:
        print(f" 리포트 이력 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mark_alert_read")
async def mark_alert_read(request: AlertReadRequest):
    """알림 읽음 처리 API"""
    try:
        service = get_kb_service()
        success = service.relationship_manager.mark_alert_as_read(
            request.company_name, 
            request.alert_id
        )
        
        return {
            "success": success,
            "message": "알림을 읽음으로 표시했습니다." if success else "알림 처리에 실패했습니다."
        }
    except Exception as e:
        print(f" 알림 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis-result", response_class=HTMLResponse)
async def analysis_result():
    """분석 결과 페이지"""
    html_path = Path(__file__).parent / "analysis_result.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/reports-history", response_class=HTMLResponse)
async def reports_history():
    """기업 리포트 이력 페이지"""
    html_path = Path(__file__).parent / "company_reports.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """대시보드 페이지"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KB Fortress AI - 관리자 대시보드</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .status-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }
        .status-card h3 {
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        .status-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .actions {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 40px;
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-danger {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .results {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        #statusDisplay {
            text-align: center;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> KB Fortress AI 관리자 대시보드</h1>
            <p>실시간 시스템 모니터링 및 관리</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>시스템 상태</h3>
                <div class="value" id="systemStatus">-</div>
                <div>System Status</div>
            </div>
            <div class="status-card">
                <h3>총 노드 수</h3>
                <div class="value" id="totalNodes">-</div>
                <div>Total Nodes</div>
            </div>
            <div class="status-card">
                <h3>등록 기업</h3>
                <div class="value" id="registeredCompanies">-</div>
                <div>Companies</div>
            </div>
            <div class="status-card">
                <h3>Neo4j 연결</h3>
                <div class="value" id="neo4jStatus">-</div>
                <div>Database</div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn btn-primary" onclick="refreshStatus()"> 상태 새로고침</button>
            <button class="btn btn-primary" onclick="simulateRisk()"> 리스크 시뮬레이션</button>
            <button class="btn btn-primary" onclick="window.open('/', '_blank')"> 기업 등록 페이지</button>
            <button class="btn btn-primary" onclick="window.open('/reports-history', '_blank')"> 리포트 이력 조회</button>
        </div>
        
        <div class="results">
            <div id="statusDisplay">시스템 상태를 불러오는 중...</div>
        </div>
    </div>

    <script>
        // 페이지 로드 시 상태 조회
        window.onload = function() {
            refreshStatus();
        };

        function refreshStatus() {
            document.getElementById('statusDisplay').innerHTML = ' 시스템 상태를 조회하는 중...';
            
            fetch('/api/system_status')
                .then(response => response.json())
                .then(data => {
                    // 상태 카드 업데이트
                    document.getElementById('systemStatus').textContent = data.system_status;
                    document.getElementById('totalNodes').textContent = data.total_nodes || 0;
                    document.getElementById('registeredCompanies').textContent = data.registered_companies || 0;
                    document.getElementById('neo4jStatus').textContent = data.neo4j_connected ? '' : '';
                    
                    // 상태 메시지 업데이트
                    const statusColor = data.system_status === 'HEALTHY' ? 'green' : 'red';
                    document.getElementById('statusDisplay').innerHTML = 
                        `<span style="color: ${statusColor}; font-weight: bold;">${data.message}</span><br>
                         <small>마지막 업데이트: ${new Date(data.last_updated).toLocaleString()}</small>`;
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('statusDisplay').innerHTML = 
                        '<span style="color: red;"> 상태 조회 실패: ' + error + '</span>';
                });
        }

        function simulateRisk() {
            const confirmed = confirm('리스크 이벤트를 시뮬레이션하시겠습니까?\\n등록된 모든 기업에게 알림이 발송됩니다.');
            
            if (!confirmed) return;
            
            document.getElementById('statusDisplay').innerHTML = ' 리스크 시뮬레이션 실행 중...';
            
            const eventData = {
                title: '한국은행 기준금리 0.25%p 인상',
                severity: 'HIGH',
                description: '기준금리가 기존 대비 0.25%p 인상되어 변동금리 대출 이자부담이 증가할 것으로 예상됩니다.'
            };
            
            fetch('/api/simulate_risk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('statusDisplay').innerHTML = 
                        `<span style="color: green;"> ${data.message}</span><br>
                         <strong>이벤트:</strong> ${data.event}<br>
                         <strong>영향받은 기업:</strong> ${data.affected_companies}개<br>
                         <small>각 기업별 분석 보고서가 reports/ 폴더에 생성되었습니다.</small>`;
                } else {
                    document.getElementById('statusDisplay').innerHTML = 
                        `<span style="color: red;"> 시뮬레이션 실패: ${data.error}</span>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('statusDisplay').innerHTML = 
                    '<span style="color: red;"> 시뮬레이션 실행 실패: ' + error + '</span>';
            });
        }
    </script>
</body>
</html>
    """
    return dashboard_html

@app.get("/analysis-result", response_class=HTMLResponse)
async def analysis_result():
    """분석 결과 표시 페이지"""
    html_path = Path(__file__).parent / "analysis_result.html"
    
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return """
        <h1>분석 결과 페이지 로드 실패</h1>
        <p>analysis_result.html 파일을 찾을 수 없습니다.</p>
        <a href="/">돌아가기</a>
        """

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 리소스 정리"""
    global kb_service
    if kb_service and hasattr(kb_service, 'cleanup'):
        kb_service.cleanup()

if __name__ == '__main__':
    import uvicorn
    
    print(" KB Fortress AI FastAPI 서버 시작...")
    print(" 기업 등록 페이지: http://localhost:8000")  
    print(" 관리자 대시보드: http://localhost:8000/dashboard")
    print(" 리포트 이력 조회: http://localhost:8000/reports-history")
    print(" 보고서 폴더: http://localhost:8000/reports/")
    print(" API 문서: http://localhost:8000/docs")
    print(" 대화형 API 테스트: http://localhost:8000/redoc")
    
    # Uvicorn 서버 실행
    uvicorn.run(
        "fastapi_server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )