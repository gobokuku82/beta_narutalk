"""
스키마 파일 생성 스크립트
database/schemas/ 폴더에 필요한 JSON 파일 생성
"""

import json
from pathlib import Path

def create_schema_files():
    """누락된 스키마 파일 생성"""
    
    # schemas 디렉토리 생성
    schema_dir = Path("database/schemas")
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating schema files in {schema_dir}")
    
    # 1. table_descriptions.json
    table_descriptions = {
        "sales_performance": {
            "description": "월별 판매 실적 데이터",
            "columns": {
                "사번": "직원 사번",
                "담당자": "담당자 이름",
                "거래처ID": "거래처 고유 식별자",
                "품목": "판매 품목명",
                "202212-202411": "월별 매출액 (YYYYMM 형식)"
            }
        },
        "지점별목표": {
            "description": "지점별 담당자별 월별 판매 목표",
            "columns": {
                "지점": "소속 지점/팀",
                "담당자": "담당자 이름",
                "202312-202411": "월별 목표액"
            }
        },
        "거래처자료": {
            "description": "거래처별 월간 영업 활동 및 성과",
            "columns": {
                "거래처ID": "거래처 식별자",
                "월": "년월 (YYYYMM)",
                "매출": "월 매출액",
                "월방문횟수": "월간 방문 횟수",
                "사용 예산": "사용된 마케팅 예산",
                "총환자수": "병원 총 환자수",
                "담당자": "담당 영업사원"
            }
        },
        "거래처정보": {
            "description": "거래처(병원/의원) 기본 정보",
            "columns": {
                "ID": "거래처 고유 식별자",
                "원장명": "병원 원장 이름",
                "지역구": "소재 지역구",
                "병원연락처": "대표 전화번호"
            }
        },
        "인사자료": {
            "description": "직원 정보",
            "columns": {
                "사번": "직원 사번",
                "성명": "직원 이름",
                "본부": "소속 본부",
                "직급": "직급",
                "부서": "부서명",
                "지점": "소속 지점",
                "연락처": "연락처",
                "기본급(₩)": "기본급",
                "성과급(₩)": "성과급"
            }
        }
    }
    
    # Save table_descriptions.json
    desc_file = schema_dir / "table_descriptions.json"
    with open(desc_file, 'w', encoding='utf-8') as f:
        json.dump(table_descriptions, f, ensure_ascii=False, indent=2)
    print(f"✅ Created: {desc_file}")
    
    # 2. relationships.json
    relationships = {
        "joins": [
            {
                "table1": "sales_performance",
                "table2": "인사자료",
                "on": "sales_performance.사번 = 인사자료.사번",
                "type": "INNER",
                "description": "직원 정보와 판매 실적 연결"
            },
            {
                "table1": "sales_performance",
                "table2": "거래처자료",
                "on": "sales_performance.거래처ID = 거래처자료.거래처ID",
                "type": "LEFT",
                "description": "거래처 정보와 판매 실적 연결"
            },
            {
                "table1": "인사자료",
                "table2": "지점별목표",
                "on": "인사자료.지점 = 지점별목표.지점",
                "type": "LEFT",
                "description": "지점별 목표와 직원 정보 연결"
            }
        ],
        "foreign_keys": [
            {
                "table": "sales_performance",
                "column": "사번",
                "references": {
                    "table": "인사자료",
                    "column": "사번"
                }
            },
            {
                "table": "sales_performance",
                "column": "거래처ID",
                "references": {
                    "table": "거래처정보",
                    "column": "ID"
                }
            }
        ]
    }
    
    # Save relationships.json
    rel_file = schema_dir / "relationships.json"
    with open(rel_file, 'w', encoding='utf-8') as f:
        json.dump(relationships, f, ensure_ascii=False, indent=2)
    print(f"✅ Created: {rel_file}")
    
    print("\n스키마 파일 생성 완료!")
    print("이제 test_text2sql.py를 다시 실행하면 warning이 사라집니다.")

if __name__ == "__main__":
    create_schema_files()
