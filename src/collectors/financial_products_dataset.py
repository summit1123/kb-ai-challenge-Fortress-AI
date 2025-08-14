import json
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass, asdict
import os

@dataclass
class FinancialProduct:
    productName: str
    provider: str
    category: str
    targetCustomer: str
    maxAmount: str
    interestRate: str
    conditions: str
    collateralRequired: bool
    guaranteeAvailable: bool
    description: str = ""
    source: str = ""

class FinancialProductsDataset:
    def __init__(self):
        self.products = []
        self._initialize_kb_products()
        self._initialize_policy_finance_products()
        self._initialize_guarantee_products()
    
    def _initialize_kb_products(self):
        """KB국민은행 중소기업 대출상품 (공개 정보 기반)"""
        kb_products = [
            FinancialProduct(
                productName="KB중소기업성장대출",
                provider="KB국민은행",
                category="운영자금",
                targetCustomer="중소기업",
                maxAmount="30억원",
                interestRate="연 4.5~8.5%",
                conditions="업력 3년 이상, 매출 50억 이하, 신용등급 BB이상",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="중소기업의 운영자금 지원을 위한 신용대출상품",
                source="KB국민은행 기업금융"
            ),
            FinancialProduct(
                productName="KB셀러존대출",
                provider="KB국민은행",
                category="온라인판매자금",
                targetCustomer="개인사업자",
                maxAmount="5억원",
                interestRate="연 5.0~9.0%",
                conditions="온라인 판매실적 6개월 이상, 월 매출 1천만원 이상",
                collateralRequired=False,
                guaranteeAvailable=False,
                description="온라인 쇼핑몰 운영자를 위한 매출연동 대출",
                source="KB국민은행 기업금융"
            ),
            FinancialProduct(
                productName="KB상생플러스대출",
                provider="KB국민은행",
                category="협력업체자금",
                targetCustomer="중소기업",
                maxAmount="10억원",
                interestRate="연 3.5~6.5%",
                conditions="대기업 협력업체, 납품계약서 확인 필요",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="대기업 협력업체를 위한 상생협력 대출",
                source="KB국민은행 기업금융"
            ),
            FinancialProduct(
                productName="KB기업시설자금대출",
                provider="KB국민은행",
                category="시설자금",
                targetCustomer="중소기업",
                maxAmount="50억원",
                interestRate="연 4.0~7.5%",
                conditions="사업계획서, 시설투자계획서 제출 필요",
                collateralRequired=True,
                guaranteeAvailable=True,
                description="기업의 시설투자 및 설비확충을 위한 대출",
                source="KB국민은행 기업금융"
            ),
            FinancialProduct(
                productName="KB개인사업자신용대출",
                provider="KB국민은행",
                category="운영자금",
                targetCustomer="개인사업자",
                maxAmount="3억원",
                interestRate="연 5.5~9.5%",
                conditions="사업자등록 6개월 이상, 신용등급 5등급 이내",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="개인사업자를 위한 간편 신용대출",
                source="KB국민은행 기업금융"
            )
        ]
        self.products.extend(kb_products)
    
    def _initialize_policy_finance_products(self):
        """정책금융기관 대출상품"""
        policy_products = [
            FinancialProduct(
                productName="IBK중소기업성장지원대출",
                provider="기업은행",
                category="정책자금",
                targetCustomer="중소기업",
                maxAmount="30억원",
                interestRate="연 2.5~4.5%",
                conditions="중소기업 인증, 성장가능성 평가",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="중소기업 성장을 위한 정책금융 지원",
                source="기업은행 정책금융"
            ),
            FinancialProduct(
                productName="산업은행성장금융",
                provider="산업은행",
                category="성장자금",
                targetCustomer="중견기업",
                maxAmount="100억원",
                interestRate="연 3.0~5.0%",
                conditions="기술력 우수기업, 성장단계 기업",
                collateralRequired=True,
                guaranteeAvailable=False,
                description="혁신기업 및 성장기업을 위한 장기자금 지원",
                source="산업은행"
            ),
            FinancialProduct(
                productName="신협소상공인대출",
                provider="신용협동조합",
                category="서민금융",
                targetCustomer="소상공인",
                maxAmount="1억원",
                interestRate="연 4.0~7.0%",
                conditions="조합원 가입, 소상공인 확인서",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="소상공인을 위한 서민금융 대출",
                source="신용협동조합"
            )
        ]
        self.products.extend(policy_products)
    
    def _initialize_guarantee_products(self):
        """보증기금 상품"""
        guarantee_products = [
            FinancialProduct(
                productName="신보일반보증",
                provider="신용보증기금",
                category="신용보증",
                targetCustomer="중소기업",
                maxAmount="30억원",
                interestRate="은행대출금리-보증료 0.5~2.0%",
                conditions="중소기업 해당, 보증심사 통과",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="중소기업을 위한 일반 신용보증",
                source="신용보증기금"
            ),
            FinancialProduct(
                productName="기보기술평가보증",
                provider="기술보증기금",
                category="기술보증",
                targetCustomer="기술기업",
                maxAmount="50억원",
                interestRate="은행대출금리-보증료 0.5~1.5%",
                conditions="기술력 보유기업, 기술평가 통과",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="기술력을 담보로 한 보증 지원",
                source="기술보증기금"
            ),
            FinancialProduct(
                productName="신보특별보증",
                provider="신용보증기금",
                category="특별보증",
                targetCustomer="중소기업",
                maxAmount="10억원",
                interestRate="은행대출금리-보증료 0.3~1.0%",
                conditions="정책자금 대상, 특별지원 요건 충족",
                collateralRequired=False,
                guaranteeAvailable=True,
                description="정책적 지원이 필요한 중소기업 대상 특별보증",
                source="신용보증기금"
            )
        ]
        self.products.extend(guarantee_products)
    
    def get_all_products(self) -> List[FinancialProduct]:
        return self.products
    
    def get_products_by_category(self, category: str) -> List[FinancialProduct]:
        return [p for p in self.products if p.category == category]
    
    def get_products_by_provider(self, provider: str) -> List[FinancialProduct]:
        return [p for p in self.products if p.provider == provider]
    
    def get_products_for_target(self, target_customer: str) -> List[FinancialProduct]:
        return [p for p in self.products if target_customer in p.targetCustomer]
    
    def save_to_csv(self, filename: str = "financial_products.csv"):
        df = pd.DataFrame([asdict(product) for product in self.products])
        filepath = f"data/raw/{filename}"
        os.makedirs("data/raw", exist_ok=True)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"금융상품 데이터 저장 완료: {filepath}")
        return filepath
    
    def save_to_json(self, filename: str = "financial_products.json"):
        data = [asdict(product) for product in self.products]
        filepath = f"data/raw/{filename}"
        os.makedirs("data/raw", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"금융상품 JSON 데이터 저장 완료: {filepath}")
        return filepath
    
    def print_summary(self):
        print(f"=== 금융상품 데이터셋 요약 ===")
        print(f"총 상품 수: {len(self.products)}")
        
        print(f"\n=== 제공기관별 ===")
        providers = {}
        for product in self.products:
            providers[product.provider] = providers.get(product.provider, 0) + 1
        for provider, count in providers.items():
            print(f"{provider}: {count}개")
        
        print(f"\n=== 카테고리별 ===")
        categories = {}
        for product in self.products:
            categories[product.category] = categories.get(product.category, 0) + 1
        for category, count in categories.items():
            print(f"{category}: {count}개")
        
        print(f"\n=== 샘플 상품 ===")
        for i, product in enumerate(self.products[:3]):
            print(f"{i+1}. {product.productName} ({product.provider})")
            print(f"   대상: {product.targetCustomer}, 한도: {product.maxAmount}")
            print(f"   금리: {product.interestRate}")

def main():
    print("KB Fortress AI - 금융상품 데이터셋 구성")
    print("=" * 50)
    
    dataset = FinancialProductsDataset()
    dataset.print_summary()
    
    # 데이터 저장
    csv_file = dataset.save_to_csv()
    json_file = dataset.save_to_json()
    
    print(f"\n데이터셋 구성 완료!")
    print(f"CSV 파일: {csv_file}")
    print(f"JSON 파일: {json_file}")

if __name__ == "__main__":
    main()