import os
import subprocess

import pytest
from hearthstone.cardxml import load_dbf
from tests.utils import get_deck_from_deckstring


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DATA_DIR = os.path.join(BASE_DIR, "testdata")
LOG_DATA_GIT = "https://github.com/HearthSim/hsreplay-test-data"
FIXTURE_SUITE = os.path.join(LOG_DATA_DIR, "archetype-fixtures")
CLUSTERING_DATA = os.path.join(LOG_DATA_DIR, "clustering-data")
LABELED_CLUSTERS = os.path.join(LOG_DATA_DIR, "labeled-clusters")


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
			"signature_weights": {
				993: 0.6944109182062946, 42658: 0.16327406926005014, 1092: 0.0, 42471: 0.25, 38569: 0.6783956921362919,
				138: 0.666465509237768, 46103: 0.1421177235168508, 1100: 0.25, 1037: 0.7852567078265713, 42743: 0.0,
				48: 0.24767895274347787, 914: 0.1400635966948287, 1651: 0.19949401169807818, 950: 0.206445548231362,
				43415: 0.25, 42818: 0.17689861665583512, 40541: 0.25, 41566: 0.18054266084857487
			},
			"rules": []
		},
		134: {
			"signature_weights": {
				1090: 1.0, 1092: 0.0, 997: 1.0, 42790: 1.0, 42442: 1.0, 41323: 1.0, 40465: 1.0, 211: 1.0, 38452: 1.0,
				757: 0.9292484766418416, 38774: 1.0, 42743: 0.0, 1656: 0.8689911983750847, 763: 1.0, 45340: 1.0,
				41418: 1.0, 42773: 1.0
			},
			"rules": []
		},
		63: {
			"signature_weights": {
				42658: 0.25, 1092: 0.0, 42471: 0.25, 46103: 0.25, 1100: 0.25, 42818: 0.25, 42743: 0.0, 48: 0.25, 914: 0.25,
				1651: 0.25, 950: 0.25, 43415: 0.25, 1019: 1.0, 40541: 0.25, 41566: 0.25, 42783: 1.0
			},
			"rules": []
		}
	}


@pytest.fixture(scope="session")
def gilneas_quest_warrior():
	return get_deck_from_deckstring("AAECAQcMS7MB0ALFBKoGognRwwLTwwLPxwLl7wLy8QKe+AIJkQOiBPwE/wf7DJvCAqLHAsrnAqrsAgA=")


@pytest.fixture(scope="session")
def gilneas_standard_warrior_signatures():
	return {
		132: {  # Quest Warrior
			"signature_weights": {
				75: 0.09742185717545061,
				596: 0.3347022587268994,
				785: 0.22587268993839835,
				1023: 0.08008213552361397,
				1074: 0.14966917636322155,
				1659: 0.12885010266940453,
				38530: 0.3059548254620123,
				38738: 0.39014373716632444,
				39225: 0.37166324435318276,
				40574: 0.47638603696098564,
				41243: 0.43896874287018034,
				41414: 0.15970796258270595,
				41418: 0.34588181610768887,
				41427: 0.6944444444444445,
				41890: 0.40520191649555104,
				41929: 0.7002053388090349,
				42395: 0.3162217659137577,
				42700: 0.20841889117043122,
				42818: 0.36647273556924487,
				45775: 0.21532055669632674,
				46027: 0.3721765913757701,
				46031: 0.22958019621263978
			},
			"rules": ["is_quest_deck"]
		},
		224: {  # Odd Quest Warrior
			"signature_weights": {
				75: 0.11045052186550405,
				401: 0.41643546043070423,
				546: 0.24668761678274165,
				581: 0.22802125209973015,
				636: 0.14633939188041448,
				810: 0.5154955363040976,
				1023: 0.10686446596077989,
				1659: 0.15228469509087822,
				41243: 0.4431610139101222,
				41418: 0.3718173753845574,
				41427: 0.6944444444444445,
				41881: 0.5624256837098692,
				41890: 0.41658645225827157,
				41935: 0.21056282203725726,
				46026: 0.4089613649661213,
				46634: 0.9225411924579582,
				47077: 0.6874469169356209,
				47346: 0.49709340731932894,
				47557: 0.5980975029726516,
				48158: 0.6944444444444445
			},
			"rules": ["is_quest_deck", "is_odd_only_deck"]
		}

	}
