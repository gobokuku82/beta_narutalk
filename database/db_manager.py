"""
Database Manager for Multiple SQLite Databases
다중 SQLite 데이터베이스 연결 및 관리
"""

import sqlite3
import aiosqlite
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages connections to multiple SQLite databases
    """

    def __init__(self):
        """Initialize database manager with database paths"""

        # Database configuration
        self.databases = {
            "hr": {
                "path": "database/hr_information/hr_data.db",
                "description": "인사정보 데이터베이스",
                "tables": ["인사자료", "지점연락처"]
            },
            "sales": {
                "path": "database/sales_performance_db/sales_performance_db.db",
                "description": "영업실적 데이터베이스",
                "tables": ["sales_performance", "monthly_summary", "employee_targets"]
            },
            "hr_rules": {
                "path": "database/hr_rules_db/hr_rules.db",
                "description": "HR 규정 데이터베이스",
                "tables": ["hr_rules", "policy_documents"]
            },
            "rules": {
                "path": "database/rules_DB/rules.db",
                "description": "일반 규정 데이터베이스",
                "tables": ["rules", "medical_laws", "rebate_laws", "fair_trade_rules"]
            }
        }

        # Connection pool
        self.connections = {}

        # Schema cache
        self.schema_cache = {}

        # Load schema from JSON if available
        self._load_schema_cache()

    def _load_schema_cache(self):
        """Load schema information from JSON files"""
        schema_files = [
            "database/schemas/text2sql_schema.json",
            "database/schemas/database_schema.json"
        ]

        for schema_file in schema_files:
            if os.path.exists(schema_file):
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                        self.schema_cache.update(schema_data)
                        logger.info(f"Loaded schema from {schema_file}")
                except Exception as e:
                    logger.error(f"Failed to load schema from {schema_file}: {e}")

    @asynccontextmanager
    async def get_connection(self, db_name: str):
        """
        Get database connection with context manager

        Args:
            db_name: Name of the database (hr, sales, rules, hr_rules)

        Yields:
            Database connection
        """
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")

        db_path = self.databases[db_name]["path"]

        # Check if database file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        # Create connection
        conn = await aiosqlite.connect(db_path)

        try:
            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")

            # Set busy timeout (for concurrent access)
            await conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds

            yield conn

        finally:
            await conn.close()

    async def execute_query(
        self,
        db_name: str,
        query: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute SQL query on specified database

        Args:
            db_name: Name of the database
            query: SQL query to execute
            timeout: Query timeout in seconds

        Returns:
            Query result with data and metadata
        """
        start_time = datetime.now()

        try:
            async with self.get_connection(db_name) as conn:
                # Set query timeout
                await conn.execute(f"PRAGMA busy_timeout = {timeout * 1000}")

                # Execute query
                cursor = await conn.execute(query)

                # Determine query type
                query_lower = query.lower().strip()

                if query_lower.startswith("select"):
                    # Fetch results for SELECT queries
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []

                    # Convert to list of dicts
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))

                    result = {
                        "data": data,
                        "columns": columns,
                        "row_count": len(data),
                        "query_type": "SELECT"
                    }

                elif query_lower.startswith(("insert", "update", "delete")):
                    # For DML queries, commit changes
                    await conn.commit()

                    result = {
                        "rows_affected": cursor.rowcount,
                        "query_type": query_lower.split()[0].upper(),
                        "data": []
                    }

                elif query_lower.startswith(("create", "alter", "drop")):
                    # For DDL queries
                    await conn.commit()

                    result = {
                        "query_type": query_lower.split()[0].upper(),
                        "success": True,
                        "data": []
                    }

                else:
                    # Other queries
                    result = {
                        "query_type": "OTHER",
                        "data": []
                    }

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                result["execution_time"] = execution_time

                logger.info(f"Query executed on {db_name} in {execution_time:.2f}s")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Query timeout on {db_name} after {timeout}s")
            raise Exception(f"Query timeout after {timeout} seconds")

        except Exception as e:
            logger.error(f"Query execution failed on {db_name}: {e}")
            raise

    async def get_table_schema(
        self,
        db_name: str,
        table_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get schema information for a specific table

        Args:
            db_name: Name of the database
            table_name: Name of the table

        Returns:
            Table schema information
        """
        # Check cache first
        cache_key = f"{db_name}.{table_name}"
        if cache_key in self.schema_cache:
            return self.schema_cache[cache_key]

        try:
            async with self.get_connection(db_name) as conn:
                # Get table info
                cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                columns_info = await cursor.fetchall()

                if not columns_info:
                    return None

                columns = []
                for col in columns_info:
                    columns.append({
                        "name": col[1],
                        "type": col[2],
                        "nullable": not col[3],
                        "default": col[4],
                        "primary_key": bool(col[5])
                    })

                # Get indexes
                cursor = await conn.execute(f"PRAGMA index_list({table_name})")
                indexes_info = await cursor.fetchall()

                indexes = []
                for idx in indexes_info:
                    indexes.append({
                        "name": idx[1],
                        "unique": bool(idx[2])
                    })

                # Get row count
                cursor = await conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = (await cursor.fetchone())[0]

                schema = {
                    "table": table_name,
                    "database": db_name,
                    "columns": columns,
                    "indexes": indexes,
                    "row_count": row_count
                }

                # Cache the schema
                self.schema_cache[cache_key] = schema

                return schema

        except Exception as e:
            logger.error(f"Failed to get schema for {table_name} in {db_name}: {e}")
            return None

    async def get_all_schemas(self) -> Dict[str, Any]:
        """
        Get schema information for all databases and tables

        Returns:
            Complete schema information
        """
        all_schemas = {}

        for db_name, db_info in self.databases.items():
            db_schemas = {}

            try:
                async with self.get_connection(db_name) as conn:
                    # Get all tables
                    cursor = await conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = await cursor.fetchall()

                    for table in tables:
                        table_name = table[0]
                        schema = await self.get_table_schema(db_name, table_name)
                        if schema:
                            db_schemas[table_name] = schema

                all_schemas[db_name] = {
                    "description": db_info["description"],
                    "path": db_info["path"],
                    "tables": db_schemas
                }

            except Exception as e:
                logger.error(f"Failed to get schemas for {db_name}: {e}")
                all_schemas[db_name] = {"error": str(e)}

        return all_schemas

    async def search_tables(
        self,
        search_term: str,
        db_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for data across tables

        Args:
            search_term: Term to search for
            db_name: Optional specific database to search

        Returns:
            Search results from matching tables
        """
        results = []
        databases = [db_name] if db_name else list(self.databases.keys())

        for db in databases:
            try:
                async with self.get_connection(db) as conn:
                    # Get all tables
                    cursor = await conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = await cursor.fetchall()

                    for table in tables:
                        table_name = table[0]

                        # Get columns
                        cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                        columns = await cursor.fetchall()

                        # Build search query for text columns
                        text_columns = [
                            col[1] for col in columns
                            if col[2].upper() in ['TEXT', 'VARCHAR', 'CHAR']
                        ]

                        if text_columns:
                            conditions = " OR ".join([
                                f"{col} LIKE '%{search_term}%'"
                                for col in text_columns
                            ])

                            search_sql = f"SELECT * FROM {table_name} WHERE {conditions} LIMIT 10"

                            try:
                                cursor = await conn.execute(search_sql)
                                rows = await cursor.fetchall()

                                if rows:
                                    col_names = [desc[0] for desc in cursor.description]
                                    for row in rows:
                                        results.append({
                                            "database": db,
                                            "table": table_name,
                                            "data": dict(zip(col_names, row))
                                        })

                            except Exception as e:
                                logger.debug(f"Search failed in {db}.{table_name}: {e}")

            except Exception as e:
                logger.error(f"Search failed in database {db}: {e}")

        return results

    async def check_all_connections(self) -> Dict[str, Any]:
        """
        Check connectivity to all databases

        Returns:
            Status of each database connection
        """
        status = {}

        for db_name, db_info in self.databases.items():
            try:
                if not os.path.exists(db_info["path"]):
                    status[db_name] = {
                        "status": "error",
                        "message": "Database file not found",
                        "path": db_info["path"]
                    }
                    continue

                async with self.get_connection(db_name) as conn:
                    # Test query
                    cursor = await conn.execute("SELECT 1")
                    await cursor.fetchone()

                    # Get database size
                    file_size = os.path.getsize(db_info["path"])

                    status[db_name] = {
                        "status": "connected",
                        "path": db_info["path"],
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    }

            except Exception as e:
                status[db_name] = {
                    "status": "error",
                    "message": str(e),
                    "path": db_info["path"]
                }

        return status

    async def backup_database(
        self,
        db_name: str,
        backup_path: Optional[str] = None
    ) -> str:
        """
        Create a backup of specified database

        Args:
            db_name: Name of the database to backup
            backup_path: Optional custom backup path

        Returns:
            Path to backup file
        """
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")

        source_path = self.databases[db_name]["path"]

        if not backup_path:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "database/backups"
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = f"{backup_dir}/{db_name}_backup_{timestamp}.db"

        try:
            async with self.get_connection(db_name) as source_conn:
                # Use SQLite backup API
                async with aiosqlite.connect(backup_path) as backup_conn:
                    await source_conn.backup(backup_conn)

            logger.info(f"Database {db_name} backed up to {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Backup failed for {db_name}: {e}")
            raise

    def get_database_info(self, db_name: str) -> Dict[str, Any]:
        """
        Get information about a specific database

        Args:
            db_name: Name of the database

        Returns:
            Database information
        """
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")

        db_info = self.databases[db_name].copy()

        # Add file size if exists
        if os.path.exists(db_info["path"]):
            file_size = os.path.getsize(db_info["path"])
            db_info["size_mb"] = round(file_size / (1024 * 1024), 2)
            db_info["exists"] = True
        else:
            db_info["exists"] = False

        return db_info


# Create singleton instance
db_manager_instance = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager_instance