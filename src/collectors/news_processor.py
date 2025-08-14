"""
뉴스 데이터 처리기
BigKinds 뉴스 엑셀 파일들을 분석하여 LLM이 처리할 수 있는 형태로 가공
"""

import pandas as pd
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import re

class NewsProcessor:
    """뉴스 데이터 처리 클래스"""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        
        # 제조업 관련 키워드
        self.manufacturing_keywords = [
            "제조업", "공장", "생산", "수출", "자동차", "부품", "중소기업", 
            "금리", "환율", "원자재", "정책자금", "대출", "금융지원"
        ]
        
        # 금융 관련 키워드  
        self.financial_keywords = [
            "기준금리", "한국은행", "금리인상", "금리인하", "원달러환율", 
            "정책자금", "중소기업대출", "금융지원", "보증", "신용보증"
        ]
    
    def load_all_news_files(self) -> List[Dict[str, Any]]:
        """모든 뉴스 엑셀 파일 로드"""
        news_files = [
            "NewsResult_20250513-20250812.xlsx",
            "NewsResult_20250513-20250813 (2).xlsx", 
            "NewsResult_20250513-20250813 (3).xlsx",
            "NewsResult_20250513-20250813 (4).xlsx",
            "NewsResult_20250513-20250813 (6).xlsx",
            "NewsResult_20250513-202508131.xlsx"
        ]
        
        all_news = []
        
        for filename in news_files:
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    df = pd.read_excel(filepath)
                    
                    for _, row in df.iterrows():
                        news_item = {
                            "news_id": row.get("뉴스 식별자", ""),
                            "date": str(row.get("일자", "")),
                            "title": str(row.get("제목", "")),
                            "media": str(row.get("언론사", "")),
                            "author": str(row.get("기고자", "")),
                            "content": str(row.get("본문", "")),
                            "keywords": str(row.get("키워드", "")),
                            "url": str(row.get("URL", "")),
                            "source_file": filename
                        }
                        all_news.append(news_item)
                        
                    print(f" 로드 완료: {filename} ({len(df)}개 뉴스)")
                    
                except Exception as e:
                    print(f" 파일 로드 오류 {filename}: {e}")
        
        print(f"\n 전체 뉴스 수집: {len(all_news)}개")
        return all_news
    
    def filter_relevant_news(self, news_list: List[Dict], max_per_category: int = 20) -> Dict[str, List[Dict]]:
        """제조업/금융 관련 뉴스 필터링 및 카테고리별 분류"""
        
        categorized_news = {
            "manufacturing": [],
            "financial": [],
            "policy": [],
            "macro_economic": []
        }
        
        for news in news_list:
            title = news["title"].lower()
            content = news["content"].lower()
            keywords = news["keywords"].lower()
            
            combined_text = f"{title} {content} {keywords}"
            
            # 제조업 관련 뉴스
            if any(keyword in combined_text for keyword in ["제조업", "공장", "생산", "자동차", "부품"]):
                if len(categorized_news["manufacturing"]) < max_per_category:
                    news["category"] = "manufacturing"
                    categorized_news["manufacturing"].append(news)
            
            # 금융 관련 뉴스
            elif any(keyword in combined_text for keyword in ["금리", "환율", "한국은행", "대출"]):
                if len(categorized_news["financial"]) < max_per_category:
                    news["category"] = "financial"
                    categorized_news["financial"].append(news)
            
            # 정책 관련 뉴스
            elif any(keyword in combined_text for keyword in ["정책자금", "중소기업지원", "금융지원", "보증"]):
                if len(categorized_news["policy"]) < max_per_category:
                    news["category"] = "policy"
                    categorized_news["policy"].append(news)
            
            # 거시경제 관련 뉴스
            elif any(keyword in combined_text for keyword in ["경기전망", "bsi", "경제상황", "수출실적"]):
                if len(categorized_news["macro_economic"]) < max_per_category:
                    news["category"] = "macro_economic"
                    categorized_news["macro_economic"].append(news)
        
        return categorized_news
    
    def extract_financial_entities(self, news_item: Dict) -> Dict[str, Any]:
        """뉴스에서 금융 엔터티 추출"""
        title = news_item["title"]
        content = news_item["content"]
        combined_text = f"{title} {content}"
        
        entities = {
            "companies": [],
            "financial_indicators": [],
            "policies": [],
            "amounts": []
        }
        
        # 기업명 추출 (간단한 패턴 매칭)
        company_patterns = [
            r"([가-힣]{2,}(?:(?:주식회사|㈜|기업|그룹|산업|정밀|제조)))",
            r"(KB국민은행|신한은행|우리은행)",
            r"(삼성|현대|LG|포스코|SK)"
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, combined_text)
            entities["companies"].extend(matches)
        
        # 금융지표 추출
        indicator_patterns = [
            r"(기준금리|금리|환율|원달러)",
            r"(\d+\.?\d*%)",
            r"(원/달러|USD/KRW)"
        ]
        
        for pattern in indicator_patterns:
            matches = re.findall(pattern, combined_text)
            entities["financial_indicators"].extend(matches)
        
        # 금액 추출
        amount_patterns = [
            r"(\d+(?:조|억|만)원?)",
            r"(\d+\.?\d*%)"
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, combined_text)
            entities["amounts"].extend(matches)
        
        return entities
    
    def process_and_save(self, output_dir: str = "data/processed") -> Dict[str, str]:
        """뉴스 데이터 처리 및 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 모든 뉴스 로드
        all_news = self.load_all_news_files()
        
        # 2. 관련 뉴스 필터링
        categorized_news = self.filter_relevant_news(all_news, max_per_category=20)
        
        # 3. 카테고리별 저장
        saved_files = {}
        
        for category, news_list in categorized_news.items():
            if news_list:
                # 엔터티 추출 추가
                for news in news_list:
                    news["extracted_entities"] = self.extract_financial_entities(news)
                
                # JSON 파일로 저장
                filename = f"news_{category}_{datetime.now().strftime('%Y%m%d')}.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(news_list, f, ensure_ascii=False, indent=2)
                
                saved_files[category] = filepath
                print(f" {category}: {len(news_list)}개 뉴스 저장 → {filepath}")
        
        # 4. 전체 요약 정보 저장
        summary = {
            "processing_date": datetime.now().isoformat(),
            "total_news_processed": len(all_news),
            "categorized_counts": {cat: len(news_list) for cat, news_list in categorized_news.items()},
            "saved_files": saved_files
        }
        
        summary_file = os.path.join(output_dir, f"news_processing_summary_{datetime.now().strftime('%Y%m%d')}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n 처리 요약:")
        print(f"전체 뉴스: {summary['total_news_processed']}개")
        for category, count in summary['categorized_counts'].items():
            print(f"- {category}: {count}개")
        
        return saved_files

def main():
    """뉴스 처리기 실행"""
    print("=== 뉴스 데이터 처리 시작 ===")
    
    processor = NewsProcessor()
    saved_files = processor.process_and_save()
    
    print(f"\n 뉴스 데이터 처리 완료!")
    print("저장된 파일들:")
    for category, filepath in saved_files.items():
        print(f"- {category}: {filepath}")

if __name__ == "__main__":
    main()