import pytest

from agent.nodes.guardrail import validate_sql


@pytest.mark.parametrize(
    "sql, expected_safe",
    [
        # --- Safe SELECT queries ---
        ("SELECT * FROM fact_pnl", True),
        ("select mes_ref, ebitda_brl from fact_pnl where mes_ref = '2024-01'", True),
        (
            "SELECT p.mes_ref, c.nome FROM fact_pnl p "
            "JOIN dim_centro_custo c ON p.centro_custo_id = c.id",
            True,
        ),
        (
            "SELECT t.trimestre, SUM(p.ebitda_brl) FROM fact_pnl p "
            "JOIN dim_tempo t ON p.mes_ref = t.mes_ref GROUP BY t.trimestre",
            True,
        ),
        # --- DML mutations — must be blocked ---
        ("DELETE FROM fact_pnl", False),
        ("UPDATE fact_pnl SET ebitda_brl = 0", False),
        ("INSERT INTO fact_pnl VALUES (1, '2024-01', 100)", False),
        ("MERGE fact_pnl USING staging ON ...", False),
        # --- DDL — must be blocked ---
        ("DROP TABLE fact_pnl", False),
        ("CREATE TABLE hack (id INT)", False),
        ("ALTER TABLE fact_pnl ADD x INT", False),
        ("TRUNCATE TABLE fact_pnl", False),
        # --- Procedure execution ---
        ("EXEC sp_who", False),
        ("EXECUTE sp_helptext 'fact_pnl'", False),
        ("SELECT * FROM OPENROWSET('SQLNCLI', 'server=.;', 'SELECT 1')", False),
        ("SELECT * FROM sp_executesql", False),
        # --- Extended stored procedures ---
        ("xp_cmdshell 'whoami'", False),
        ("EXEC xp_fixeddrives", False),
        # --- Stacked queries ---
        ("SELECT 1; DROP TABLE fact_pnl", False),
        ("SELECT mes_ref FROM fact_pnl; SELECT * FROM dim_tempo", False),
        # --- Obfuscation via comments ---
        ("/* comment */ DELETE FROM fact_pnl", False),
        ("SELECT 1 -- comment\n; DROP TABLE fact_pnl", False),
        # --- Mixed-case obfuscation ---
        ("dElEtE FROM fact_pnl", False),
        ("DrOp TABLE fact_pnl", False),
        ("ExEc sp_who", False),
    ],
)
def test_validate_sql(sql: str, expected_safe: bool) -> None:
    is_safe, _ = validate_sql(sql)
    assert is_safe == expected_safe


def test_returns_non_empty_reason_on_failure() -> None:
    is_safe, reason = validate_sql("DELETE FROM fact_pnl")
    assert not is_safe
    assert reason != ""


def test_returns_empty_reason_on_success() -> None:
    is_safe, reason = validate_sql("SELECT * FROM fact_pnl")
    assert is_safe
    assert reason == ""


def test_blocked_keyword_inside_string_literal_is_still_rejected() -> None:
    # The guardrail is conservative: if the keyword appears anywhere after
    # comment stripping, the query is rejected. Safe for a read-only BI agent.
    is_safe, _ = validate_sql("SELECT 'DROP TABLE' AS label FROM fact_pnl")
    assert not is_safe
