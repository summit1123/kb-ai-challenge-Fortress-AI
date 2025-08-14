from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid
from datetime import datetime

class NodeType(Enum):
    REFERENCE_COMPANY = "ReferenceCompany"  # 분석용 벤치마킹 기업
    USER_COMPANY = "UserCompany"            # 사용자 입력 기업
    POLICY = "Policy"
    MACRO_INDICATOR = "MacroIndicator"
    NEWS_ARTICLE = "NewsArticle"
    KB_PRODUCT = "KB_Product"

class RelationshipType(Enum):
    IS_EXPOSED_TO = "IS_EXPOSED_TO"
    HAS_IMPACT_ON = "HAS_IMPACT_ON"
    COMPETES_WITH = "COMPETES_WITH"
    IS_ELIGIBLE_FOR = "IS_ELIGIBLE_FOR"
    SIMILAR_TO = "SIMILAR_TO"  # UserCompany → ReferenceCompany 매칭

@dataclass
class BaseNode:
    """기본 노드 클래스"""
    node_id: str
    node_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class ReferenceCompany:
    """벤치마킹용 기업 노드 (분석 참조용)"""
    node_id: str
    node_type: str
    created_at: datetime
    company_name: str
    industry_code: str  # KSIC 코드
    location: str
    revenue_range: str
    updated_at: Optional[datetime] = None
    debt_info: Optional[str] = None
    employee_count: Optional[int] = None
    establishment_year: Optional[int] = None
    business_type: str = "제조업"
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"company_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.REFERENCE_COMPANY.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "companyName": self.company_name,
            "industryCode": self.industry_code,
            "location": self.location,
            "revenueRange": self.revenue_range,
            "debtInfo": self.debt_info,
            "employeeCount": self.employee_count,
            "establishmentYear": self.establishment_year,
            "businessType": self.business_type
        })
        return base_dict

@dataclass
class UserCompany:
    """사용자 입력 기업 노드 (실시간 생성)"""
    node_id: str
    node_type: str
    created_at: datetime
    company_name: str
    industry_sector: str  # "자동차부품", "철강", "화학" 등
    revenue_text: str     # "매출 80억원"
    debt_text: str        # "변동금리 대출 10억원"  
    updated_at: Optional[datetime] = None
    location: Optional[str] = None
    employee_count_text: Optional[str] = None
    export_ratio_text: Optional[str] = None
    business_description: Optional[str] = None
    user_input_raw: Optional[str] = None  # 원본 텍스트 저장
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"user_company_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.USER_COMPANY.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "companyName": self.company_name,
            "industrySector": self.industry_sector,
            "revenueText": self.revenue_text,
            "debtText": self.debt_text,
            "location": self.location,
            "employeeCountText": self.employee_count_text,
            "exportRatioText": self.export_ratio_text,
            "businessDescription": self.business_description,
            "userInputRaw": self.user_input_raw
        })
        return base_dict

@dataclass
class Policy:
    """정부/지자체 정책 노드"""
    node_id: str
    node_type: str
    created_at: datetime
    policy_name: str
    issuing_org: str
    support_field: str
    eligibility_text: str
    updated_at: Optional[datetime] = None
    support_amount: Optional[str] = None
    application_period: Optional[str] = None
    policy_type: str = "지원정책"
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"policy_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.POLICY.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "policyName": self.policy_name,
            "issuingOrg": self.issuing_org,
            "supportField": self.support_field,
            "eligibilityText": self.eligibility_text,
            "supportAmount": self.support_amount,
            "applicationPeriod": self.application_period,
            "policyType": self.policy_type
        })
        return base_dict

@dataclass
class MacroIndicator:
    """거시경제지표 노드"""
    node_id: str
    node_type: str
    created_at: datetime
    indicator_name: str
    value: float
    updated_at: Optional[datetime] = None
    change_rate: Optional[float] = None
    date: Optional[datetime] = None
    unit: str = "%"
    category: str = "경제지표"
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"indicator_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.MACRO_INDICATOR.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "indicatorName": self.indicator_name,
            "value": self.value,
            "changeRate": self.change_rate,
            "date": self.date.isoformat() if self.date else None,
            "unit": self.unit,
            "category": self.category
        })
        return base_dict

@dataclass
class NewsArticle:
    """뉴스 기사 노드"""
    node_id: str
    node_type: str
    created_at: datetime
    title: str
    publisher: str
    publish_date: datetime
    article_text: str
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    category: str = "경제"
    sentiment: Optional[str] = None
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"news_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.NEWS_ARTICLE.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "title": self.title,
            "publisher": self.publisher,
            "publishDate": self.publish_date.isoformat(),
            "articleText": self.article_text,
            "summary": self.summary,
            "category": self.category,
            "sentiment": self.sentiment
        })
        return base_dict

@dataclass
class KB_Product:
    """KB 금융상품 노드"""
    node_id: str
    node_type: str
    created_at: datetime
    product_name: str
    product_type: str
    target_customer: str
    loan_limit: str
    interest_rate: str
    collateral: str
    updated_at: Optional[datetime] = None
    credit_grade_min: Optional[str] = None
    loan_period: Optional[str] = None
    special_conditions: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"kb_product_{uuid.uuid4().hex[:8]}"
        self.node_type = NodeType.KB_PRODUCT.value
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        base_dict.update({
            "productName": self.product_name,
            "productType": self.product_type,
            "targetCustomer": self.target_customer,
            "loanLimit": self.loan_limit,
            "interestRate": self.interest_rate,
            "collateral": self.collateral,
            "creditGradeMin": self.credit_grade_min,
            "loanPeriod": self.loan_period,
            "specialConditions": self.special_conditions,
            "description": self.description
        })
        return base_dict

