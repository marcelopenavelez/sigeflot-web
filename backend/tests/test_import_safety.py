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


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_local_qa_import_is_allowed_only_on_localhost(host):
    validate_target("sigeflot_local_qa", False, OFFICIAL, {"APP_ENV": "development", "SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host=host, local_qa=True)


@pytest.mark.parametrize("database", ["sigeflot", "sigeflot_test"])
def test_local_qa_rejects_other_databases(database):
    with pytest.raises(SystemExit, match="requires sigeflot_local_qa"):
        validate_target(database, False, OFFICIAL, {"SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host="localhost", local_qa=True)


@pytest.mark.parametrize("host", ["railway.internal", "db.example.com"])
def test_local_qa_rejects_remote_hosts(host):
    with pytest.raises(SystemExit, match="requires localhost"):
        validate_target("sigeflot_local_qa", False, OFFICIAL, {"SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host=host, local_qa=True)


def test_local_qa_rejects_production_confirmation_and_filename_errors():
    with pytest.raises(SystemExit, match="forbidden in production"):
        validate_target("sigeflot_local_qa", False, OFFICIAL, {"APP_ENV": "production", "SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host="localhost", local_qa=True)
    with pytest.raises(SystemExit, match="confirmation"):
        validate_target("sigeflot_local_qa", False, OFFICIAL, {}, host="localhost", local_qa=True)
    with pytest.raises(SystemExit, match="official source"):
        validate_target("sigeflot_local_qa", False, "other.xlsx", {"SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host="localhost", local_qa=True)
    with pytest.raises(SystemExit, match="cannot be combined"):
        validate_target("sigeflot_local_qa", True, OFFICIAL, {"SIGEFLOT_LOCAL_QA_IMPORT_CONFIRMATION": "IMPORT_SIGEFLOT_LOCAL_QA_2026"}, host="localhost", local_qa=True)
