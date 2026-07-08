from pathlib import Path

from deep_research_team.settings import (
    AGENTS_CONFIG,
    ANALYST_MAX_ITER,
    ANALYST_MAX_TOKENS,
    CACHE_DIR,
    CACHE_TTL,
    DB_PATH,
    ENV_VARS,
    LLM_PROVIDER_DEFAULT,
    LOG_FORMAT,
    OUTPUT_DIR,
    REPORT_FILE,
    RESEARCHER_MAX_ITER,
    RESEARCHER_MAX_TOKENS,
    SERPER_TIMEOUT,
    TASKS_CONFIG,
    URL_VALIDATE_TIMEOUT,
    WRITER_MAX_TOKENS,
    setup_logging,
)


def test_settings_have_expected_values() -> None:
    assert RESEARCHER_MAX_TOKENS == 4096
    assert ANALYST_MAX_TOKENS == 8192
    assert WRITER_MAX_TOKENS == 16384
    assert RESEARCHER_MAX_ITER == 8
    assert ANALYST_MAX_ITER == 3
    assert SERPER_TIMEOUT == 10
    assert URL_VALIDATE_TIMEOUT == 5
    assert CACHE_TTL == 86400
    assert LLM_PROVIDER_DEFAULT == "mimo"
    assert AGENTS_CONFIG == "config/agents.yaml"
    assert TASKS_CONFIG == "config/tasks.yaml"


def test_settings_paths_are_paths() -> None:
    assert isinstance(OUTPUT_DIR, Path)
    assert isinstance(CACHE_DIR, Path)
    assert isinstance(DB_PATH, Path)
    assert isinstance(REPORT_FILE, Path)


def test_settings_paths_relative_to_project_root() -> None:
    from deep_research_team.settings import PROJECT_ROOT
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT == Path(__file__).resolve().parent.parent
    assert OUTPUT_DIR == PROJECT_ROOT / "output"
    assert CACHE_DIR == PROJECT_ROOT / "output" / "cache"
    assert DB_PATH == PROJECT_ROOT / "output" / "history.db"


def test_env_vars_list() -> None:
    assert "GROQ_API_KEY" in ENV_VARS
    assert "SERPER_API_KEY" in ENV_VARS
    assert "DEEPSEEK_API_KEY" in ENV_VARS
    assert "MIMO_API_KEY" in ENV_VARS
    assert "MIMO_BASE_URL" in ENV_VARS
    assert "MIMO_THINKING" in ENV_VARS
    assert "GEMINI_API_KEY" in ENV_VARS
    assert "OMNIROUTE_API_KEY" in ENV_VARS
    assert "OMNIROUTE_BASE_URL" in ENV_VARS
    assert "OMNIROUTE_MODEL" in ENV_VARS


def test_log_format() -> None:
    assert "%(asctime)s" in LOG_FORMAT
    assert "%(levelname)s" in LOG_FORMAT


def test_setup_logging() -> None:
    logger = setup_logging("test_logger")
    assert logger.name == "test_logger"
    assert logger.level != 0