@dataclass
class Relationship:
    """관계 클래스"""
    from_node_id: str
    to_node_id: str
    relationship_type: str
    properties: Dict[str, Any]
    created_at: datetime
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fromNodeId": self.from_node_id,
            "toNodeId": self.to_node_id,
            "relationshipType": self.relationship_type,
            "createdAt": self.created_at.isoformat(),
            **self.properties
        }

class GraphSchema:
    """그래프 스키마 관리"""
    
    @staticmethod
    def get_node_types() -> List[str]:
        return [node_type.value for node_type in NodeType]
    
    @staticmethod
    def get_relationship_types() -> List[str]:
        return [rel_type.value for rel_type in RelationshipType]
    
    @staticmethod
    def get_schema_definition() -> Dict[str, Any]:
        """전체 스키마 정의 반환"""
        return {
            "nodes": {
                "Company": {
                    "required_fields": ["company_name", "industry_code", "location", "revenue_range"],
                    "optional_fields": ["debt_info", "employee_count", "establishment_year", "business_type"],
                    "description": "중소기업 정보"
                },
                "Policy": {
                    "required_fields": ["policy_name", "issuing_org", "support_field", "eligibility_text"],
                    "optional_fields": ["support_amount", "application_period", "policy_type"],
                    "description": "정부/지자체 지원정책"
                },
                "MacroIndicator": {
                    "required_fields": ["indicator_name", "value"],
                    "optional_fields": ["change_rate", "date", "unit", "category"],
                    "description": "거시경제지표"
                },
                "NewsArticle": {
                    "required_fields": ["title", "publisher", "publish_date", "article_text"],
                    "optional_fields": ["summary", "category", "sentiment"],
                    "description": "뉴스 기사"
                },
                "KB_Product": {
                    "required_fields": ["product_name", "product_type", "target_customer", "loan_limit", "interest_rate", "collateral"],
                    "optional_fields": ["credit_grade_min", "loan_period", "special_conditions", "description"],
                    "description": "KB 금융상품"
                }
            },
            "relationships": {
                "IS_EXPOSED_TO": {
                    "from": ["Company"],
                    "to": ["MacroIndicator"],
                    "properties": ["exposure_level", "rationale"],
                    "description": "기업이 거시경제지표에 노출되는 정도"
                },
                "HAS_IMPACT_ON": {
                    "from": ["NewsArticle", "MacroIndicator"],
                    "to": ["Company", "MacroIndicator"],
                    "properties": ["impact_score", "rationale", "sentiment"],
                    "description": "뉴스나 지표가 기업에 미치는 영향"
                },
                "COMPETES_WITH": {
                    "from": ["Company"],
                    "to": ["Company"],
                    "properties": ["similarity_score", "competition_type"],
                    "description": "기업간 경쟁관계"
                },
                "IS_ELIGIBLE_FOR": {
                    "from": ["Company"],
                    "to": ["Policy", "KB_Product"],
                    "properties": ["eligibility_score", "matching_conditions", "recommendation_reason"],
                    "description": "기업이 정책이나 상품에 대한 자격"
                }
            }
        }

def create_sample_nodes():
    """샘플 노드 생성"""
    # 샘플 기업
    company = Company(
        node_id="company_sample_01",
        node_type=NodeType.COMPANY.value,
        created_at=datetime.now(),
        company_name="대한정밀",
        industry_code="C28",
        location="경기도 안산시",
        revenue_range="50억~100억",
        debt_info="총 부채 15억원 (변동금리 대출 10억원)",
        employee_count=45,
        establishment_year=2010,
        business_type="자동차부품 제조업"
    )
    
    # 샘플 거시경제지표
    base_rate = MacroIndicator(
        node_id="indicator_base_rate",
        node_type=NodeType.MACRO_INDICATOR.value,
        created_at=datetime.now(),
        indicator_name="한국은행 기준금리",
        value=3.5,
        change_rate=0.5,
        date=datetime.now(),
        unit="%",
        category="금리"
    )
    
    # 샘플 KB 상품
    kb_product = KB_Product(
        node_id="kb_product_01",
        node_type=NodeType.KB_PRODUCT.value,
        created_at=datetime.now(),
        product_name="KB 중소기업 우대대출",
        product_type="운전자금",
        target_customer="중소기업",
        loan_limit="최대 30억원",
        interest_rate="연 4.5~8.5%",
        collateral="무담보",
        credit_grade_min="BB+",
        special_conditions="기술력, 수출실적"
    )
    
    return [company, base_rate, kb_product]

if __name__ == "__main__":
    # 스키마 정의 출력
    schema = GraphSchema.get_schema_definition()
    print("=== KB Fortress AI 그래프 스키마 ===")
    
    print("\n노드 타입:")
    for node_type, definition in schema["nodes"].items():
        print(f"  {node_type}: {definition['description']}")
    
    print("\n관계 타입:")
    for rel_type, definition in schema["relationships"].items():
        print(f"  {rel_type}: {definition['description']}")
    
    # 샘플 노드 생성 테스트
    print("\n=== 샘플 노드 생성 테스트 ===")
    sample_nodes = create_sample_nodes()
    for node in sample_nodes:
        print(f"{node.node_type}: {node.to_dict()}")