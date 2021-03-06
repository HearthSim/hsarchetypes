import logging
from collections import Counter
from copy import copy

from hearthstone.enums import CardSet

from .utils import card_db


ARCHETYPE_CORE_CARD_THRESHOLD = .8
ARCHETYPE_CORE_CARD_WEIGHT = 1
ARCHETYPE_TECH_CARD_THRESHOLD = .3
ARCHETYPE_TECH_CARD_WEIGHT = .5
CCP_INPUT_CUTOFF = .3
CCP_THRESHOLD = .1
PCP_EVERGREEN_THRESHOLD = .6
PCP_THRESHOLD = .7


default_thresholds = {
	ARCHETYPE_CORE_CARD_THRESHOLD: ARCHETYPE_CORE_CARD_WEIGHT,
	ARCHETYPE_TECH_CARD_THRESHOLD: ARCHETYPE_TECH_CARD_WEIGHT,
}


logger = logging.getLogger("hsarchetypes")
db = card_db()


def calculate_player_class_prevalence(cluster_data):
		card_counter = Counter()
		deck_occurrences = 0.0
		for cluster_id, cluster_decks in cluster_data:
			for deck in cluster_decks:
				obs_count = deck["observations"]
				deck_occurrences += obs_count
				for dbf_id, count in deck["cards"].items():
					card_counter[dbf_id] += obs_count

		result = {}
		logger.info("\nCalculating PCP Values")
		for dbf_id in card_counter:
			pcp_val = card_counter[dbf_id] / deck_occurrences
			if db[int(dbf_id)].card_set in (CardSet.CORE, CardSet.EXPERT1):
				# Evergreen card
				if pcp_val >= PCP_EVERGREEN_THRESHOLD:
					result[str(dbf_id)] = pcp_val
			else:
				if pcp_val >= PCP_THRESHOLD:
					result[str(dbf_id)] = pcp_val

		for dbf_id, pcp_val in sorted(result.items(), key=lambda t: t[1], reverse=True):
			logger.info("\t%s: %s" % (db[int(dbf_id)].name, str(pcp_val)))

		return result


def calculate_signature_weights(
	cluster_data,
	thresholds=default_thresholds,
	use_ccp=True,
	use_thresholds=True,
	use_pcp_adjustment=True
):

	if not use_ccp and use_pcp_adjustment:
		pcp_weights = calculate_player_class_prevalence(cluster_data)
	else:
		pcp_weights = {}

	# For each archetype generate new signatures.
	raw_new_weights = {}
	for cluster_id, cluster_decks in cluster_data:
		raw_new_weights[cluster_id] = calculate_signature_weights_for_cluster(
			cluster_decks,
			thresholds=thresholds,
			use_thresholds=use_thresholds,
			pcp_weights=pcp_weights
		)

	if use_ccp:
		ccp_input_weights = generate_ccp_input_weights(raw_new_weights)
		final_new_weights = {}

		# Then apply the cross-cluster-prevalence scaling
		for cluster_id, weights in ccp_input_weights.items():
			weights_copy = copy(ccp_input_weights)
			del weights_copy[cluster_id]
			final_new_weights[cluster_id] = apply_cross_cluster_prevalence(
				weights,
				weights_copy
			)
		return final_new_weights
	else:
		return raw_new_weights


def generate_ccp_input_weights(input_weights, cutoff=CCP_INPUT_CUTOFF):
	result = {}
	for cluster_id, weights in input_weights.items():
		if cluster_id not in result:
			result[cluster_id] = {}
		for dbf_id, weight in weights.items():
			if weight >= cutoff:
				result[cluster_id][dbf_id] = weight
	return result


def calculate_signature_weights_for_cluster(
	decks, thresholds=default_thresholds, use_thresholds=True, pcp_weights=None
):
	prevalence_counts = {}
	deck_occurrences = 0

	for deck in decks:
		obs_count = deck["observations"]
		deck_occurrences += obs_count
		for dbf_id, count in deck["cards"].items():
			if dbf_id not in prevalence_counts:
				prevalence_counts[dbf_id] = 0
			prevalence_counts[dbf_id] += obs_count

	if not deck_occurrences:
		# Could not find any matching deck, break early
		return []

	return calculate_prevalences(
		prevalence_counts, deck_occurrences, thresholds, use_thresholds, pcp_weights
	)


def calculate_prevalences(
	prevalence_counts, deck_occurrences, thresholds, use_thresholds, pcp_weights
):
	ret = {}

	for dbf_id, observation_count in prevalence_counts.items():
		prevalence = float(observation_count) / float(deck_occurrences)

		if use_thresholds:
			for threshold in sorted(thresholds.keys(), reverse=True):
				if prevalence >= threshold:
					weight = float(thresholds[threshold]) * prevalence
					if dbf_id in pcp_weights:
						weight = weight * (1 - pcp_weights[dbf_id] ** 3)

					ret[dbf_id] = weight
					break
		else:
			if dbf_id in pcp_weights:
				prevalence = prevalence * (1 - pcp_weights[dbf_id] ** 3)

			ret[dbf_id] = prevalence

	return ret


def apply_cross_cluster_prevalence(weights, all_other_weights):
	ret = {}

	num_other_archetypes = len(all_other_weights)
	for dbf_id, weight in weights.items():

		count_in_other_archetypes = 0
		for other_archetype, other_weights in all_other_weights.items():
			if other_weights.get(dbf_id, 0) > CCP_THRESHOLD:
				count_in_other_archetypes += 1

		cluster_freq_modifier = _calc_cross_cluster_modifier(
			count_in_other_archetypes,
			num_other_archetypes
		)

		ret[dbf_id] = weight * cluster_freq_modifier

	return ret


def _calc_cross_cluster_modifier(count_in_other_archetypes, num_other_archetypes):
	if num_other_archetypes == 0:
		return 1

	p = (1 - count_in_other_archetypes / num_other_archetypes)
	cluster_freq_modifier = p * p
	return cluster_freq_modifier
