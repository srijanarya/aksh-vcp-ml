"""
Database Utilities - SQLite operations for ML agents

Provides reusable database connection, query execution, and bulk insert operations.
All functions are thread-safe and use context managers for proper resource cleanup.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection(db_path: str, timeout: float = 30.0):
    """
    Get a SQLite database connection with automatic cleanup.

    Args:
        db_path: Absolute path to SQLite database file
        timeout: Connection timeout in seconds (default: 30.0)

    Yields:
        sqlite3.Connection: Database connection

    Raises:
        sqlite3.OperationalError: If database cannot be opened

    Example:
        with get_db_connection("/path/to/db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies")
    """
    # Ensure parent directory exists
    db_path_obj = Path(db_path)
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=timeout)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.debug(f"Connected to database: {db_path}")
        yield conn
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to connect to {db_path}: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug(f"Closed connection to {db_path}")


def execute_query(
    db_path: str,
    query: str,
    params: Optional[Tuple] = None,
    fetch_one: bool = False,
    commit: bool = False
) -> Optional[List[sqlite3.Row]]:
    """
    Execute a SQL query with optional parameters.

    Args:
        db_path: Absolute path to SQLite database
        query: SQL query string (supports ? placeholders)
        params: Query parameters tuple (default: None)
        fetch_one: If True, return single row; if False, return all rows
        commit: If True, commit transaction after execution

    Returns:
        List of sqlite3.Row objects, single Row, or None for INSERT/UPDATE

    Raises:
        sqlite3.Error: If query execution fails

    Example:
        # SELECT query
        rows = execute_query(
            "/path/to/db.db",
            "SELECT * FROM companies WHERE isin = ?",
            params=("INE123A01234",),
            fetch_one=False
        )

        # INSERT query
        execute_query(
            "/path/to/db.db",
            "INSERT INTO companies (name, isin) VALUES (?, ?)",
            params=("TCS", "INE123A01234"),
            commit=True
        )
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()
                logger.debug(f"Committed transaction: {query[:50]}...")
                return None

            if fetch_one:
                result = cursor.fetchone()
                logger.debug(f"Fetched 1 row from query: {query[:50]}...")
                return result
            else:
                results = cursor.fetchall()
                logger.debug(f"Fetched {len(results)} rows from query: {query[:50]}...")
                return results

        except sqlite3.Error as e:
            logger.error(f"Query failed: {query[:100]}... Error: {e}")
            raise


def bulk_insert(
    db_path: str,
    table_name: str,
    columns: List[str],
    data: List[Tuple],
    batch_size: int = 1000,
    on_conflict: str = "IGNORE"
) -> int:
    """
    Bulk insert data into a table with batching.

    Args:
        db_path: Absolute path to SQLite database
        table_name: Target table name
        columns: List of column names
        data: List of tuples matching column order
        batch_size: Number of rows per batch (default: 1000)
        on_conflict: Conflict resolution strategy: "IGNORE" or "REPLACE"

    Returns:
        Total number of rows inserted

    Raises:
        ValueError: If columns/data mismatch or invalid conflict strategy
        sqlite3.Error: If insert fails

    Example:
        data = [
            ("TCS", "INE123A01234", 3500.0),
            ("Infosys", "INE009A01021", 1450.0)
        ]
        rows_inserted = bulk_insert(
            "/path/to/db.db",
            table_name="companies",
            columns=["name", "isin", "price"],
            data=data,
            batch_size=1000,
            on_conflict="REPLACE"
        )
    """
    if not data:
        logger.warning("No data provided for bulk insert")
        return 0

    if on_conflict not in ("IGNORE", "REPLACE"):
        raise ValueError(f"Invalid on_conflict: {on_conflict}. Must be 'IGNORE' or 'REPLACE'")

    # Validate data structure
    expected_cols = len(columns)
    for i, row in enumerate(data[:10]):  # Check first 10 rows
        if len(row) != expected_cols:
            raise ValueError(
                f"Row {i} has {len(row)} values but {expected_cols} columns specified"
            )

    # Build INSERT query
    placeholders = ", ".join(["?"] * len(columns))
    columns_str = ", ".join(columns)
    query = f"INSERT OR {on_conflict} INTO {table_name} ({columns_str}) VALUES ({placeholders})"

    total_inserted = 0

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            try:
                cursor.executemany(query, batch)
                conn.commit()

                rows_affected = cursor.rowcount
                total_inserted += rows_affected

                logger.info(
                    f"Batch {i // batch_size + 1}: Inserted {rows_affected} rows "
                    f"into {table_name} ({i + len(batch)}/{len(data)} total)"
                )

            except sqlite3.Error as e:
                logger.error(f"Batch insert failed at row {i}: {e}")
                conn.rollback()
                raise

    logger.info(f"Bulk insert complete: {total_inserted} rows inserted into {table_name}")
    return total_inserted


def create_table_if_not_exists(
    db_path: str,
    table_name: str,
    schema: Dict[str, str],
    primary_key: Optional[str] = None,
    indexes: Optional[List[str]] = None
) -> bool:
    """
    Create a table if it doesn't already exist.

    Args:
        db_path: Absolute path to SQLite database
        table_name: Name of table to create
        schema: Dict mapping column names to SQLite types
                Example: {"company_name": "TEXT", "isin": "TEXT", "price": "REAL"}
        primary_key: Column name to use as PRIMARY KEY (optional)
        indexes: List of column names to create indexes on (optional)

    Returns:
        True if table was created, False if already exists

    Raises:
        sqlite3.Error: If table creation fails

    Example:
        created = create_table_if_not_exists(
            "/path/to/db.db",
            table_name="companies",
            schema={
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "isin": "TEXT UNIQUE",
                "price": "REAL",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            indexes=["isin", "name"]
        )
    """
    # Check if table exists
    check_query = f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(check_query, (table_name,))

        if cursor.fetchone():
            logger.debug(f"Table {table_name} already exists")
            return False

        # Build CREATE TABLE statement
        columns_def = []
        for col_name, col_type in schema.items():
            col_def = f"{col_name} {col_type}"
            if primary_key and col_name == primary_key:
                col_def += " PRIMARY KEY"
            columns_def.append(col_def)

        create_query = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns_def)}
            )
        """

        cursor.execute(create_query)
        conn.commit()
        logger.info(f"Created table: {table_name}")

        # Create indexes
        if indexes:
            for index_col in indexes:
                index_name = f"idx_{table_name}_{index_col}"
                index_query = f"CREATE INDEX {index_name} ON {table_name} ({index_col})"
                cursor.execute(index_query)
                logger.info(f"Created index: {index_name}")
            conn.commit()

        return True
