import os
import subprocess
import pytest
from hearthstone.cardxml import load_dbf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DATA_DIR = os.path.join(BASE_DIR, "testdata")
LOG_DATA_GIT = "https://github.com/HearthSim/hsreplay-test-data"
FIXTURE_SUITE = os.path.join(LOG_DATA_DIR, "archetype-fixtures")


def pytest_configure(config):
	if not os.path.exists(LOG_DATA_DIR):
		proc = subprocess.Popen(["git", "clone", LOG_DATA_GIT, LOG_DATA_DIR])
	else:
		os.chdir(LOG_DATA_DIR)
		proc = subprocess.Popen(["git", "pull"])
	assert proc.wait() == 0


@pytest.fixture(scope="session")
def dbf_db():
	db, _ = load_dbf()
	return db
