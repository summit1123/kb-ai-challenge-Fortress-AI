import requests
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

class ECOSAPICollector:
    """한국은행 ECOS API 데이터 수집기"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ECOS_API_KEY")
        if not self.api_key:
            raise ValueError("ECOS API 키가 필요합니다")
        
        self.base_url = "https://ecos.bok.or.kr/api"
        self.session = requests.Session()
        
        # 주요 거시경제지표 코드 정의
        self.indicators = {
            "base_rate": {
                "stat_code": "722Y001",  # 한국은행 기준금리
                "item_code1": "0101000",
                "item_code2": "",
                "item_code3": "",
                "name": "한국은행 기준금리",
                "unit": "%"
            },
            "usd_krw": {
                "stat_code": "731Y001",  # 원/달러 환율
                "item_code1": "0000001",
                "item_code2": "",
                "item_code3": "",
                "name": "원/달러 환율",
                "unit": "원"
            },
            "consumer_price": {
                "stat_code": "901Y009",  # 소비자물가지수
                "item_code1": "0",
                "item_code2": "",
                "item_code3": "",
                "name": "소비자물가지수",
                "unit": "지수"
            },
            "manufacturing_bsi": {
                "stat_code": "512Y007",  # 제조업 경기전망 BSI
                "item_code1": "AA",
                "item_code2": "",
                "item_code3": "",
                "name": "제조업 경기전망 BSI",
                "unit": "포인트"
            },
            "export_amount": {
                "stat_code": "403Y003",  # 수출액
                "item_code1": "1010000",
                "item_code2": "",
                "item_code3": "",
                "name": "수출액",
                "unit": "백만달러"
            },
            #  원자재 가격 지표 추가
            "steel_price_index": {
                "stat_code": "901Y015",  # 철강가격지수
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "철강가격지수",
                "unit": "지수"
            },
            "petrochemical_price_index": {
                "stat_code": "901Y016",  # 석유화학가격지수
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "석유화학가격지수",
                "unit": "지수"
            },
            "nonferrous_metal_price_index": {
                "stat_code": "901Y017",  # 비철금속가격지수
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "비철금속가격지수",
                "unit": "지수"
            },
            "oil_import_price": {
                "stat_code": "902Y016",  # 원유도입단가
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "원유도입단가",
                "unit": "달러/배럴"
            },
            "textile_material_price_index": {
                "stat_code": "901Y018",  # 섬유원료가격지수
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "섬유원료가격지수",
                "unit": "지수"
            },
            "agricultural_product_price_index": {
                "stat_code": "901Y014",  # 농산물가격지수
                "item_code1": "AAAA",
                "item_code2": "",
                "item_code3": "",
                "name": "농산물가격지수",
                "unit": "지수"
            }
        }
    
    def get_indicator_data(self, indicator_key: str, start_date: str, end_date: str, 
                          cycle: str = "D") -> Optional[List[Dict]]:
        """
        특정 지표 데이터 조회
        
        Args:
            indicator_key: 지표 키 (base_rate, usd_krw 등)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            cycle: 주기 (D: 일, M: 월, Q: 분기, Y: 년)
        """
        if indicator_key not in self.indicators:
            raise ValueError(f"지원하지 않는 지표입니다: {indicator_key}")
        
        indicator = self.indicators[indicator_key]
        
        url = f"{self.base_url}/StatisticSearch/{self.api_key}/json/kr/1/100000/{indicator['stat_code']}/{cycle}/{start_date}/{end_date}/{indicator['item_code1']}"
        
        if indicator['item_code2']:
            url += f"/{indicator['item_code2']}"
        if indicator['item_code3']:
            url += f"/{indicator['item_code3']}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if "StatisticSearch" not in data:
                print(f"데이터 없음: {indicator['name']}")
                return None
            
            rows = data["StatisticSearch"]["row"]
            
            processed_data = []
            for row in rows:
                try:
                    processed_data.append({
                        "indicator_name": indicator["name"],
                        "indicator_key": indicator_key,
                        "date": row["TIME"],
                        "value": float(row["DATA_VALUE"]) if row["DATA_VALUE"] != "-" else None,
                        "unit": indicator["unit"],
                        "stat_code": indicator["stat_code"],
                        "collected_at": datetime.now().isoformat()
                    })
                except (ValueError, KeyError) as e:
                    print(f"데이터 처리 오류: {row} - {e}")
                    continue
            
            print(f" {indicator['name']}: {len(processed_data)}개 데이터 수집")
            return processed_data
            
        except requests.RequestException as e:
            print(f" API 요청 오류 ({indicator['name']}): {e}")
            return None
        except Exception as e:
            print(f" 데이터 처리 오류 ({indicator['name']}): {e}")
            return None
    
    def get_latest_indicators(self, days_back: int = 30) -> Dict[str, List[Dict]]:
        """최근 지표 데이터 일괄 수집"""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        
        print(f"ECOS 데이터 수집 기간: {start_date} ~ {end_date}")
        
        all_data = {}
        
        for indicator_key in self.indicators.keys():
            print(f"수집 중: {self.indicators[indicator_key]['name']}")
            
            data = self.get_indicator_data(indicator_key, start_date, end_date)
            if data:
                all_data[indicator_key] = data
            
            # API 호출 제한 방지를 위한 대기
            time.sleep(0.5)
        
        return all_data
    
    def calculate_change_rates(self, data: List[Dict]) -> List[Dict]:
        """변화율 계산"""
        if len(data) < 2:
            return data
        
        # 날짜순 정렬
        data.sort(key=lambda x: x["date"])
        
        for i in range(1, len(data)):
            current_value = data[i]["value"]
            previous_value = data[i-1]["value"]
            
            if current_value is not None and previous_value is not None and previous_value != 0:
                change_rate = ((current_value - previous_value) / previous_value) * 100
                data[i]["change_rate"] = round(change_rate, 4)
            else:
                data[i]["change_rate"] = None
        
        # 첫 번째 데이터는 변화율 없음
        data[0]["change_rate"] = None
        
        return data
    
    def save_to_files(self, all_data: Dict[str, List[Dict]], output_dir: str = "data/raw"):
        """수집된 데이터를 파일로 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 전체 데이터를 하나의 JSON 파일로 저장
        json_path = os.path.join(output_dir, "ecos_indicators.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f" JSON 저장: {json_path}")
        
        # CSV 형태로 변환하여 저장
        csv_data = []
        for indicator_key, data_list in all_data.items():
            for data in data_list:
                csv_data.append(data)
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(output_dir, "ecos_indicators.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f" CSV 저장: {csv_path}")
        
        # 최신값만 별도 저장 (그래프 DB 로딩용)
        latest_data = {}
        for indicator_key, data_list in all_data.items():
            if data_list:
                # 변화율 계산
                data_with_rates = self.calculate_change_rates(data_list)
                # 최신 데이터 선택
                latest_data[indicator_key] = data_with_rates[-1]
        
        latest_path = os.path.join(output_dir, "ecos_latest_indicators.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(latest_data, f, ensure_ascii=False, indent=2)
        print(f" 최신 지표 저장: {latest_path}")
        
        return latest_data
    
    def print_summary(self, all_data: Dict[str, List[Dict]]):
        """수집 결과 요약"""
        print("\n=== ECOS 데이터 수집 결과 ===")
        
        total_records = 0
        for indicator_key, data_list in all_data.items():
            count = len(data_list)
            total_records += count
            indicator_name = self.indicators[indicator_key]["name"]
            
            if data_list:
                latest = data_list[-1]
                latest_value = latest["value"]
                latest_date = latest["date"]
                print(f"{indicator_name}: {count}개 ({latest_date} 최신값: {latest_value})")
            else:
                print(f"{indicator_name}: 데이터 없음")
        
        print(f"\n총 수집 레코드: {total_records}개")
    
    def get_current_indicators_summary(self) -> Dict[str, Any]:
        """현재 주요 지표 요약"""
        # 최근 7일 데이터 수집
        data = self.get_latest_indicators(days_back=7)
        
        summary = {}
        for indicator_key, data_list in data.items():
            if data_list:
                data_with_rates = self.calculate_change_rates(data_list)
                latest = data_with_rates[-1]
                
                summary[indicator_key] = {
                    "name": self.indicators[indicator_key]["name"],
                    "current_value": latest["value"],
                    "change_rate": latest.get("change_rate"),
                    "unit": latest["unit"],
                    "date": latest["date"]
                }
        
        return summary

def main():
    """ECOS 데이터 수집 실행"""
    print("=== ECOS API 데이터 수집 시작 ===")
    
    try:
        collector = ECOSAPICollector()
        
        # 최근 30일 데이터 수집
        all_data = collector.get_latest_indicators(days_back=30)
        
        if all_data:
            # 파일 저장
            latest_data = collector.save_to_files(all_data)
            
            # 결과 요약
            collector.print_summary(all_data)
            
            # 현재 지표 요약
            print("\n=== 현재 주요 지표 ===")
            current_summary = collector.get_current_indicators_summary()
            for key, info in current_summary.items():
                change_str = f"({info['change_rate']:+.2f}%)" if info['change_rate'] else ""
                print(f"{info['name']}: {info['current_value']} {info['unit']} {change_str}")
            
            print("\n ECOS 데이터 수집 완료!")
            return True
        else:
            print(" 수집된 데이터가 없습니다.")
            return False
            
    except Exception as e:
        print(f" ECOS 데이터 수집 오류: {e}")
        return False

if __name__ == "__main__":
    main()