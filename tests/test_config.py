import pytest
import tomlkit

from freakotp.config import Config


@pytest.fixture
def temp_config_path(tmp_path):
    return tmp_path / "config.toml"


def test_config_initialization(temp_config_path):
    config = Config(temp_config_path)
    assert config.config_path == temp_config_path
    assert config.copy_to_clipboard is True
    assert config.show_codes is False
    assert config.spinner_style == ""
    print(config)


def test_config_save_and_load(temp_config_path):
    config = Config(temp_config_path)
    config.copy_to_clipboard = True
    config.show_codes = True
    config.spinner_style = "◯◔◒◕●"
    config.save()

    config2 = Config.load(temp_config_path)
    assert config2.copy_to_clipboard is True
    assert config2.show_codes is True
    assert config2.spinner_style == "◯◔◒◕●"
    config2.copy_to_clipboard = False
    config2.show_codes = False
    config2.spinner_style = ""
    config2.save()

    config3 = Config.load(temp_config_path)
    assert config3.copy_to_clipboard is False
    assert config3.show_codes is False
    assert config3.spinner_style == ""


def test_config_file_format(temp_config_path):
    config = Config(temp_config_path)
    config.copy_to_clipboard = True
    config.show_codes = False
    config.spinner_style = ""
    config.save()

    with temp_config_path.open("r", encoding="utf-8") as f:
        content = tomlkit.parse(f.read())

    assert content["copy_to_clipboard"] is True
    assert content["show_codes"] is False
    assert content["spinner_style"] == ""
