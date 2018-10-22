import json
import os

from hsarchetypes.classification import classify_deck

from .conftest import LABELED_CLUSTERS
from .utils import get_deck_from_deckstring


def test_kft_warlock_classification(kft_standard_warlock_signatures, kft_control_warlock):
	DEMON_CONTROL_WARLOCK = 63
	archetype_id = classify_deck(kft_control_warlock, kft_standard_warlock_signatures)
	assert archetype_id == DEMON_CONTROL_WARLOCK


def test_false_positive_rules(gilneas_standard_warrior_signatures, gilneas_quest_warrior):
	QUEST_WARRIOR = 132
	archetype_id = classify_deck(gilneas_quest_warrior, gilneas_standard_warrior_signatures)
	assert archetype_id == QUEST_WARRIOR


MECHATHUN_PRIEST_DECK = \
	"AAECAa0GBu0FpQmdxwLc9QLx+wKIggMM+wHlBPYH0gryDPsM0cEC2MECns4C8M8C6NACvfMCAA=="
MECHATHUN_QUEST_PRIEST_DECK = \
	"AAECAa0GCO0Fw8EC0cEClsQCnccC3PUC8fsCiIIDC4oB+wHlBPIMysMCns4C8M8C6NACqeIC6uYCof4CAA=="

MECHATHUN_PRIEST_SIGNATURE = {
	251: 0.9799464612783544,
	613: 1.0,
	1014: 0.9938477433898464,
	1362: 0.9560418917014981,
	1650: 0.9991546517634904,
	41169: 0.9892922556708778,
	41176: 0.9381956511529611,
	41885: 0.9878833419433617,
	42782: 0.9962428967266238,
	42992: 0.9941764899262668,
	43112: 1.0,
	47836: 0.9962428967266238,
	48625: 1.0,
	49416: 0.9962428967266238
}

MECHATHUN_PRIEST_REQUIRED_CARDS = [48625]
MECHATHUN_PRIEST_ID = 254

MECHATHUN_QUEST_PRIEST_SIGNATURE = {
	138: 0.9531813781571769,
	251: 1.0,
	613: 0.7045674557775236,
	749: 0.973422511660653,
	41169: 1.0,
	41494: 1.0,
	41885: 0.983895098125495,
	42782: 0.98926339875033,
	42992: 0.994631699375165,
	43112: 1.0,
	45353: 0.9965678077972366,
	45930: 0.9859192114758426,
	47836: 0.98926339875033,
	48625: 1.0,
	48929: 1.0,
	49416: 0.98926339875033
}

MECHATHUN_QUEST_PRIEST_REQUIRED_CARDS = [41494, 48625]
MECHATHUN_QUEST_PRIEST_ID = 255


def test_required_cards():
	mechathun_priest_deck = get_deck_from_deckstring(MECHATHUN_PRIEST_DECK)
	mechathun_quest_priest_deck = get_deck_from_deckstring(MECHATHUN_QUEST_PRIEST_DECK)

	assert classify_deck(mechathun_priest_deck, {
		MECHATHUN_QUEST_PRIEST_ID: {
			"signature_weights": MECHATHUN_QUEST_PRIEST_SIGNATURE,
			"required_cards": MECHATHUN_QUEST_PRIEST_REQUIRED_CARDS
		},
	}) is None

	signature_weights = {
		MECHATHUN_PRIEST_ID: {
			"signature_weights": MECHATHUN_PRIEST_SIGNATURE,
			"required_cards": MECHATHUN_PRIEST_REQUIRED_CARDS
		},
		MECHATHUN_QUEST_PRIEST_ID: {
			"signature_weights": MECHATHUN_QUEST_PRIEST_SIGNATURE,
			"required_cards": MECHATHUN_QUEST_PRIEST_REQUIRED_CARDS
		},
	}

	assert MECHATHUN_PRIEST_ID == classify_deck(mechathun_priest_deck, signature_weights)
	assert MECHATHUN_QUEST_PRIEST_ID == classify_deck(
		mechathun_quest_priest_deck,
		signature_weights
	)


def test_neural_network_training():
	data_path = os.path.join(
		LABELED_CLUSTERS,
		"cluster_snapshot.json"
	)
	with open(data_path, "r") as f:
		json.load(f)
