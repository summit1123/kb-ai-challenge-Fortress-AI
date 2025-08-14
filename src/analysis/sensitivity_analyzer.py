"""
민감도 분석 모듈
ReferenceCompany 데이터로 업종별 민감도 계수 계산 후
UserCompany에 개인화 적용
"""

import json
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class SensitivityCoefficient:
    """민감도 계수"""
    factor: str  # "interest_rate", "exchange_rate", "raw_material"
    coefficient: float  # 영향 계수 (-1.0 ~ 1.0)
    confidence: float   # 신뢰도 (0.0 ~ 1.0)
    rationale: str      # 근거 설명

@dataclass
class SectorPattern:
    """업종별 패턴"""
    sector_name: str
    total_companies: int
    avg_debt_ratio: float
    avg_export_ratio: float
    avg_variable_rate_exposure: float
    sensitivity_coefficients: List[SensitivityCoefficient]
    key_risks: List[str]

class SensitivityAnalyzer:
    """민감도 분석기"""
    
    def __init__(self):
        self.sector_patterns = {}
        self.load_reference_data()
    
    def load_reference_data(self):
        """ReferenceCompany 데이터 로드"""
        # DART에서 수집한 실제 기업 데이터 로드
        data_files = [f for f in os.listdir("data/raw") if f.startswith("company_data_") and f.endswith(".json")]
        if not data_files:
            print(" ReferenceCompany 데이터가 없습니다")
            return
            
        latest_file = sorted(data_files)[-1]
        filepath = os.path.join("data/raw", latest_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            company_data = json.load(f)
        
        print(f" ReferenceCompany 데이터 로드: {company_data['total_companies']}개 기업")
        
        # 업종별 패턴 계산
        self._calculate_sector_patterns(company_data['companies'])
    
    def _calculate_sector_patterns(self, companies: List[Dict]):
        """업종별 패턴 계산"""
        sector_groups = {}
        
        # 업종별 그룹핑
        for company in companies:
            sector = company.get("sector", "unknown")
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(company)
        
        # 업종별 민감도 계수 계산
        for sector_name, sector_companies in sector_groups.items():
            if not sector_companies:
                continue
                
            pattern = self._analyze_sector_sensitivity(sector_name, sector_companies)
            self.sector_patterns[sector_name] = pattern
            
            print(f" {pattern.sector_name} 업종 패턴 분석 완료: {pattern.total_companies}개 기업")
    
    def _analyze_sector_sensitivity(self, sector_name: str, companies: List[Dict]) -> SectorPattern:
        """개별 업종 민감도 분석"""
        
        # 기본 통계 계산
        total_companies = len(companies)
        avg_debt_ratio = np.mean([c.get("debt_ratio", 0) for c in companies])
        avg_export_ratio = np.mean([c.get("export_ratio_pct", 0) for c in companies]) 
        avg_variable_rate = np.mean([c.get("variable_rate_exposure", 0) for c in companies])
        
        # 민감도 계수 계산
        sensitivity_coefficients = []
        
        # 1. 금리 민감도
        interest_sensitivity = self._calculate_interest_sensitivity(companies)
        sensitivity_coefficients.append(interest_sensitivity)
        
        # 2. 환율 민감도  
        forex_sensitivity = self._calculate_forex_sensitivity(companies)
        sensitivity_coefficients.append(forex_sensitivity)
        
        # 3. 원자재 민감도
        material_sensitivity = self._calculate_material_sensitivity(companies)
        sensitivity_coefficients.append(material_sensitivity)
        
        # 주요 리스크 요인
        key_risks = self._identify_key_risks(sector_name, {
            "debt_ratio": avg_debt_ratio,
            "export_ratio": avg_export_ratio, 
            "variable_rate": avg_variable_rate
        })
        
        return SectorPattern(
            sector_name=sector_name,
            total_companies=total_companies,
            avg_debt_ratio=avg_debt_ratio,
            avg_export_ratio=avg_export_ratio,
            avg_variable_rate_exposure=avg_variable_rate,
            sensitivity_coefficients=sensitivity_coefficients,
            key_risks=key_risks
        )
    
    def _calculate_interest_sensitivity(self, companies: List[Dict]) -> SensitivityCoefficient:
        """금리 민감도 계산"""
        # 변동금리 노출도 기반 민감도 계산
        variable_rates = [c.get("variable_rate_exposure", 0) for c in companies]
        debt_ratios = [c.get("debt_ratio", 0) for c in companies]
        
        # 가중평균으로 민감도 계산 (변동금리 노출 * 부채비율)
        weighted_exposure = []
        for var_rate, debt_ratio in zip(variable_rates, debt_ratios):
            weighted_exposure.append(var_rate * debt_ratio)
        
        avg_weighted_exposure = np.mean(weighted_exposure)
        
        # 민감도 계수 (0~1 정규화)
        coefficient = min(avg_weighted_exposure * 2, 1.0)  # 최대 1.0으로 제한
        
        # 신뢰도 (데이터 일관성 기반)
        confidence = 1.0 - (np.std(weighted_exposure) / (np.mean(weighted_exposure) + 0.001))
        confidence = max(0.5, min(confidence, 1.0))  # 0.5~1.0 범위
        
        rationale = f"변동금리 평균 노출도 {np.mean(variable_rates):.1%}, 부채비율 평균 {np.mean(debt_ratios):.1%}"
        
        return SensitivityCoefficient(
            factor="interest_rate",
            coefficient=coefficient,
            confidence=confidence,
            rationale=rationale
        )
    
    def _calculate_forex_sensitivity(self, companies: List[Dict]) -> SensitivityCoefficient:
        """환율 민감도 계산"""
        export_ratios = [c.get("export_ratio_pct", 0) / 100 for c in companies]  # 백분율을 소수로 변환
        forex_scores = [c.get("forex_sensitivity_score", 0) for c in companies]
        
        # 수출비중과 환율 민감도 점수의 가중평균
        weighted_forex = []
        for export_ratio, forex_score in zip(export_ratios, forex_scores):
            # 수출비중이 높을수록 환율 상승 시 수익 증가 (양의 민감도)
            weighted_forex.append(export_ratio * 0.7 + forex_score * 0.3)
        
        avg_weighted_forex = np.mean(weighted_forex)
        
        # 환율 민감도는 양수/음수 모두 가능 (-1.0 ~ 1.0)
        coefficient = avg_weighted_forex
        
        confidence = 1.0 - (np.std(weighted_forex) / (abs(np.mean(weighted_forex)) + 0.001))
        confidence = max(0.5, min(confidence, 1.0))
        
        rationale = f"수출비중 평균 {np.mean(export_ratios)*100:.1f}%, 환율 민감도 평균 {np.mean(forex_scores):.2f}"
        
        return SensitivityCoefficient(
            factor="exchange_rate", 
            coefficient=coefficient,
            confidence=confidence,
            rationale=rationale
        )
    
    def _calculate_material_sensitivity(self, companies: List[Dict]) -> SensitivityCoefficient:
        """원자재 민감도 계산"""
        material_deps = [c.get("raw_material_dependency", 0) for c in companies]
        
        # 원자재 의존도가 높을수록 가격 상승 시 부정적 영향 (음의 민감도)
        avg_material_dep = np.mean(material_deps)
        coefficient = -avg_material_dep  # 음수로 설정 (비용 증가)
        
        confidence = 1.0 - (np.std(material_deps) / (np.mean(material_deps) + 0.001))
        confidence = max(0.5, min(confidence, 1.0))
        
        rationale = f"원자재 의존도 평균 {avg_material_dep:.1%}"
        
        return SensitivityCoefficient(
            factor="raw_material_price",
            coefficient=coefficient,
            confidence=confidence,
            rationale=rationale
        )
    
    def _identify_key_risks(self, sector_name: str, metrics: Dict) -> List[str]:
        """업종별 주요 리스크 요인 식별"""
        risks = []
        
        if metrics["variable_rate"] > 0.65:
            risks.append(f"금리 상승 리스크 (변동금리 노출 {metrics['variable_rate']:.1%})")
        
        if metrics["export_ratio"] > 30:
            risks.append(f"환율 변동 리스크 (수출비중 {metrics['export_ratio']:.0f}%)")
        
        if metrics["debt_ratio"] > 0.5:
            risks.append(f"부채 부담 리스크 (부채비율 {metrics['debt_ratio']:.1%})")
        
        # 업종별 특화 리스크
        if sector_name == "automotive_parts":
            risks.append("완성차 업체 의존도 리스크")
        elif sector_name == "steel":
            risks.append("원자재(철광석) 가격 변동 리스크")  
        elif sector_name == "chemicals":
            risks.append("나프타 등 유가 연동 리스크")
        
        return risks
    
    def calculate_user_company_sensitivity(self, user_input: Dict) -> Dict[str, Any]:
        """UserCompany 맞춤형 민감도 계산"""
        
        # 업종 매칭
        industry_sector = user_input.get("industry_sector", "").lower()
        matched_sector = self._match_sector(industry_sector)
        
        if not matched_sector:
            return {"error": "매칭되는 업종 패턴을 찾을 수 없습니다"}
        
        sector_pattern = self.sector_patterns[matched_sector]
        
        # 사용자 기업 특성 추출
        user_characteristics = self._extract_user_characteristics(user_input)
        
        # 개인화 민감도 계산
        personalized_sensitivity = {}
        
        for coeff in sector_pattern.sensitivity_coefficients:
            personal_coeff = self._personalize_coefficient(coeff, user_characteristics, sector_pattern)
            personalized_sensitivity[coeff.factor] = personal_coeff
        
        # 종합 리스크 점수
        overall_risk = self._calculate_overall_risk(personalized_sensitivity, user_characteristics)
        
        # 구체적 영향 추정
        impact_estimates = self._estimate_concrete_impacts(personalized_sensitivity, user_characteristics)
        
        return {
            "matched_sector": matched_sector,
            "sector_pattern": {
                "sector_name": sector_pattern.sector_name,
                "benchmark_companies": sector_pattern.total_companies,
                "key_risks": sector_pattern.key_risks
            },
            "personalized_sensitivity": personalized_sensitivity,
            "overall_risk_score": overall_risk,
            "impact_estimates": impact_estimates,
            "recommendations": self._generate_recommendations(overall_risk, personalized_sensitivity)
        }
    
    def _match_sector(self, industry_text: str) -> str:
        """업종 텍스트를 sector와 매칭"""
        industry_lower = industry_text.lower()
        
        if any(keyword in industry_lower for keyword in ["자동차", "부품", "automotive"]):
            return "automotive_parts"
        elif any(keyword in industry_lower for keyword in ["철강", "강", "steel"]):
            return "steel" 
        elif any(keyword in industry_lower for keyword in ["화학", "chemical"]):
            return "chemicals"
        
        return None
    
    def _extract_user_characteristics(self, user_input: Dict) -> Dict:
        """사용자 입력에서 특성 추출"""
        characteristics = {}
        
        # 매출 규모 추출
        revenue_text = user_input.get("revenue_text", "")
        if "억" in revenue_text:
            # "80억원" → 8000000000
            try:
                revenue_value = float(revenue_text.replace("억", "").replace("원", "").strip()) * 100000000
                characteristics["revenue"] = revenue_value
            except:
                characteristics["revenue"] = 0
        
        # 부채 정보 추출
        debt_text = user_input.get("debt_text", "")
        if "변동금리" in debt_text and "억" in debt_text:
            try:
                debt_value = float(debt_text.replace("변동금리", "").replace("대출", "").replace("억", "").replace("원", "").strip()) * 100000000
                characteristics["variable_debt"] = debt_value
                characteristics["has_variable_debt"] = True
            except:
                characteristics["variable_debt"] = 0
                characteristics["has_variable_debt"] = False
        
        # 수출 비중 추출
        export_text = user_input.get("export_ratio_text", "")
        if "%" in export_text:
            try:
                export_ratio = float(export_text.replace("%", "").strip())
                characteristics["export_ratio"] = export_ratio / 100  # 소수로 변환
            except:
                characteristics["export_ratio"] = 0
        
        return characteristics
    
    def _personalize_coefficient(self, base_coeff: SensitivityCoefficient, user_char: Dict, sector_pattern: SectorPattern) -> Dict:
        """기본 계수를 사용자 특성에 맞게 개인화"""
        
        personal_coeff = base_coeff.coefficient
        adjustment_reason = []
        
        if base_coeff.factor == "interest_rate":
            # 변동금리 대출 보유 여부
            if user_char.get("has_variable_debt", False):
                user_debt_ratio = user_char.get("variable_debt", 0) / max(user_char.get("revenue", 1), 1)
                sector_avg_variable = sector_pattern.avg_variable_rate_exposure
                
                if user_debt_ratio > sector_avg_variable * 0.1:  # 매출 대비 변동부채 비율
                    adjustment = 0.2  # 민감도 증가
                    personal_coeff = min(personal_coeff + adjustment, 1.0)
                    adjustment_reason.append(f"변동금리 대출 보유로 업종 평균 대비 +{adjustment:.1%} 상향")
        
        elif base_coeff.factor == "exchange_rate":
            # 수출 비중
            user_export = user_char.get("export_ratio", 0)
            sector_avg_export = sector_pattern.avg_export_ratio / 100
            
            if user_export > sector_avg_export * 1.2:  # 업종 평균보다 20% 높음
                adjustment = 0.15
                personal_coeff = min(personal_coeff + adjustment, 1.0) 
                adjustment_reason.append(f"수출비중 {user_export:.1%}로 업종 평균 대비 높음")
        
        return {
            "base_coefficient": base_coeff.coefficient,
            "personalized_coefficient": personal_coeff,
            "confidence": base_coeff.confidence,
            "adjustment_reason": adjustment_reason,
            "rationale": base_coeff.rationale
        }
    
    def _calculate_overall_risk(self, sensitivities: Dict, user_char: Dict) -> float:
        """종합 리스크 점수 계산 (0~1)"""
        risk_scores = []
        
        for factor, sensitivity in sensitivities.items():
            coeff = abs(sensitivity["personalized_coefficient"])  # 절대값으로 리스크 크기
            confidence = sensitivity["confidence"]
            weighted_risk = coeff * confidence
            risk_scores.append(weighted_risk)
        
        return min(np.mean(risk_scores), 1.0)
    
    def _estimate_concrete_impacts(self, sensitivities: Dict, user_char: Dict) -> Dict:
        """구체적 영향 추정"""
        impacts = {}
        
        # 금리 영향
        if "interest_rate" in sensitivities:
            interest_sens = sensitivities["interest_rate"]
            if user_char.get("has_variable_debt", False):
                debt_amount = user_char.get("variable_debt", 0)
                # 금리 0.5%p 상승 시 연간 추가 이자부담
                annual_impact = debt_amount * 0.005  # 0.5%
                monthly_impact = annual_impact / 12
                
                impacts["interest_rate_0.5pp_increase"] = {
                    "monthly_impact": int(monthly_impact),
                    "annual_impact": int(annual_impact),
                    "description": f"금리 0.5%p 상승 시 월 {monthly_impact/10000:.0f}만원 추가 부담"
                }
        
        # 환율 영향 (수출기업의 경우)
        if "exchange_rate" in sensitivities and user_char.get("export_ratio", 0) > 0:
            export_ratio = user_char.get("export_ratio", 0)
            revenue = user_char.get("revenue", 0)
            export_revenue = revenue * export_ratio
            
            # 원/달러 10원 상승 시 수출 매출 증가 (3% 가정)
            forex_benefit = export_revenue * 0.03
            monthly_benefit = forex_benefit / 12
            
            impacts["usd_krw_10won_increase"] = {
                "monthly_benefit": int(monthly_benefit),
                "annual_benefit": int(forex_benefit), 
                "description": f"원/달러 10원 상승 시 월 {monthly_benefit/10000:.0f}만원 수익 증가"
            }
        
        return impacts
    
    def _generate_recommendations(self, overall_risk: float, sensitivities: Dict) -> List[str]:
        """리스크 기반 추천사항 생성"""
        recommendations = []
        
        if overall_risk > 0.7:
            recommendations.append("️  종합 리스크가 높음 - 금융 리스크 관리 전략 수립 필요")
        
        # 금리 리스크 높은 경우
        interest_sens = sensitivities.get("interest_rate", {})
        if interest_sens.get("personalized_coefficient", 0) > 0.6:
            recommendations.append(" 변동금리 대출의 고정금리 전환 검토 권장")
            recommendations.append(" KB 중소기업 고정금리 전환대출 상품 확인")
        
        # 환율 수혜 가능한 경우
        forex_sens = sensitivities.get("exchange_rate", {})  
        if forex_sens.get("personalized_coefficient", 0) > 0.4:
            recommendations.append(" 환율 상승 수혜 예상 - 수출 확대 전략 검토")
            recommendations.append(" KB 수출금융 상품으로 운전자금 지원 활용")
        
        return recommendations

def main():
    """민감도 분석기 테스트"""
    print("=== 민감도 분석기 테스트 ===")
    
    analyzer = SensitivityAnalyzer()
    
    # 업종별 패턴 출력
    print("\n 업종별 민감도 패턴:")
    for sector_name, pattern in analyzer.sector_patterns.items():
        print(f"\n{pattern.sector_name}:")
        print(f"  - 분석 기업: {pattern.total_companies}개")
        print(f"  - 평균 변동금리 노출: {pattern.avg_variable_rate_exposure:.1%}")
        print(f"  - 평균 수출비중: {pattern.avg_export_ratio:.1f}%")
        
        for coeff in pattern.sensitivity_coefficients:
            print(f"  - {coeff.factor}: {coeff.coefficient:.3f} (신뢰도 {coeff.confidence:.2f})")
    
    # 사용자 기업 테스트
    print("\n 사용자 기업 민감도 분석 테스트:")
    
    test_user = {
        "company_name": "대한정밀",
        "industry_sector": "자동차부품",
        "revenue_text": "80억원",
        "debt_text": "변동금리 대출 10억원", 
        "export_ratio_text": "30%"
    }
    
    result = analyzer.calculate_user_company_sensitivity(test_user)
    
    print(f"매칭 업종: {result['matched_sector']}")
    print(f"종합 리스크 점수: {result['overall_risk_score']:.2f}")
    
    print("\n 맞춤형 추천:")
    for rec in result['recommendations']:
        print(f"  {rec}")
    
    print("\n 예상 영향:")
    for impact_type, impact_data in result['impact_estimates'].items():
        print(f"  {impact_data['description']}")

if __name__ == "__main__":
    main()