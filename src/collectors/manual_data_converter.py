import re
import json
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass 
class FinancialProduct:
    productName: str
    provider: str = "KB국민은행"
    category: str = ""
    targetCustomer: str = ""
    maxAmount: str = ""
    interestRate: str = ""
    conditions: str = ""
    collateralRequired: bool = False
    guaranteeAvailable: bool = False
    description: str = ""
    source: str = "KB국민은행 기업금융"

class ManualDataConverter:
    def __init__(self, markdown_file: str = "data/raw/financial_products_manual.md"):
        self.markdown_file = markdown_file
        self.products = []
    
    def parse_markdown(self):
        """마크다운 파일에서 상품 정보 추출"""
        try:
            with open(self.markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ### 상품명 패턴으로 각 상품 구분
            product_sections = re.split(r'### 상품명:', content)[1:]  # 첫 번째는 헤더이므로 제외
            
            for section in product_sections:
                product = self._parse_product_section(section)
                if product:
                    self.products.append(product)
                    
            print(f"총 {len(self.products)}개 상품 파싱 완료")
            return self.products
            
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {self.markdown_file}")
            return []
    
    def _parse_product_section(self, section: str) -> FinancialProduct:
        """개별 상품 섹션 파싱"""
        lines = section.strip().split('\n')
        if not lines:
            return None
            
        # 상품명 (첫 번째 줄)
        product_name = lines[0].strip()
        
        # 각 필드 추출
        data = {
            'productName': product_name,
            'maxAmount': self._extract_field(section, r'대출한도[:\s]*(.+?)(?:\n|$)'),
            'interestRate': self._extract_field(section, r'금리[:\s]*(.+?)(?:\n|$)'),
            'targetCustomer': self._extract_field(section, r'대상고객[:\s]*(.+?)(?:\n|$)'),
            'conditions': self._extract_field(section, r'자격요건[:\s]*(.+?)(?:\n|$)'),
            'category': self._extract_field(section, r'용도[:\s]*(.+?)(?:\n|$)'),
            'description': self._extract_field(section, r'상환방법[:\s]*(.+?)(?:\n|$)'),
        }
        
        # 담보 여부 확인
        collateral_text = self._extract_field(section, r'담보[:\s]*(.+?)(?:\n|$)')
        data['collateralRequired'] = '무담보' not in collateral_text if collateral_text else False
        
        # 보증 가능 여부 확인  
        guarantee_text = self._extract_field(section, r'보증[:\s]*(.+?)(?:\n|$)')
        data['guaranteeAvailable'] = '가능' in guarantee_text if guarantee_text else False
        
        return FinancialProduct(**data)
    
    def _extract_field(self, text: str, pattern: str) -> str:
        """정규식으로 필드 값 추출"""
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip().replace('**', '').replace('*', '')
        return ""
    
    def save_to_csv(self, filename: str = "kb_products_manual.csv"):
        """CSV로 저장"""
        if not self.products:
            print("저장할 상품 데이터가 없습니다.")
            return
            
        df = pd.DataFrame([asdict(product) for product in self.products])
        filepath = f"data/raw/{filename}"
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"수동 입력 상품 데이터 저장: {filepath}")
        return filepath
    
    def save_to_json(self, filename: str = "kb_products_manual.json"):
        """JSON으로 저장"""
        if not self.products:
            print("저장할 상품 데이터가 없습니다.")
            return
            
        data = [asdict(product) for product in self.products]
        filepath = f"data/raw/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON 데이터 저장: {filepath}")
        return filepath
    
    def print_summary(self):
        """데이터 요약 출력"""
        if not self.products:
            print("파싱된 상품이 없습니다.")
            return
            
        print(f"\n=== 수동 입력 상품 데이터 요약 ===")
        print(f"총 상품 수: {len(self.products)}")
        
        print(f"\n=== 상품 목록 ===")
        for i, product in enumerate(self.products, 1):
            print(f"{i}. {product.productName}")
            print(f"   대상: {product.targetCustomer}, 한도: {product.maxAmount}")
            print(f"   금리: {product.interestRate}")
            print()

def main():
    print("수동 입력 상품 데이터 변환기")
    print("=" * 40)
    
    converter = ManualDataConverter()
    products = converter.parse_markdown()
    
    if products:
        converter.print_summary()
        converter.save_to_csv()
        converter.save_to_json()
    else:
        print("마크다운 파일에 상품 정보를 입력한 후 다시 실행해주세요.")
        print("파일 위치: data/raw/financial_products_manual.md")

if __name__ == "__main__":
    main()