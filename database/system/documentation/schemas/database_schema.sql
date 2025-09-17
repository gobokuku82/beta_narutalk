-- Database Schema SQL Creation Script
-- Generated from existing SQLite databases
-- Total: 5 databases, 6 tables

-- =====================================================
-- Database: hr_data.db
-- Path: database/hr_information/hr_data.db
-- =====================================================

-- Drop tables if exist (for clean recreation)
DROP TABLE IF EXISTS 인사자료;
DROP TABLE IF EXISTS 지점연락처;

-- Table: 인사자료 (Employee Information)
CREATE TABLE 인사자료 (
    사번 TEXT PRIMARY KEY,
    성명 TEXT NOT NULL,
    본부 TEXT,
    직급 TEXT,
    부서 TEXT,
    지점 TEXT,
    연락처 TEXT,
    월평균사용예산 REAL,
    최근_평가 TEXT,
    기본급 INTEGER,  -- Changed from TEXT to INTEGER
    성과급 INTEGER,  -- Changed from TEXT to INTEGER
    책임업무 TEXT
);

-- Table: 지점연락처 (Branch Contacts)
CREATE TABLE 지점연락처 (
    본부 TEXT,
    부서 TEXT,
    지점 TEXT NOT NULL,
    지점_연락처 TEXT,
    PRIMARY KEY (본부, 부서, 지점)
);

-- =====================================================
-- Database: sales_performance_db.db
-- Path: database/sales_performance_db/sales_performance_db.db
-- =====================================================

DROP TABLE IF EXISTS sales_performance;

-- Table: sales_performance (Monthly Sales Performance)
CREATE TABLE sales_performance (
    사번 TEXT NOT NULL,
    담당자 TEXT NOT NULL,
    거래처ID TEXT NOT NULL,
    품목 TEXT NOT NULL,
    -- Monthly columns from 2022-12 to 2024-11
    "202212" INTEGER DEFAULT 0,
    "202301" INTEGER DEFAULT 0,
    "202302" INTEGER DEFAULT 0,
    "202303" INTEGER DEFAULT 0,
    "202304" INTEGER DEFAULT 0,
    "202305" INTEGER DEFAULT 0,
    "202306" INTEGER DEFAULT 0,
    "202307" INTEGER DEFAULT 0,
    "202308" INTEGER DEFAULT 0,
    "202309" INTEGER DEFAULT 0,
    "202310" INTEGER DEFAULT 0,
    "202311" INTEGER DEFAULT 0,
    "202312" INTEGER DEFAULT 0,
    "202401" INTEGER DEFAULT 0,
    "202402" INTEGER DEFAULT 0,
    "202403" INTEGER DEFAULT 0,
    "202404" INTEGER DEFAULT 0,
    "202405" INTEGER DEFAULT 0,
    "202406" INTEGER DEFAULT 0,
    "202407" INTEGER DEFAULT 0,
    "202408" INTEGER DEFAULT 0,
    "202409" INTEGER DEFAULT 0,
    "202410" INTEGER DEFAULT 0,
    "202411" INTEGER DEFAULT 0,
    PRIMARY KEY (사번, 거래처ID, 품목),
    FOREIGN KEY (사번) REFERENCES 인사자료(사번),
    FOREIGN KEY (거래처ID) REFERENCES 거래처정보(ID)
);

-- Create indexes for performance optimization
CREATE INDEX idx_sales_performance_사번 ON sales_performance(사번);
CREATE INDEX idx_sales_performance_거래처ID ON sales_performance(거래처ID);
CREATE INDEX idx_sales_performance_담당자 ON sales_performance(담당자);

-- =====================================================
-- Database: clients_db.db
-- Path: database/sales_performance_db/clients_db.db
-- =====================================================

DROP TABLE IF EXISTS 거래처자료;

-- Table: 거래처자료 (Client Transaction Data)
CREATE TABLE 거래처자료 (
    거래처ID TEXT NOT NULL,
    월 INTEGER NOT NULL,  -- YYYYMM format
    매출 INTEGER DEFAULT 0,
    월방문횟수 INTEGER DEFAULT 0,
    사용_예산 INTEGER DEFAULT 0,
    총환자수 INTEGER DEFAULT 0,
    담당자 TEXT,
    PRIMARY KEY (거래처ID, 월),
    FOREIGN KEY (거래처ID) REFERENCES 거래처정보(ID),
    FOREIGN KEY (담당자) REFERENCES 인사자료(성명)
);

-- Create indexes for query optimization
CREATE INDEX idx_거래처자료_거래처ID ON 거래처자료(거래처ID);
CREATE INDEX idx_거래처자료_월 ON 거래처자료(월);
CREATE INDEX idx_거래처자료_담당자 ON 거래처자료(담당자);

-- =====================================================
-- Database: sales_target_db.db
-- Path: database/sales_performance_db/sales_target_db.db
-- =====================================================

DROP TABLE IF EXISTS 지점별목표;

