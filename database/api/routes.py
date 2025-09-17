"""
API Routes for Worker Agents
Worker Agents와 데이터베이스를 연결하는 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import sqlite3
import os
import logging
from datetime import datetime
import aiofiles
import asyncio

from ..system.connection import get_db
from ..system.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/v1", tags=["Worker Agent APIs"])

# Initialize database manager
db_manager = DatabaseManager()


# ===== SQL Execution Endpoints =====

@router.post("/execute_sql")
async def execute_sql(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute SQL query on specified database

    Request body:
    - query: SQL query string
    - database: Target database name (hr, sales, rules, hr_rules)
    - timeout: Query timeout in seconds (optional, default: 30)
    """
    try:
        query = request.get("query")
        database = request.get("database", "sales")  # Default to sales DB
        timeout = request.get("timeout", 30)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Execute query through database manager
        result = await db_manager.execute_query(database, query, timeout)

        return {
            "status": "success",
            "data": result.get("data", []),
            "rows_affected": result.get("rows_affected", 0),
            "execution_time": result.get("execution_time", 0),
            "database": database
        }

    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database": database
        }


@router.get("/schema/{table_name}")
async def get_table_schema(
    table_name: str,
    database: Optional[str] = Query("sales", description="Target database")
) -> Dict[str, Any]:
    """
    Get schema information for a specific table

    Path parameters:
    - table_name: Name of the table

    Query parameters:
    - database: Target database (hr, sales, rules, hr_rules)
    """
    try:
        # Get schema from database manager
        schema_info = await db_manager.get_table_schema(database, table_name)

        if not schema_info:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found in {database}")

        return {
            "status": "success",
            "table": table_name,
            "database": database,
            "columns": schema_info.get("columns", []),
            "indexes": schema_info.get("indexes", []),
            "row_count": schema_info.get("row_count", 0)
        }

    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemas")
