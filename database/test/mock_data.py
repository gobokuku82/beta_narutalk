"""
Mock Database Manager
테스트용 데이터 관리 및 접근 인터페이스
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import logging
logger = logging.getLogger(__name__)


class MockDatabase:
    """Mock 데이터베이스 관리 클래스"""
    
    def __init__(self):
        """Mock 데이터베이스 초기화"""
        self.base_path = Path(__file__).parent
        self.data = {}
        self._load_all_data()
    
    def _load_all_data(self):
        """모든 JSON 데이터 파일 로드"""
        data_files = {
            'drugs': 'drug_database.json',
            'sales': 'sales_data.json',
            'compliance': 'compliance_data.json',
            'customers': 'customer_data.json'
        }
        
        for key, filename in data_files.items():
            filepath = self.base_path / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.data[key] = json.load(f)
                logger.info(f"Loaded {key} data from {filename}")
            else:
                logger.warning(f"Data file not found: {filename}")
                self.data[key] = {}
    
    # Drug Database Methods
    def get_drug_by_id(self, drug_id: str) -> Optional[Dict]:
        """ID로 약물 정보 조회"""
        drugs = self.data.get('drugs', {}).get('drugs', [])
        for drug in drugs:
            if drug['id'] == drug_id:
                return drug
        return None
    
    def get_drug_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 약물 정보 조회 (한글/영문)"""
        drugs = self.data.get('drugs', {}).get('drugs', [])
        name_lower = name.lower()
        
        for drug in drugs:
            if (name_lower in drug['generic_name'].lower() or 
                name in drug['korean_name'] or
                any(name in brand for brand in drug['brand_names'])):
                return drug
        return None
    
    def search_drugs(self, keyword: str, category: str = None) -> List[Dict]:
        """키워드로 약물 검색"""
        drugs = self.data.get('drugs', {}).get('drugs', [])
        results = []
        keyword_lower = keyword.lower()
        
        for drug in drugs:
            # 카테고리 필터
            if category and drug['category'] != category:
                continue
            
            # 키워드 매칭
            if (keyword_lower in drug['generic_name'].lower() or
                keyword in drug['korean_name'] or
                any(keyword in brand for brand in drug['brand_names']) or
                any(keyword in indication for indication in drug['indication'])):
                results.append(drug)
        
        return results
    
    def get_drug_categories(self) -> List[str]:
        """모든 약물 카테고리 목록"""
        drugs = self.data.get('drugs', {}).get('drugs', [])
        categories = list(set(drug['category'] for drug in drugs))
        return sorted(categories)
    
    # Sales Database Methods
    def get_monthly_sales(self, year: int = 2024, month: str = None) -> Dict:
        """월별 매출 데이터 조회"""
        sales = self.data.get('sales', {}).get('monthly_sales', {})
        year_data = sales.get(str(year), {})
        
        if month:
            return year_data.get(month, {})
        return year_data
    
    def get_team_performance(self, team_name: str = None) -> Dict:
        """팀별 실적 데이터 조회"""
        performance = self.data.get('sales', {}).get('team_performance', {})
        
        if team_name:
            return performance.get(team_name, {})
        return performance
    
    def get_product_ranking(self, top_n: int = 10) -> List[Dict]:
        """제품 판매 순위"""
        ranking = self.data.get('sales', {}).get('product_ranking', [])
        return ranking[:top_n]
    
    def get_customer_purchases(self, customer_id: str = None) -> List[Dict]:
        """고객 구매 이력"""
        purchases = self.data.get('sales', {}).get('customer_purchases', [])
        
        if customer_id:
            return [p for p in purchases if p['customer_id'] == customer_id]
        return purchases
    
    def get_kpi_metrics(self) -> Dict:
        """KPI 지표 조회"""
        return self.data.get('sales', {}).get('kpi_metrics', {})
    
    # Compliance Database Methods
    def get_regulations(self, agency: str = None, category: str = None) -> Dict:
        """규정 정보 조회"""
        regulations = self.data.get('compliance', {}).get('regulations', {})
        
        if agency:
            agency_regs = regulations.get(agency, {})
            if category:
                return agency_regs.get(category, {})
            return agency_regs
        return regulations
    
    def get_recent_updates(self, limit: int = 5) -> List[Dict]:
        """최근 규정 업데이트"""
        updates = self.data.get('compliance', {}).get('recent_updates', [])
        return updates[:limit]
    
    def get_compliance_checklist(self, category: str = None) -> Dict:
        """컴플라이언스 체크리스트"""
        checklist = self.data.get('compliance', {}).get('compliance_checklist', {})
        
        if category:
            return checklist.get(category, [])
        return checklist
    
    def get_risk_assessment(self) -> Dict:
        """리스크 평가 정보"""
        return self.data.get('compliance', {}).get('risk_assessment', {})
    
    def get_audit_history(self) -> List[Dict]:
        """감사 이력"""
        return self.data.get('compliance', {}).get('audit_history', [])
    
    # Customer Database Methods
    def get_hospital(self, hospital_id: str = None) -> Dict:
        """병원 정보 조회"""
        hospitals = self.data.get('customers', {}).get('hospitals', [])
        
        if hospital_id:
            for hospital in hospitals:
                if hospital['id'] == hospital_id:
                    return hospital
            return None
        return hospitals
    
    def get_clinic(self, clinic_id: str = None) -> Dict:
        """의원 정보 조회"""
        clinics = self.data.get('customers', {}).get('clinics', [])
        
        if clinic_id:
            for clinic in clinics:
                if clinic['id'] == clinic_id:
                    return clinic
            return None
        return clinics
    
    def get_pharmacy(self, pharmacy_id: str = None) -> Dict:
        """약국 정보 조회"""
        pharmacies = self.data.get('customers', {}).get('pharmacies', [])
        
        if pharmacy_id:
            for pharmacy in pharmacies:
                if pharmacy['id'] == pharmacy_id:
                    return pharmacy
            return None
        return pharmacies
    
    def get_doctor(self, doctor_id: str = None) -> Dict:
        """의사 정보 조회"""
        doctors = self.data.get('customers', {}).get('doctors', [])
        
        if doctor_id:
            for doctor in doctors:
                if doctor['id'] == doctor_id:
                    return doctor
            return None
        return doctors
    
    def get_customer_segments(self) -> Dict:
        """고객 세그먼트 정보"""
        return self.data.get('customers', {}).get('customer_segments', {})
    
    def search_customers(self, keyword: str, customer_type: str = None) -> List[Dict]:
        """고객 검색"""
        results = []
        keyword_lower = keyword.lower()
        
        # 병원 검색
        if not customer_type or customer_type == 'hospital':
            hospitals = self.data.get('customers', {}).get('hospitals', [])
            for hospital in hospitals:
                if (keyword_lower in hospital['name'].lower() or
                    keyword_lower in hospital['address'].lower()):
                    results.append({**hospital, 'customer_type': 'hospital'})
        
        # 의원 검색
        if not customer_type or customer_type == 'clinic':
            clinics = self.data.get('customers', {}).get('clinics', [])
            for clinic in clinics:
                if (keyword_lower in clinic['name'].lower() or
                    keyword_lower in clinic['doctor'].lower()):
                    results.append({**clinic, 'customer_type': 'clinic'})
        
        # 약국 검색
        if not customer_type or customer_type == 'pharmacy':
            pharmacies = self.data.get('customers', {}).get('pharmacies', [])
            for pharmacy in pharmacies:
                if keyword_lower in pharmacy['name'].lower():
                    results.append({**pharmacy, 'customer_type': 'pharmacy'})
        
        return results
    
    # Analytics Helper Methods
    def get_sales_summary(self, period: str = '2024-06') -> Dict:
        """매출 요약 통계"""
        monthly_sales = self.get_monthly_sales(2024)
        
        if period in monthly_sales:
            month_data = monthly_sales[period.split('-')[1] + '월']
            total_sales = month_data.get('total', 0)
            
            # 전월 대비 성장률 계산
            months = list(monthly_sales.keys())
            current_idx = months.index(period.split('-')[1] + '월')
            if current_idx > 0:
                prev_month = months[current_idx - 1]
                prev_total = monthly_sales[prev_month].get('total', 0)
                growth_rate = ((total_sales - prev_total) / prev_total * 100) if prev_total else 0
            else:
                growth_rate = 0
            
            return {
                'period': period,
                'total_sales': total_sales,
                'growth_rate': round(growth_rate, 2),
                'top_product': max(month_data['products'].items(), key=lambda x: x[1])[0] if month_data.get('products') else None,
                'top_region': max(month_data['regions'].items(), key=lambda x: x[1])[0] if month_data.get('regions') else None
            }
        
        return {}
    
    def generate_mock_trend(self, data_type: str = 'sales', periods: int = 6) -> List[Dict]:
        """트렌드 데이터 생성 (시뮬레이션)"""
        trends = []
        base_value = random.randint(1000000, 5000000)
        
        for i in range(periods):
            variation = random.uniform(-0.1, 0.2)  # -10% ~ +20% 변동
            value = int(base_value * (1 + variation))
            trends.append({
                'period': f'2024-{str(i+1).zfill(2)}',
                'value': value,
                'type': data_type
            })
            base_value = value
        
        return trends
    
    # CRUD Operations (for future real DB migration)
    def create_record(self, collection: str, data: Dict) -> Dict:
        """레코드 생성 (시뮬레이션)"""
        # 실제 DB에서는 INSERT 수행
        record_id = f"{collection[:3].upper()}{random.randint(1000, 9999)}"
        data['id'] = record_id
        data['created_at'] = datetime.now().isoformat()
        
        logger.info(f"Created record in {collection}: {record_id}")
        return data
    
    def update_record(self, collection: str, record_id: str, data: Dict) -> Dict:
        """레코드 업데이트 (시뮬레이션)"""
        # 실제 DB에서는 UPDATE 수행
        data['updated_at'] = datetime.now().isoformat()
        logger.info(f"Updated record in {collection}: {record_id}")
        return data
    
    def delete_record(self, collection: str, record_id: str) -> bool:
        """레코드 삭제 (시뮬레이션)"""
        # 실제 DB에서는 DELETE 수행
        logger.info(f"Deleted record from {collection}: {record_id}")
        return True
    

# Singleton instance
mock_db = MockDatabase()

# Export functions for easy access
def get_mock_db() -> MockDatabase:
    """Mock DB 인스턴스 반환"""
    return mock_db