from pathlib import Path
import re
import pytest

MIGRATION_PATH = Path(__file__).resolve().parent.parent / "migrations" / "001_initial_schema.sql"


@pytest.fixture(scope="module")
def sql_content() -> str:
    assert MIGRATION_PATH.exists(), f"Migration file not found at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_migration_file_exists(sql_content: str):
    """Verify that 001_initial_schema.sql exists and is non-empty."""
    assert len(sql_content.strip()) > 0


def test_all_required_tables_created(sql_content: str):
    """Verify all 6 core tables are created."""
    required_tables = [
        "profiles",
        "notices",
        "notice_pages",
        "notice_chunks",
        "notice_relationships",
        "error_reports",
    ]
    for table in required_tables:
        pattern = rf"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+{table}\b"
        assert re.search(pattern, sql_content, re.IGNORECASE), f"Missing CREATE TABLE for {table}"


def test_profiles_table_structure(sql_content: str):
    """Verify profiles table has auth.users reference and role check."""
    assert re.search(r"REFERENCES\s+auth\.users\s*\(\s*id\s*\)", sql_content, re.IGNORECASE)
    assert re.search(r"role\s+text\s+NOT\s+NULL\s+CHECK\s*\(\s*role\s+IN\s*\(\s*'uploader'\s*,\s*'admin'\s*\)\s*\)", sql_content, re.IGNORECASE)
    assert re.search(r"full_name\s+text", sql_content, re.IGNORECASE)
    assert re.search(r"created_at\s+timestamptz", sql_content, re.IGNORECASE)


def test_notices_table_columns(sql_content: str):
    """Verify notices table contains all required columns."""
    required_columns = [
        "id",
        "title",
        "notice_date",
        "deadline_date",
        "audience",
        "category",
        "summary",
        "storage_path",
        "processing_status",
        "publication_status",
        "review_reasons",
        "created_at",
        "updated_at",
    ]
    for col in required_columns:
        pattern = rf"\b{col}\b"
        assert re.search(pattern, sql_content, re.IGNORECASE), f"Missing column {col} in notices"

    # Verify audience enum/values
    assert re.search(r"'student',\s*'faculty',\s*'staff',\s*'all',\s*'unspecified'", sql_content)
    # Verify processing status values
    assert re.search(r"'pending',\s*'processing',\s*'completed',\s*'failed'", sql_content)
    # Verify publication status values
    assert re.search(r"'held',\s*'published',\s*'withdrawn'", sql_content)
    # Verify storage path is unique
    assert re.search(r"storage_path\s+text\s+NOT\s+NULL\s+UNIQUE", sql_content, re.IGNORECASE)
    # Verify review_reasons is jsonb
    assert re.search(r"review_reasons\s+jsonb", sql_content, re.IGNORECASE)


def test_notice_pages_structure(sql_content: str):
    """Verify notice_pages table columns and constraints."""
    required_columns = ["notice_id", "page_number", "extracted_text", "is_scanned", "created_at"]
    for col in required_columns:
        assert re.search(rf"\b{col}\b", sql_content, re.IGNORECASE), f"Missing column {col} in notice_pages"
    assert re.search(r"REFERENCES\s+notices\s*\(\s*id\s*\)\s+ON\s+DELETE\s+CASCADE", sql_content, re.IGNORECASE)
    assert re.search(r"is_scanned\s+boolean", sql_content, re.IGNORECASE)


def test_notice_chunks_structure(sql_content: str):
    """Verify notice_chunks table columns including search_vector tsvector."""
    required_columns = ["notice_id", "page_number", "chunk_text", "search_vector"]
    for col in required_columns:
        assert re.search(rf"\b{col}\b", sql_content, re.IGNORECASE), f"Missing column {col} in notice_chunks"
    assert re.search(r"search_vector\s+tsvector\s+GENERATED\s+ALWAYS\s+AS", sql_content, re.IGNORECASE)


def test_notice_relationships_and_error_reports(sql_content: str):
    """Verify notice_relationships and error_reports tables."""
    assert re.search(r"earlier_id\s+uuid\s+NOT\s+NULL\s+REFERENCES\s+notices\s*\(\s*id\s*\)", sql_content, re.IGNORECASE)
    assert re.search(r"later_id\s+uuid\s+NOT\s+NULL\s+REFERENCES\s+notices\s*\(\s*id\s*\)", sql_content, re.IGNORECASE)
    assert re.search(r"relation\s+relation_type", sql_content, re.IGNORECASE)
    assert re.search(r"issue_type\s+text\s+NOT\s+NULL", sql_content, re.IGNORECASE)
    assert re.search(r"status\s+report_status", sql_content, re.IGNORECASE)


def test_critical_security_rls_on_all_tables(sql_content: str):
    """Verify ALTER TABLE ... ENABLE ROW LEVEL SECURITY is executed for every table."""
    tables = [
        "profiles",
        "notices",
        "notice_pages",
        "notice_chunks",
        "notice_relationships",
        "error_reports",
    ]
    for table in tables:
        pattern = rf"ALTER\s+TABLE\s+{table}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\s*;"
        assert re.search(pattern, sql_content, re.IGNORECASE), f"Missing ENABLE RLS on table {table}"


def test_critical_security_revocations(sql_content: str):
    """Verify REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated is present."""
    pattern = r"REVOKE\s+ALL\s+ON\s+ALL\s+TABLES\s+IN\s+SCHEMA\s+public\s+FROM\s+anon\s*,\s*authenticated\s*;"
    assert re.search(pattern, sql_content, re.IGNORECASE), "Missing REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated"


def test_sql_delimiters_balanced(sql_content: str):
    """Verify parentheses and single quotes are balanced in the SQL script."""
    # Strip comments
    lines = [
        re.sub(r"--.*$", "", line)
        for line in sql_content.splitlines()
    ]
    cleaned = "\n".join(lines)

    open_parens = cleaned.count("(")
    close_parens = cleaned.count(")")
    assert open_parens == close_parens, f"Mismatched parentheses: {open_parens} != {close_parens}"

    # Verify single quote parity (handling escaped double single quotes '')
    escaped_single_quotes = cleaned.count("''")
    total_single_quotes = cleaned.count("'")
    raw_single_quotes = total_single_quotes - (escaped_single_quotes * 2)
    assert raw_single_quotes % 2 == 0, f"Mismatched single quotes: {raw_single_quotes}"

