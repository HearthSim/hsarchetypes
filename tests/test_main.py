import pytest
from hsarchetypes import get_signature_components, _calc_cross_cluster_modifier


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



def test_calculate_prevalences_for_one_archetype():
	# deck_digest -> { card_id, dbf_id, count }
	matching_decks = {}

	# deck_digest -> total_games
	observation_counts = {}

	thresholds = {
		.8: 1,
		.3: 0.5,
	}

	# archetype_id -> {dbf_id -> weight }
	other_sigs = {

	}

	components = get_signature_components(matching_decks, observation_counts, thresholds, other_sigs)

	# Assert the final weight is the prevelance * threshold


def test_calculate_prevalences_for_two_distinct_archetypes():
	# deck_digest -> { card_id, dbf_id, count }
	matching_decks = {}

	# deck_digest -> total_games
	observation_counts = {}

	thresholds = {
		.8: 1,
		.3: 0.5,
	}

	# archetype_id -> {dbf_id -> weight }
	other_sigs = {

	}

	components = get_signature_components(matching_decks, observation_counts, thresholds, other_sigs)


	# Assert the final weight is the prevelance * threshold


def test_calculate_prevalences_for_two_overlapping_archetypes():
	# deck_digest -> { card_id, dbf_id, count }
	matching_decks = {}

	# deck_digest -> total_games
	observation_counts = {}

	thresholds = {
		.8: 1,
		.3: 0.5,
	}

	# archetype_id -> {dbf_id -> weight }
	other_sigs = {

	}

	components = get_signature_components(matching_decks, observation_counts, thresholds, other_sigs)

def test_calculate_prevalences_for_three_archetypes():
	# deck_digest -> { card_id, dbf_id, count }
	matching_decks = {}

	# deck_digest -> total_games
	observation_counts = {}

	thresholds = {
		.8: 1,
		.3: 0.5,
	}

	# archetype_id -> {dbf_id -> weight }
	other_sigs = {

	}

	components = get_signature_components(matching_decks, observation_counts, thresholds, other_sigs)