-- Table: 지점별목표 (Branch Sales Targets)
CREATE TABLE 지점별목표 (
    지점 TEXT NOT NULL,
    담당자 TEXT NOT NULL,
    -- Monthly target columns from 2023-12 to 2024-11
    "202312" INTEGER DEFAULT 0,
    "202401" INTEGER DEFAULT 0,
    "202402" INTEGER DEFAULT 0,
    "202403" INTEGER DEFAULT 0,
    "202404" INTEGER DEFAULT 0,
    "202405" INTEGER DEFAULT 0,
    "202406" INTEGER DEFAULT 0,
    "202407" INTEGER DEFAULT 0,
    "202408" INTEGER DEFAULT 0,
    "202409" INTEGER DEFAULT 0,
    "202410" INTEGER DEFAULT 0,
    "202411" INTEGER DEFAULT 0,
    PRIMARY KEY (지점, 담당자),
    FOREIGN KEY (지점) REFERENCES 지점연락처(지점),
    FOREIGN KEY (담당자) REFERENCES 인사자료(성명)
);

-- =====================================================
-- Database: clients_info.db
-- Path: database/sales_performance_db/clients_info.db
-- =====================================================

DROP TABLE IF EXISTS 거래처정보;

-- Table: 거래처정보 (Client Master Information)
CREATE TABLE 거래처정보 (
    ID TEXT PRIMARY KEY,
    원장명 TEXT NOT NULL,
    지역구 TEXT,
    병원연락처 TEXT
);

-- Create index for region-based queries
CREATE INDEX idx_거래처정보_지역구 ON 거래처정보(지역구);

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- View: Employee Performance Summary
CREATE VIEW IF NOT EXISTS 직원별실적요약 AS
SELECT
    sp.사번,
    sp.담당자,
    COUNT(DISTINCT sp.거래처ID) as 관리거래처수,
    SUM(sp."202401" + sp."202402" + sp."202403" +
        sp."202404" + sp."202405" + sp."202406" +
        sp."202407" + sp."202408" + sp."202409" +
        sp."202410" + sp."202411") as 연간총매출_2024
FROM sales_performance sp
GROUP BY sp.사번, sp.담당자;

-- View: Client Summary with Details
CREATE VIEW IF NOT EXISTS 거래처상세정보 AS
SELECT
    ci.ID,
    ci.원장명,
    ci.지역구,
    ci.병원연락처,
    cd.월,
    cd.매출,
    cd.월방문횟수,
    cd.사용_예산,
    cd.총환자수,
    cd.담당자
FROM 거래처정보 ci
LEFT JOIN 거래처자료 cd ON ci.ID = cd.거래처ID;

-- View: Branch Performance vs Target
CREATE VIEW IF NOT EXISTS 지점실적대목표 AS
SELECT
    st.지점,
    st.담당자,
    st."202411" as 목표_202411,
    COALESCE(SUM(sp."202411"), 0) as 실적_202411,
    CASE
        WHEN st."202411" > 0
        THEN ROUND(COALESCE(SUM(sp."202411"), 0) * 100.0 / st."202411", 2)
        ELSE 0
    END as 달성률
FROM 지점별목표 st
LEFT JOIN sales_performance sp ON st.담당자 = sp.담당자
GROUP BY st.지점, st.담당자, st."202411";

-- =====================================================
-- Triggers for Data Integrity
-- =====================================================

-- Trigger: Validate Employee ID on Sales Performance Insert
CREATE TRIGGER IF NOT EXISTS validate_employee_on_sales_insert
BEFORE INSERT ON sales_performance
BEGIN
    SELECT CASE
        WHEN NEW.사번 NOT IN (SELECT 사번 FROM 인사자료)
        THEN RAISE(ABORT, 'Invalid employee ID')
    END;
END;

-- Trigger: Validate Client ID on Transaction Insert
CREATE TRIGGER IF NOT EXISTS validate_client_on_transaction_insert
BEFORE INSERT ON 거래처자료
BEGIN
    SELECT CASE
        WHEN NEW.거래처ID NOT IN (SELECT ID FROM 거래처정보)
        THEN RAISE(ABORT, 'Invalid client ID')
    END;
END;

-- =====================================================
-- Sample Queries
-- =====================================================

-- Query 1: Get employee sales performance for specific month
-- SELECT
--     sp.담당자,
--     sp.거래처ID,
--     ci.원장명,
--     sp."202411" as 매출_202411
-- FROM sales_performance sp
-- JOIN 거래처정보 ci ON sp.거래처ID = ci.ID
-- WHERE sp."202411" > 0
-- ORDER BY sp."202411" DESC;

-- Query 2: Monthly performance trend for a specific employee
-- SELECT
--     '2024-01' as 월, "202401" as 매출 FROM sales_performance WHERE 사번 = ?
-- UNION SELECT '2024-02', "202402" FROM sales_performance WHERE 사번 = ?
-- UNION SELECT '2024-03', "202403" FROM sales_performance WHERE 사번 = ?
-- -- ... continue for all months

-- Query 3: Branch target achievement rate
-- SELECT
--     지점,
--     담당자,
--     목표_202411,
--     실적_202411,
--     달성률
-- FROM 지점실적대목표
-- ORDER BY 달성률 DESC;