async def get_all_schemas() -> Dict[str, Any]:
    """
    Get schema information for all databases and tables
    """
    try:
        # Load schema from JSON file
        schema_path = "database/schemas/text2sql_schema.json"

        if os.path.exists(schema_path):
            async with aiofiles.open(schema_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                schemas = json.loads(content)

            return {
                "status": "success",
                "schemas": schemas
            }
        else:
            # Fallback to dynamic schema retrieval
            all_schemas = await db_manager.get_all_schemas()
            return {
                "status": "success",
                "schemas": all_schemas
            }

    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Search Endpoints =====

@router.post("/search/hr")
async def search_hr(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search HR information database

    Request body:
    - query: Search query
    - filters: Optional filters (department, position, etc.)
    - limit: Maximum results (default: 100)
    """
    try:
        search_query = request.get("query", "")
        filters = request.get("filters", {})
        limit = request.get("limit", 100)

        # Build SQL query for HR database
        sql = """
        SELECT * FROM 인사자료
        WHERE 1=1
        """

        conditions = []
        if search_query:
            conditions.append(f"(성명 LIKE '%{search_query}%' OR 사번 LIKE '%{search_query}%')")

        if filters.get("department"):
            conditions.append(f"부서 = '{filters['department']}'")

        if filters.get("position"):
            conditions.append(f"직급 = '{filters['position']}'")

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        sql += f" LIMIT {limit}"

        # Execute on HR database
        result = await db_manager.execute_query("hr", sql)

        return {
            "status": "success",
            "data": result.get("data", []),
            "count": len(result.get("data", [])),
            "query": search_query
        }

    except Exception as e:
        logger.error(f"HR search failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }


@router.post("/search/regulations")
async def search_regulations(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search regulations and rules databases

    Request body:
    - query: Search query
    - rule_type: Type of rule (medical_law, rebate_law, fair_trade, etc.)
    - keywords: List of keywords
    """
    try:
        search_query = request.get("query", "")
        rule_type = request.get("rule_type", "all")
        keywords = request.get("keywords", [])

        results = []

        # Search in rules_DB
        if rule_type in ["all", "medical", "rebate", "fair_trade"]:
            sql = f"""
            SELECT * FROM rules
            WHERE content LIKE '%{search_query}%'
            """

            if keywords:
                keyword_conditions = " OR ".join([f"content LIKE '%{kw}%'" for kw in keywords])
                sql += f" OR ({keyword_conditions})"

            rule_results = await db_manager.execute_query("rules", sql)
            results.extend(rule_results.get("data", []))

        # Search in hr_rules_db
        if rule_type in ["all", "hr", "internal"]:
            sql = f"""
            SELECT * FROM hr_rules
            WHERE rule_content LIKE '%{search_query}%'
            """

            hr_rule_results = await db_manager.execute_query("hr_rules", sql)
            results.extend(hr_rule_results.get("data", []))

        return {
            "status": "success",
            "data": results,
            "count": len(results),
            "query": search_query,
            "rule_type": rule_type
        }

    except Exception as e:
        logger.error(f"Regulation search failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }


@router.post("/search/papers")
async def search_papers(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search medical papers (mock implementation - connect to real APIs)

    Request body:
    - query: Search query
    - source: Paper source (pubmed, arxiv, etc.)
    - limit: Maximum results
    """
    try:
        search_query = request.get("query", "")
        source = request.get("source", "pubmed")
        limit = request.get("limit", 20)

        # TODO: Implement actual paper search APIs (PubMed, arXiv, etc.)
        # For now, return mock data

        return {
            "status": "success",
            "data": [
                {
                    "title": f"Sample paper about {search_query}",
                    "authors": ["Author 1", "Author 2"],
                    "abstract": f"Abstract related to {search_query}",
                    "source": source,
                    "url": "https://example.com/paper",
                    "published_date": "2024-01-01"
                }
            ],
            "count": 1,
            "query": search_query,
            "source": source
        }

    except Exception as e:
        logger.error(f"Paper search failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }


@router.post("/search/hira")
async def search_hira(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search HIRA (Health Insurance Review & Assessment) data

    Request body:
    - query: Search query
    - category: Data category
    - period: Time period
    """
    try:
        search_query = request.get("query", "")
        category = request.get("category", "all")
        period = request.get("period", "2024")

        # TODO: Implement actual HIRA API integration
        # For now, return mock data

        return {
            "status": "success",
            "data": [
                {
                    "item": f"HIRA data for {search_query}",
                    "category": category,
                    "period": period,
                    "value": 0,
                    "unit": "건"
                }
            ],
            "count": 1,
            "query": search_query
        }

    except Exception as e:
        logger.error(f"HIRA search failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }


# ===== Document Management Endpoints =====

@router.post("/documents/generate")
async def generate_document(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate documents (reports, forms, etc.)

    Request body:
    - document_type: Type of document (visit_report, product_seminar, sample_request)
    - template_id: Template to use
    - data: Data to fill in the template
    """
    try:
        doc_type = request.get("document_type")
        template_id = request.get("template_id")
        data = request.get("data", {})

        if not doc_type:
            raise HTTPException(status_code=400, detail="Document type is required")

        # TODO: Implement actual document generation logic
        # For now, return mock document

        document = {
            "id": f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": doc_type,
            "template": template_id,
            "content": f"Generated {doc_type} document",
            "created_at": datetime.now().isoformat(),
            "status": "generated"
        }

        return {
            "status": "success",
            "document": document
        }

    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/documents/store")
async def store_document(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store generated documents in database

    Request body:
    - document: Document object to store
    - database: Target database (default: main chatbot DB)
    """
    try:
        document = request.get("document")
        database = request.get("database", "main")

        if not document:
            raise HTTPException(status_code=400, detail="Document is required")

        # Store in appropriate database
        # TODO: Implement actual storage logic

        return {
            "status": "success",
            "document_id": document.get("id"),
            "stored_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Document storage failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# ===== Rules and Compliance Endpoints =====

@router.get("/rules/{rule_type}")
async def get_rules(
    rule_type: str,
    keywords: Optional[List[str]] = Query(None)
) -> Dict[str, Any]:
    """
    Get specific rules and regulations

    Path parameters:
    - rule_type: Type of rule (medical_law, rebate_law, fair_trade, etc.)

    Query parameters:
    - keywords: Optional keywords to filter
    """
    try:
        # Query rules database
        sql = f"SELECT * FROM rules WHERE type = '{rule_type}'"

        if keywords:
            keyword_conditions = " OR ".join([f"content LIKE '%{kw}%'" for kw in keywords])
            sql += f" AND ({keyword_conditions})"

        result = await db_manager.execute_query("rules", sql)

        return {
            "status": "success",
            "rule_type": rule_type,
            "rules": result.get("data", []),
            "count": len(result.get("data", []))
        }

    except Exception as e:
        logger.error(f"Rules retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/check")
async def check_compliance(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check document compliance with regulations

    Request body:
    - document: Document content to check
    - rules: List of rules to check against
    - strict_mode: Enable strict compliance checking
    """
    try:
        document = request.get("document", "")
        rules = request.get("rules", ["medical_law", "rebate_law"])
        strict_mode = request.get("strict_mode", True)

        # TODO: Implement actual compliance checking logic
        # This would involve:
        # 1. Parsing the document
        # 2. Extracting key elements
        # 3. Checking against rule database
        # 4. Identifying violations

        return {
            "status": "success",
            "compliant": True,
            "violations": [],
            "warnings": [],
            "checked_rules": rules
        }

    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "compliant": False
        }


# ===== Analytics Endpoints =====

@router.post("/analytics/sales")
async def analyze_sales(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze sales performance data

    Request body:
    - period: Analysis period
    - metrics: Metrics to calculate
    - group_by: Grouping criteria
    """
    try:
        period = request.get("period", "monthly")
        metrics = request.get("metrics", ["total", "average"])
        group_by = request.get("group_by", "employee")

        # Build analytics query
        sql = """
        SELECT
            employee_name,
            SUM(sales_amount) as total_sales,
            AVG(sales_amount) as avg_sales,
            COUNT(*) as transaction_count
        FROM sales_performance
        GROUP BY employee_name
        """

        result = await db_manager.execute_query("sales", sql)

        return {
            "status": "success",
            "data": result.get("data", []),
            "period": period,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Sales analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": []
        }


# ===== Health Check =====

@router.get("/health")
async def api_health_check() -> Dict[str, Any]:
    """
    Check API and database connectivity
    """
    try:
        # Check all database connections
        db_status = await db_manager.check_all_connections()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "databases": db_status,
            "version": "1.0.0"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }