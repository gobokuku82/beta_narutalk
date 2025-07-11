"""
고객 정보 에이전트 - 고객 데이터 관리 및 조회
포트: 8004
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Client Agent",
    description="고객 데이터 관리 및 조회 에이전트",
    version="1.0.0"
)

# 요청/응답 모델
class ClientInfoRequest(BaseModel):
    client_id: Optional[str] = None
    info_type: str = "basic"  # basic, transactions, contracts
    filters: Optional[Dict[str, Any]] = None

class ClientInfoResponse(BaseModel):
    info_type: str
    results: Dict[str, Any]
    timestamp: str
    client_count: int

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# 모의 고객 데이터 (실제로는 SQLite 사용)
MOCK_CLIENTS = [
    {
        "id": "client001",
        "name": "ABC 병원",
        "type": "hospital",
        "contact": "02-123-4567",
        "address": "서울시 강남구",
        "registration_date": "2020-03-15",
        "total_transactions": 25,
        "total_amount": 15000000,
        "status": "active"
    },
    {
        "id": "client002",
        "name": "XYZ 의료센터",
        "type": "clinic",
        "contact": "02-987-6543",
        "address": "서울시 서초구",
        "registration_date": "2021-07-20",
        "total_transactions": 18,
        "total_amount": 8500000,
        "status": "active"
    },
    {
        "id": "client003",
        "name": "건강한 약국",
        "type": "pharmacy",
        "contact": "02-555-1234",
        "address": "서울시 송파구",
        "registration_date": "2019-11-10",
        "total_transactions": 42,
        "total_amount": 12000000,
        "status": "active"
    },
    {
        "id": "client004",
        "name": "메디케어 클리닉",
        "type": "clinic",
        "contact": "02-777-8888",
        "address": "서울시 마포구",
        "registration_date": "2022-02-05",
        "total_transactions": 8,
        "total_amount": 3200000,
        "status": "new"
    }
]

# 모의 거래 데이터
MOCK_TRANSACTIONS = [
    {
        "id": "trans001",
        "client_id": "client001",
        "date": "2024-01-15",
        "amount": 850000,
        "product": "감기약 패키지",
        "status": "completed"
    },
    {
        "id": "trans002",
        "client_id": "client001",
        "date": "2024-01-20",
        "amount": 1200000,
        "product": "종합비타민",
        "status": "completed"
    },
    {
        "id": "trans003",
        "client_id": "client002",
        "date": "2024-01-18",
        "amount": 650000,
        "product": "소화제",
        "status": "pending"
    }
]

# 모의 계약 데이터
MOCK_CONTRACTS = [
    {
        "id": "contract001",
        "client_id": "client001",
        "type": "supply_agreement",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "value": 50000000,
        "status": "active"
    },
    {
        "id": "contract002",
        "client_id": "client002",
        "type": "distribution_agreement",
        "start_date": "2024-02-01",
        "end_date": "2024-07-31",
        "value": 25000000,
        "status": "active"
    }
]


def get_client_info(client_id: Optional[str] = None, info_type: str = "basic") -> Dict[str, Any]:
    """고객 정보 조회 함수"""
    
    if client_id:
        # 특정 고객 정보
        client = next((cli for cli in MOCK_CLIENTS if cli['id'] == client_id), None)
        if not client:
            return {"error": f"Client {client_id} not found"}
        
        if info_type == "transactions":
            transactions = [t for t in MOCK_TRANSACTIONS if t['client_id'] == client_id]
            return {
                "client_id": client_id,
                "name": client['name'],
                "transactions": transactions,
                "total_transactions": len(transactions),
                "total_amount": sum(t['amount'] for t in transactions)
            }
        
        elif info_type == "contracts":
            contracts = [c for c in MOCK_CONTRACTS if c['client_id'] == client_id]
            return {
                "client_id": client_id,
                "name": client['name'],
                "contracts": contracts,
                "total_contracts": len(contracts),
                "total_contract_value": sum(c['value'] for c in contracts)
            }
        
        else:  # basic
            return {
                "client_id": client_id,
                "name": client['name'],
                "type": client['type'],
                "contact": client['contact'],
                "address": client['address'],
                "registration_date": client['registration_date'],
                "total_transactions": client['total_transactions'],
                "total_amount": client['total_amount'],
                "status": client['status']
            }
    
    else:
        # 전체 고객 정보
        if info_type == "transactions":
            return {
                "total_clients": len(MOCK_CLIENTS),
                "total_transactions": len(MOCK_TRANSACTIONS),
                "total_amount": sum(t['amount'] for t in MOCK_TRANSACTIONS),
                "recent_transactions": sorted(MOCK_TRANSACTIONS, key=lambda x: x['date'], reverse=True)[:5],
                "transaction_status": {
                    "completed": len([t for t in MOCK_TRANSACTIONS if t['status'] == 'completed']),
                    "pending": len([t for t in MOCK_TRANSACTIONS if t['status'] == 'pending'])
                }
            }
        
        elif info_type == "contracts":
            return {
                "total_clients": len(MOCK_CLIENTS),
                "total_contracts": len(MOCK_CONTRACTS),
                "total_contract_value": sum(c['value'] for c in MOCK_CONTRACTS),
                "active_contracts": len([c for c in MOCK_CONTRACTS if c['status'] == 'active']),
                "contract_types": {
                    "supply_agreement": len([c for c in MOCK_CONTRACTS if c['type'] == 'supply_agreement']),
                    "distribution_agreement": len([c for c in MOCK_CONTRACTS if c['type'] == 'distribution_agreement'])
                }
            }
        
        else:  # basic
            return {
                "total_clients": len(MOCK_CLIENTS),
                "client_types": {
                    "hospital": len([c for c in MOCK_CLIENTS if c['type'] == 'hospital']),
                    "clinic": len([c for c in MOCK_CLIENTS if c['type'] == 'clinic']),
                    "pharmacy": len([c for c in MOCK_CLIENTS if c['type'] == 'pharmacy'])
                },
                "client_status": {
                    "active": len([c for c in MOCK_CLIENTS if c['status'] == 'active']),
                    "new": len([c for c in MOCK_CLIENTS if c['status'] == 'new'])
                },
                "total_business_value": sum(c['total_amount'] for c in MOCK_CLIENTS)
            }


@app.post("/info", response_model=ClientInfoResponse)
async def get_client_information(request: ClientInfoRequest):
    """고객 정보 조회"""
    try:
        logger.info(f"Getting client info: {request.client_id}, type: {request.info_type}")
        
        # 고객 정보 조회
        results = get_client_info(request.client_id, request.info_type)
        
        response = ClientInfoResponse(
            info_type=request.info_type,
            results=results,
            timestamp=datetime.now().isoformat(),
            client_count=len(MOCK_CLIENTS)
        )
        
        logger.info(f"Client info retrieved for {request.info_type}")
        return response
        
    except Exception as e:
        logger.error(f"Client info error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients")
async def list_clients():
    """고객 목록 조회"""
    return {
        "clients": MOCK_CLIENTS,
        "total": len(MOCK_CLIENTS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/transactions")
async def list_transactions():
    """거래 목록 조회"""
    return {
        "transactions": MOCK_TRANSACTIONS,
        "total": len(MOCK_TRANSACTIONS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/contracts")
async def list_contracts():
    """계약 목록 조회"""
    return {
        "contracts": MOCK_CONTRACTS,
        "total": len(MOCK_CONTRACTS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """통계 조회"""
    return {
        "total_clients": len(MOCK_CLIENTS),
        "total_transactions": len(MOCK_TRANSACTIONS),
        "total_contracts": len(MOCK_CONTRACTS),
        "total_business_value": sum(c['total_amount'] for c in MOCK_CLIENTS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="client_agent",
        timestamp=datetime.now().isoformat(),
        details={
            "port": 8004,
            "version": "1.0.0",
            "capabilities": ["client_management", "transaction_tracking", "contract_management"],
            "client_count": len(MOCK_CLIENTS)
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "client_agent",
        "description": "고객 데이터 관리 및 조회 에이전트",
        "version": "1.0.0",
        "endpoints": {
            "info": "/info",
            "clients": "/clients",
            "transactions": "/transactions",
            "contracts": "/contracts",
            "stats": "/stats",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 