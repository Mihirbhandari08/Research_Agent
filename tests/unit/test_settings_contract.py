from app.config.settings import Settings


def test_settings_exposes_nested_contract():
    settings = Settings(
        app_env="development",
        log_level="DEBUG",
        api_host="127.0.0.1",
        api_port=9000,
        gemini_default_model="gemini/gemini-2.5-pro",
        gemini_fallback_model="gemini/gemini-2.0-flash",
        timeout_node_seconds=20.0,
        default_max_llm_calls=12,
        default_max_tool_calls=25,
        default_max_input_tokens=50000,
        default_max_output_tokens=15000,
        default_max_cost_usd=2.5,
        langsmith_project="demo-project",
        otel_service_name="demo-service",
    )

    assert settings.app.app_env == "development"
    assert settings.app.log_level == "DEBUG"
    assert settings.llm.gemini_default_model == "gemini/gemini-2.5-pro"
    assert settings.api.host == "127.0.0.1"
    assert settings.api.port == 9000
    assert settings.timeouts.node_seconds == 20.0
    assert settings.budgets.default_max_llm_calls == 12
    assert settings.budgets.default_max_tool_calls == 25
    assert settings.langsmith.project == "demo-project"
    assert settings.otel.service_name == "demo-service"
