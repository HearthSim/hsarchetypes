import json
import os

from hsarchetypes.classification import classify_deck

from .conftest import LABELED_CLUSTERS


def test_kft_warlock_classification(kft_standard_warlock_signatures, kft_control_warlock):
	DEMON_CONTROL_WARLOCK = 63
	archetype_id = classify_deck(kft_control_warlock, kft_standard_warlock_signatures)
	assert archetype_id == DEMON_CONTROL_WARLOCK


def test_new_signature_format(kft_standard_warlock_signatures_new, kft_control_warlock):
	DEMON_CONTROL_WARLOCK = 63
	archetype_id = classify_deck(kft_control_warlock, kft_standard_warlock_signatures_new)
	assert archetype_id == DEMON_CONTROL_WARLOCK


def test_neural_network_training():
	data_path = os.path.join(
		LABELED_CLUSTERS,
		"cluster_snapshot.json"
	)
	with open(data_path, "r") as f:
		json.load(f)
