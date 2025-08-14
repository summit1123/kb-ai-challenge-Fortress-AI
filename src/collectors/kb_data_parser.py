import re
import json
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class KBLoanProduct:
    product_name: str
    provider: str = "KB국민은행"
    product_type: str = ""  # 운전자금/시설자금/특수
    target_customer: str = ""
    credit_grade_min: str = ""
    loan_limit: str = ""
    loan_period: str = ""
    interest_rate: str = ""
    collateral: str = ""
    guarantee: str = ""
    special_conditions: str = ""
    description: str = ""
    source: str = "KB국민은행 기업금융 실제 데이터"

class KBDataParser:
    def __init__(self, file_path: str = "data/raw/financial_products_manual.md"):
        self.file_path = file_path
        self.products = []
    
    def parse_all_products(self) -> List[KBLoanProduct]:
        """전체 파일에서 모든 상품 정보 추출"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 상품별로 텍스트 분할
            product_sections = self._split_by_products(content)
            
            for section in product_sections:
                product = self._parse_product(section)
                if product:
                    self.products.append(product)
            
            print(f"총 {len(self.products)}개 KB 상품 파싱 완료")
            return self.products
            
        except Exception as e:
            print(f"파일 파싱 오류: {e}")
            return []
    
    def _split_by_products(self, content: str) -> List[str]:
        """상품명을 기준으로 텍스트 분할"""
        # 실제 KB 상품명 패턴 (더 정확하게)
        product_names = [
            "지방자치단체협약중소기업자금대출",
            "KB동반성장 팩토링",
            "KB 수출기업 우대대출", 
            "KB 소상공인 119plus",
            "착한기업의 지속가능경영을 지원하는 착한대출",
            "KB Green Wave_ESG 우수기업대출",
            "KB 우수기술기업 TCB신용대출",
            "KB 모아드림론",
            "KB 태양광발전사업자우대대출",
            "KB 동산ㆍ채권담보대출",
            "KB커머셜모기지론",
            "상업어음할인",
            "KB 플러스론",
            "KB구매론",
            "KB 동반성장협약 상생대출",
            "KB 사회적경제기업 우대대출",
            "KB 미래성장기업 우대대출",
            "KB 유망분야 성장기업 우대대출",
            "KB 특화산업단지 입주기업대출",
            "정책자금대출",
            "KB 지식재산(IP) 협약보증부대출"
        ]
        
        sections = []
        
        # 각 상품명으로 텍스트 분할
        for product_name in product_names:
            # 상품명이 포함된 위치 찾기
            start_idx = content.find(product_name)
            if start_idx == -1:
                continue
            
            # 해당 상품 섹션의 끝 찾기 (다음 상품명까지)
            end_idx = len(content)
            for other_name in product_names:
                if other_name != product_name:
                    other_idx = content.find(other_name, start_idx + len(product_name))
                    if other_idx != -1 and other_idx < end_idx:
                        end_idx = other_idx
            
            # 섹션 추출
            section = content[start_idx:end_idx].strip()
            if len(section) > 100:  # 충분한 길이의 섹션만
                sections.append(section)
        
        return sections
    
    def _parse_product(self, section: str) -> Optional[KBLoanProduct]:
        """개별 상품 섹션에서 정보 추출"""
        if len(section) < 50:  # 너무 짧은 섹션은 제외
            return None
            
        lines = section.split('\n')
        product_name = lines[0].strip()
        
        # 기본 정보 추출
        data = {
            'product_name': product_name,
            'target_customer': self._extract_target_customer(section),
            'credit_grade_min': self._extract_credit_grade(section),
            'loan_limit': self._extract_loan_limit(section),
            'loan_period': self._extract_loan_period(section),
            'interest_rate': self._extract_interest_rate(section),
            'collateral': self._extract_collateral(section),
            'special_conditions': self._extract_special_conditions(section),
            'description': section[:300]  # 처음 300자를 설명으로
        }
        
        # 상품 유형 분류
        data['product_type'] = self._classify_product_type(product_name, section)
        
        return KBLoanProduct(**data)
    
    def _extract_target_customer(self, text: str) -> str:
        """대상고객 추출"""
        patterns = [
            r"가입대상[:\s]*(.*?)(?:\n|※)",
            r"대출신청자격[:\s]*(.*?)(?:\n|※)",
            r"개인사업자[&\s]*법인",
            r"중소기업", r"소상공인", r"수출기업"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0)
        return "중소기업"
    
    def _extract_credit_grade(self, text: str) -> str:
        """신용등급 추출"""
        pattern = r"신용등급[:\s]*([A-Z]+[+-]?[^가-힣]*?)(?:\n|\s|이상)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_loan_limit(self, text: str) -> str:
        """대출한도 추출"""
        patterns = [
            r"대출금액[:\s]*(.*?)(?=대출기간|원리금|목록|$)",
            r"한도[:\s]*(.*?)(?=대출기간|원리금|목록|$)",
            r"최대[:\s]*(\d+억원?)",
            r"(\d+억원?\s*이내)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                limit_text = match.group(1).strip()
                if limit_text and len(limit_text) < 200:
                    return limit_text
        return ""
    
    def _extract_loan_period(self, text: str) -> str:
        """대출기간 추출"""
        pattern = r"대출기간 및 상환 방법[:\s]*(.*?)(?=대출신청시기|금리|목록|$)"
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if match:
            period_text = match.group(1).strip()
            if len(period_text) < 300:
                return period_text
        return ""
    
    def _extract_interest_rate(self, text: str) -> str:
        """금리 정보 추출"""
        patterns = [
            r"기준금리[:\s]*연\s*(\d+\.\d+%)",
            r"적용금리[:\s]*연\s*([\d.~%\s]+)",
            r"대출금리[:\s]*(.*?)(?=이자계산|원리금|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                rate_info = match.group(1).strip()
                if rate_info and len(rate_info) < 100:
                    return rate_info
        return ""
    
    def _extract_collateral(self, text: str) -> str:
        """담보 정보 추출"""
        if "무담보" in text or "신용대출" in text:
            return "무담보"
        elif "부동산" in text or "근저당" in text:
            return "부동산담보"
        elif "동산" in text or "재고" in text:
            return "동산담보"
        elif "보증서" in text:
            return "보증서담보"
        return ""
    
    def _extract_special_conditions(self, text: str) -> str:
        """특별 조건 추출"""
        conditions = []
        
        condition_keywords = [
            "수출실적", "ESG", "기술력", "태양광", "협약", "상생", 
            "사회적경제", "지식재산", "IP", "특화산업단지"
        ]
        
        for keyword in condition_keywords:
            if keyword in text:
                conditions.append(keyword)
        
        return ", ".join(conditions)
    
    def _classify_product_type(self, name: str, content: str) -> str:
        """상품 유형 분류"""
        if any(word in name for word in ["시설", "모기지", "커머셜"]):
            return "시설자금"
        elif any(word in name for word in ["팩토링", "할인", "IP"]):
            return "특수금융"
        elif any(word in content for word in ["운전자금", "운영자금"]):
            return "운전자금"
        else:
            return "기타"
    
    def save_to_files(self):
        """CSV와 JSON으로 저장"""
        if not self.products:
            print("저장할 상품 데이터가 없습니다.")
            return
        
        # CSV 저장
        df = pd.DataFrame([asdict(product) for product in self.products])
        csv_path = "data/raw/kb_actual_products.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"CSV 저장: {csv_path}")
        
        # JSON 저장
        json_path = "data/raw/kb_actual_products.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(product) for product in self.products], 
                     f, ensure_ascii=False, indent=2)
        print(f"JSON 저장: {json_path}")
    
    def print_summary(self):
        """파싱 결과 요약"""
        if not self.products:
            return
            
        print(f"\n=== KB 실제 상품 데이터 파싱 결과 ===")
        print(f"총 상품 수: {len(self.products)}")
        
        # 상품 유형별 분류
        type_count = {}
        for product in self.products:
            ptype = product.product_type
            type_count[ptype] = type_count.get(ptype, 0) + 1
        
        print(f"\n=== 상품 유형별 분포 ===")
        for ptype, count in type_count.items():
            print(f"{ptype}: {count}개")
        
        print(f"\n=== 상품 목록 (처음 10개) ===")
        for i, product in enumerate(self.products[:10], 1):
            print(f"{i}. {product.product_name}")
            print(f"   유형: {product.product_type}")
            print(f"   대상: {product.target_customer}")
            print(f"   한도: {product.loan_limit[:50]}...")
            print()

def main():
    print("KB 국민은행 실제 상품 데이터 파서")
    print("=" * 50)
    
    parser = KBDataParser()
    products = parser.parse_all_products()
    
    if products:
        parser.print_summary()
        parser.save_to_files()
        print("\n파싱 완료! 이제 실제 KB 상품 데이터를 활용할 수 있습니다.")
    else:
        print("파싱된 상품이 없습니다.")

if __name__ == "__main__":
    main()