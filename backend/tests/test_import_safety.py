from app.scripts.import_official_data import validate_target
import pytest

OFFICIAL = "Control_Flota_DIRESA.xlsx"

def test_migration_test_apply_is_allowed():
    validate_target("sigeflot_migration_test", False, OFFICIAL, {})

def test_non_test_requires_production_flag():
    with pytest.raises(SystemExit, match="require --production"):
        validate_target("sigeflot", False, OFFICIAL, {})

def test_production_requires_environment_authorization():
    with pytest.raises(SystemExit, match="APP_ENV"):
        validate_target("sigeflot", True, OFFICIAL, {})

def test_production_requires_correct_confirmation():
    with pytest.raises(SystemExit, match="confirmation"):
        validate_target("sigeflot", True, OFFICIAL, {"APP_ENV":"production", "SIGEFLOT_ALLOW_PRODUCTION_IMPORT":"true"})

def test_production_requires_official_filename():
    with pytest.raises(SystemExit, match="official source"):
        validate_target("sigeflot", True, "other.xlsx", {"APP_ENV":"production", "SIGEFLOT_ALLOW_PRODUCTION_IMPORT":"true", "SIGEFLOT_IMPORT_CONFIRMATION":"CONTROL_FLOTA_DIRESA_2026"})
