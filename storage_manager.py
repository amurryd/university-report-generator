# file: storage_manager.py
"""
Storage Manager Module - PostgreSQL Layer for LED IAPT 4.1
----------------------------------------------------------
Provides persistent storage for reports, data, and metadata

Features:
- Report versioning and history
- Data source tracking
- Metadata persistence
- Query and analytics
- Backup and restore
- Report comparison
"""

import pandas as pd
import psycopg2
from psycopg2 import sql, extras
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib


class StorageManager:
    """
    Manages PostgreSQL storage for LED IAPT 4.1 reports and data
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "led_reports",
        user: str = None,
        password: str = None,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Initialize PostgreSQL connection pool
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        
        # Create connection pool
        try:
            self.pool = SimpleConnectionPool(
                min_connections,
                max_connections,
                **self.connection_params
            )
            print(f"✓ PostgreSQL connection pool initialized")
            print(f"  Host: {host}:{port}")
            print(f"  Database: {database}")
            
            # Initialize schema
            self._initialize_schema()
            
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    def __del__(self):
        """Close all connections when object is destroyed"""
        if hasattr(self, 'pool') and self.pool:
            self.pool.closeall()
    
    # ========================================================================
    # SCHEMA INITIALIZATION
    # ========================================================================
    
    def _initialize_schema(self):
        """Create database schema if not exists"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Enable UUID extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
                
                # Reports table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id SERIAL PRIMARY KEY,
                        uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
                        report_type VARCHAR(100) NOT NULL,
                        section VARCHAR(50),
                        title TEXT,
                        content TEXT NOT NULL,
                        content_hash VARCHAR(64) UNIQUE,
                        word_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version INTEGER DEFAULT 1,
                        parent_id INTEGER REFERENCES reports(id),
                        status VARCHAR(50) DEFAULT 'draft',
                        metadata JSONB
                    );
                """)
                
                # Data sources table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS data_sources (
                        id SERIAL PRIMARY KEY,
                        source_url TEXT NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        source_hash VARCHAR(64) UNIQUE,
                        row_count INTEGER,
                        column_count INTEGER,
                        columns JSONB,
                        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cached BOOLEAN DEFAULT FALSE,
                        metadata JSONB
                    );
                """)
                
                # Report-Data relationship table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS report_data_sources (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                        data_source_id INTEGER REFERENCES data_sources(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(report_id, data_source_id)
                    );
                """)
                
                # Validation results table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS validation_results (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                        is_valid BOOLEAN NOT NULL,
                        issues JSONB,
                        warnings JSONB,
                        validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    );
                """)
                
                # Token usage tracking
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS token_usage (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                        prompt_tokens INTEGER,
                        output_tokens INTEGER,
                        total_tokens INTEGER,
                        estimated_cost DECIMAL(10, 6),
                        model_name VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # User feedback table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_email VARCHAR(255)
                    );
                """)
                
                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_type 
                    ON reports(report_type);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_created 
                    ON reports(created_at);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_status 
                    ON reports(status);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_data_sources_url 
                    ON data_sources(source_url);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_validation_report 
                    ON validation_results(report_id);
                """)
                
                conn.commit()
                print("✓ Database schema initialized")
                
        except Exception as e:
            conn.rollback()
            print(f"❌ Schema initialization failed: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # REPORT MANAGEMENT
    # ========================================================================
    
    def save_report(
        self,
        content: str,
        report_type: str = "led_iapt_4.1",
        section: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "draft"
    ) -> int:
        """
        Save a report to the database
        
        Args:
            content: Report text content
            report_type: Type of report (e.g., "led_iapt_4.1")
            section: Section identifier (e.g., "section_3")
            title: Report title
            metadata: Additional metadata
            status: Report status (draft, final, archived)
            
        Returns:
            Report ID
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Calculate content hash for deduplication
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                # Count words
                word_count = len(content.split())
                
                # Check if identical report exists
                cur.execute(
                    "SELECT id FROM reports WHERE content_hash = %s",
                    (content_hash,)
                )
                existing = cur.fetchone()
                
                if existing:
                    print(f"⚠️ Identical report already exists (ID: {existing[0]})")
                    return existing[0]
                
                # Insert new report
                cur.execute("""
                    INSERT INTO reports 
                    (report_type, section, title, content, content_hash, 
                     word_count, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    report_type,
                    section,
                    title or f"{report_type} Report",
                    content,
                    content_hash,
                    word_count,
                    status,
                    json.dumps(metadata) if metadata else None
                ))
                
                report_id = cur.fetchone()[0]
                conn.commit()
                
                print(f"✓ Report saved (ID: {report_id})")
                return report_id
                
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to save report: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a report by ID
        
        Returns:
            Dictionary with report data or None
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, uuid, report_type, section, title, content,
                        word_count, created_at, updated_at, version,
                        status, metadata
                    FROM reports
                    WHERE id = %s
                """, (report_id,))
                
                result = cur.fetchone()
                
                if result:
                    return dict(result)
                return None
                
        finally:
            self.pool.putconn(conn)
    
    def list_reports(
        self,
        report_type: Optional[str] = None,
        section: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List reports with optional filters
        
        Returns:
            List of report summaries
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                # Build query dynamically
                query = """
                    SELECT 
                        id, uuid, report_type, section, title,
                        word_count, created_at, status
                    FROM reports
                    WHERE 1=1
                """
                params = []
                
                if report_type:
                    query += " AND report_type = %s"
                    params.append(report_type)
                
                if section:
                    query += " AND section = %s"
                    params.append(section)
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [dict(row) for row in results]
                
        finally:
            self.pool.putconn(conn)
    
    def update_report_status(self, report_id: int, status: str) -> bool:
        """Update report status (draft, final, archived)"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE reports 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status, report_id))
                
                conn.commit()
                return cur.rowcount > 0
                
        finally:
            self.pool.putconn(conn)
    
    def create_report_version(
        self,
        parent_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a new version of an existing report
        
        Returns:
            New version's report ID
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Get parent report info
                cur.execute("""
                    SELECT report_type, section, title, version
                    FROM reports WHERE id = %s
                """, (parent_id,))
                
                parent = cur.fetchone()
                if not parent:
                    raise ValueError(f"Parent report {parent_id} not found")
                
                report_type, section, title, parent_version = parent
                new_version = parent_version + 1
                
                # Create new version
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                word_count = len(content.split())
                
                cur.execute("""
                    INSERT INTO reports 
                    (report_type, section, title, content, content_hash,
                     word_count, version, parent_id, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    report_type, section, title, content, content_hash,
                    word_count, new_version, parent_id,
                    json.dumps(metadata) if metadata else None
                ))
                
                new_id = cur.fetchone()[0]
                conn.commit()
                
                print(f"✓ Created version {new_version} (ID: {new_id})")
                return new_id
                
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to create version: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    def get_report_versions(self, report_id: int) -> List[Dict[str, Any]]:
        """Get all versions of a report"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                # Get the base report or find the root parent
                cur.execute("""
                    WITH RECURSIVE version_tree AS (
                        SELECT id, parent_id FROM reports WHERE id = %s
                        UNION
                        SELECT r.id, r.parent_id 
                        FROM reports r
                        INNER JOIN version_tree vt ON r.id = vt.parent_id
                    )
                    SELECT MIN(id) as root_id FROM version_tree
                """, (report_id,))
                
                root_id = cur.fetchone()['root_id']
                
                # Get all versions from root
                cur.execute("""
                    WITH RECURSIVE versions AS (
                        SELECT id, parent_id, version, created_at, status
                        FROM reports WHERE id = %s
                        UNION
                        SELECT r.id, r.parent_id, r.version, r.created_at, r.status
                        FROM reports r
                        INNER JOIN versions v ON r.parent_id = v.id
                    )
                    SELECT * FROM versions ORDER BY version
                """, (root_id,))
                
                return [dict(row) for row in cur.fetchall()]
                
        finally:
            self.pool.putconn(conn)
    
    def delete_report(self, report_id: int) -> bool:
        """Delete a report (and all related data due to CASCADE)"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reports WHERE id = %s", (report_id,))
                conn.commit()
                
                deleted = cur.rowcount > 0
                if deleted:
                    print(f"✓ Report {report_id} deleted")
                return deleted
                
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # DATA SOURCE TRACKING
    # ========================================================================
    
    def track_data_source(
        self,
        source_url: str,
        source_type: str,
        row_count: int,
        column_count: int,
        columns: List[str],
        cached: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Track a data source that was used
        
        Returns:
            Data source ID
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                source_hash = hashlib.md5(source_url.encode()).hexdigest()
                
                # Check if already tracked recently (within 24 hours)
                cur.execute("""
                    SELECT id FROM data_sources 
                    WHERE source_hash = %s 
                    AND fetched_at > NOW() - INTERVAL '24 hours'
                """, (source_hash,))
                
                existing = cur.fetchone()
                if existing:
                    return existing[0]
                
                # Insert new tracking record
                cur.execute("""
                    INSERT INTO data_sources
                    (source_url, source_type, source_hash, row_count, 
                     column_count, columns, cached, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    source_url, source_type, source_hash, row_count,
                    column_count, json.dumps(columns), cached,
                    json.dumps(metadata) if metadata else None
                ))
                
                source_id = cur.fetchone()[0]
                conn.commit()
                return source_id
                
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to track data source: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    def link_report_to_sources(
        self,
        report_id: int,
        source_ids: List[int]
    ):
        """Link a report to its data sources"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for source_id in source_ids:
                    cur.execute("""
                        INSERT INTO report_data_sources (report_id, data_source_id)
                        VALUES (%s, %s)
                        ON CONFLICT (report_id, data_source_id) DO NOTHING
                    """, (report_id, source_id))
                
                conn.commit()
                print(f"✓ Linked report to {len(source_ids)} data source(s)")
                
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # VALIDATION TRACKING
    # ========================================================================
    
    def save_validation_results(
        self,
        report_id: int,
        is_valid: bool,
        issues: List[str],
        warnings: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Save validation results for a report"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO validation_results
                    (report_id, is_valid, issues, warnings, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    report_id, is_valid,
                    json.dumps(issues), json.dumps(warnings),
                    json.dumps(metadata) if metadata else None
                ))
                
                validation_id = cur.fetchone()[0]
                conn.commit()
                return validation_id
                
        finally:
            self.pool.putconn(conn)
    
    def get_validation_results(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get latest validation results for a report"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM validation_results
                    WHERE report_id = %s
                    ORDER BY validated_at DESC
                    LIMIT 1
                """, (report_id,))
                
                result = cur.fetchone()
                return dict(result) if result else None
                
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # TOKEN USAGE TRACKING
    # ========================================================================
    
    def track_token_usage(
        self,
        report_id: int,
        prompt_tokens: int,
        output_tokens: int,
        total_tokens: int,
        model_name: str,
        cost_per_million: float = 0.075
    ) -> int:
        """Track AI token usage for cost monitoring"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                estimated_cost = (total_tokens / 1_000_000) * cost_per_million
                
                cur.execute("""
                    INSERT INTO token_usage
                    (report_id, prompt_tokens, output_tokens, total_tokens,
                     estimated_cost, model_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    report_id, prompt_tokens, output_tokens, total_tokens,
                    estimated_cost, model_name
                ))
                
                usage_id = cur.fetchone()[0]
                conn.commit()
                return usage_id
                
        finally:
            self.pool.putconn(conn)
    
    def get_token_usage_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get token usage statistics for the past N days"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as report_count,
                        SUM(total_tokens) as total_tokens,
                        AVG(total_tokens) as avg_tokens_per_report,
                        SUM(estimated_cost) as total_cost,
                        AVG(estimated_cost) as avg_cost_per_report
                    FROM token_usage
                    WHERE created_at > NOW() - INTERVAL '%s days'
                """, (days,))
                
                return dict(cur.fetchone())
                
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about stored reports"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_reports,
                        COUNT(DISTINCT report_type) as report_types,
                        AVG(word_count) as avg_word_count,
                        MAX(word_count) as max_word_count,
                        COUNT(CASE WHEN status = 'final' THEN 1 END) as final_reports,
                        COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_reports
                    FROM reports
                """)
                
                return dict(cur.fetchone())
                
        finally:
            self.pool.putconn(conn)
    
    def search_reports(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search in report content"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, report_type, section, title, 
                        LEFT(content, 200) as excerpt,
                        created_at, status
                    FROM reports
                    WHERE 
                        content ILIKE %s OR
                        title ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (f'%{search_term}%', f'%{search_term}%', limit))
                
                return [dict(row) for row in cur.fetchall()]
                
        finally:
            self.pool.putconn(conn)
    
    # ========================================================================
    # FEEDBACK COLLECTION
    # ========================================================================
    
    def save_feedback(
        self,
        report_id: int,
        rating: int,
        comment: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> int:
        """Save user feedback for a report"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO feedback (report_id, rating, comment, user_email)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (report_id, rating, comment, user_email))
                
                feedback_id = cur.fetchone()[0]
                conn.commit()
                return feedback_id
                
        finally:
            self.pool.putconn(conn)
    
    def get_average_rating(self, report_type: Optional[str] = None) -> float:
        """Get average rating for reports"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                if report_type:
                    cur.execute("""
                        SELECT AVG(f.rating)
                        FROM feedback f
                        JOIN reports r ON f.report_id = r.id
                        WHERE r.report_type = %s
                    """, (report_type,))
                else:
                    cur.execute("SELECT AVG(rating) FROM feedback")
                
                result = cur.fetchone()[0]
                return float(result) if result else 0.0
                
        finally:
            self.pool.putconn(conn)


# For testing this module independently
if __name__ == "__main__":
    print("=" * 70)
    print("Storage Manager Module - PostgreSQL Layer")
    print("=" * 70)
    
    # Example usage (requires PostgreSQL running)
    try:
        storage = StorageManager(
            host="localhost",
            database="led_reports",
            user="your_user",
            password="your_password"
        )
        
        print("\n✓ Storage Manager initialized successfully")
        print("\nAvailable methods:")
        print("- save_report(): Save a new report")
        print("- get_report(): Retrieve a report")
        print("- list_reports(): List reports with filters")
        print("- create_report_version(): Version control")
        print("- track_data_source(): Track data sources")
        print("- save_validation_results(): Store validation")
        print("- track_token_usage(): Monitor AI costs")
        print("- get_report_statistics(): Analytics")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure PostgreSQL is running and configured correctly")
    
    print("=" * 70)
