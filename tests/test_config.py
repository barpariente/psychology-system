from common.config import load_settings


def test_defaults_when_env_is_empty():
    settings = load_settings({})
    assert settings.mongo_db == "psychology_system"
    assert settings.fake_ai is False
    assert settings.max_retries == 3
    assert settings.openai_api_key is None


def test_reads_values_from_env():
    settings = load_settings({"FAKE_AI": "TRUE", "MAX_RETRIES": "5", "MONGO_DB": "other"})
    assert settings.fake_ai is True
    assert settings.max_retries == 5
    assert settings.mongo_db == "other"
