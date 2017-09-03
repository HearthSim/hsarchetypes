import os
import subprocess
import pytest
from hearthstone.cardxml import load_dbf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DATA_DIR = os.path.join(BASE_DIR, "testdata")
LOG_DATA_GIT = "https://github.com/HearthSim/hsreplay-test-data"
FIXTURE_SUITE = os.path.join(LOG_DATA_DIR, "archetype-fixtures")
CLUSTERING_DATA = os.path.join(LOG_DATA_DIR, "clustering-data")


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


@pytest.fixture(scope="session")
def kft_control_warlock():
	return {
		42658: 2,
		1092: 2,
		42471: 2,
		43415: 1,
		1100: 2,
		42818: 1,
		48: 2,
		914: 2,
		1651: 2,
		950: 2,
		42743: 2,
		46103: 2,
		1019: 2,
		40541: 2,
		41566: 2,
		42783: 2
	}

@pytest.fixture(scope="session")
def kft_standard_warlock_signatures():
	return {
		132: {
			993: 0.6944109182062946, 42658: 0.16327406926005014, 1092: 0.0, 42471: 0.25, 38569: 0.6783956921362919,
			  138: 0.666465509237768, 46103: 0.1421177235168508, 1100: 0.25, 1037: 0.7852567078265713, 42743: 0.0,
			  48: 0.24767895274347787, 914: 0.1400635966948287, 1651: 0.19949401169807818, 950: 0.206445548231362,
			  43415: 0.25, 42818: 0.17689861665583512, 40541: 0.25, 41566: 0.18054266084857487
		},
		134: {
			1090: 1.0, 1092: 0.0, 997: 1.0, 42790: 1.0, 42442: 1.0, 41323: 1.0, 40465: 1.0, 211: 1.0, 38452: 1.0,
			  757: 0.9292484766418416, 38774: 1.0, 42743: 0.0, 1656: 0.8689911983750847, 763: 1.0, 45340: 1.0,
			  41418: 1.0, 42773: 1.0
			  },
		63: {
			42658: 0.25, 1092: 0.0, 42471: 0.25, 46103: 0.25, 1100: 0.25, 42818: 0.25, 42743: 0.0, 48: 0.25, 914: 0.25,
			 1651: 0.25, 950: 0.25, 43415: 0.25, 1019: 1.0, 40541: 0.25, 41566: 0.25, 42783: 1.0
		}
	}
