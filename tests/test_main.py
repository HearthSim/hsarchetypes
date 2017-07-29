import json
import os
import pytest
from hearthstone.enums import CardClass
from hsarchetypes import (
	calculate_signature_weights, classify_deck, _calc_cross_cluster_modifier
)
from tests.conftest import FIXTURE_SUITE


def test_calc_cross_cluster_modifier():

	assert _calc_cross_cluster_modifier(0, 0) == 1

	assert _calc_cross_cluster_modifier(0, 1) == 1
	assert _calc_cross_cluster_modifier(1, 1) == 0

	assert _calc_cross_cluster_modifier(0, 2) == 1
	assert _calc_cross_cluster_modifier(1, 2) == .25
	assert _calc_cross_cluster_modifier(2, 2) == 0

	assert _calc_cross_cluster_modifier(0, 3) == 1
	assert _calc_cross_cluster_modifier(1, 3) == pytest.approx(4 / 9.0)
	assert _calc_cross_cluster_modifier(2, 3) == pytest.approx(1 / 9.0)
	assert _calc_cross_cluster_modifier(3, 3) == 0


def test_signature_components(dbf_db):
	for snapshot in os.listdir(FIXTURE_SUITE):
		snapshot_path = os.path.join(FIXTURE_SUITE, snapshot)

		archetype_map_path = os.path.join(snapshot_path, "archetype_map.json")
		if os.path.exists(archetype_map_path):
			archetype_map = json.loads(open(archetype_map_path).read())
		else:
			archetype_map = {}

		for game_format in ("FT_STANDARD", "FT_WILD"):
			format_path = os.path.join(snapshot_path, game_format)
			for player_class in CardClass:
				if CardClass.DRUID <= player_class <= CardClass.WARRIOR:
					training_file = "%s_training_decks.json" % player_class.name
					training_path = os.path.join(format_path, training_file)
					training_data = json.loads(open(training_path).read())

					new_weights = calculate_signature_weights(training_data)

					validation_file = "%s_validation_decks.json" % player_class.name
					validation_path = os.path.join(format_path, validation_file)
					validation_data = json.loads(open(validation_path).read())

					for expected_id, validation_decks in validation_data.items():
						for digest, validation_deck in validation_decks.items():
							deck = validation_deck["cards"]
							assigned_id = classify_deck(
								deck,
								new_weights.keys(),
								new_weights
							)
							template = "Assigned Archetype %s (%s). Expected: %s (%s)"
							template += "\nDeck %s %s"
							msg = template % (
								assigned_id,
								archetype_map.get(assigned_id, ""),
								expected_id,
								archetype_map.get(expected_id, ""),
								digest,
								to_pretty_deck(dbf_db, deck)
							)

							assert assigned_id == expected_id, msg


def to_pretty_deck(dbf_db, deck):
	result = []
	for dbf_id, count in deck.items():
		for i in range(count):
			result.append(dbf_db[int(dbf_id)].name)
	return result