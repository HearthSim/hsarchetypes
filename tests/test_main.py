import json
import os
import pytest
from hearthstone.enums import CardClass
from hsarchetypes import (
	_calc_cross_cluster_modifier, calculate_signature_weights, classify_deck
)
from .conftest import FIXTURE_SUITE


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


@pytest.mark.parametrize(
	'game_format',
	["FT_STANDARD", "FT_WILD"]
)
@pytest.mark.parametrize(
	'player_class_name',
	['DRUID', 'HUNTER', 'MAGE', 'PALADIN', 'PRIEST', 'ROGUE', 'SHAMAN', 'WARLOCK', 'WARRIOR']
)
def test_signature_components(dbf_db, game_format, player_class_name):
	for snapshot in os.listdir(FIXTURE_SUITE):
		print("\n\n*** Fixture: %s ***" % snapshot)

		snapshot_path = os.path.join(FIXTURE_SUITE, snapshot)
		with open(snapshot_path, "r") as f:
			data = json.load(f)

		archetype_map = data["archetype_map"]
		player_class = CardClass[player_class_name]
		class_data = data[game_format][player_class.name]
		training_data = class_data["training"]
		validation_data = class_data["validation"]

		new_weights = calculate_signature_weights(training_data)
		print_pretty_weights(new_weights, archetype_map, dbf_db)

		for expected_id, validation_decks in validation_data.items():
			print("Validating: %s" % archetype_map.get(expected_id, ""))

			for digest, validation_deck in validation_decks.items():
				deck = validation_deck["cards"]
				assigned_id = classify_deck(
					deck,
					new_weights.keys(),
					new_weights
				)
				template = "Assigned Archetype %s (%s). Expected: %s (%s)"
				template += "\nDeck %s\n%s"
				msg = template % (
					assigned_id,
					archetype_map.get(assigned_id, ""),
					expected_id,
					archetype_map.get(expected_id, ""),
					digest,
					to_pretty_deck(dbf_db, deck)
				)
				assert assigned_id == expected_id, msg


def print_pretty_weights(archetype_weights, archetype_map, dbf_db):
	for archetype_id, weights in archetype_weights.items():
		archetype_name = archetype_map[archetype_id]
		print("Archetype: %s" % archetype_name)
		for dbf_id, weight in sorted(weights.items(), key=lambda t: t[1], reverse=True):
			print("Weight: %s, Card: %s" % (round(weight, 3), dbf_db[int(dbf_id)].name))


def to_pretty_deck(dbf_db, deck):
	card_map = {dbf_db[int(dbf_id)]: count for dbf_id, count in deck.items()}
	alpha_sorted = sorted(card_map.items(), key=lambda t: t[0].name)
	mana_sorted = sorted(alpha_sorted, key=lambda t: t[0].cost)
	value_map = ["%s x %i" % (t[0].name, t[1]) for t in mana_sorted]
	return "[%s]" % (", ".join(value_map))
