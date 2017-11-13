from copy import copy
from collections import Counter


ARCHETYPE_CORE_CARD_THRESHOLD = .8
ARCHETYPE_CORE_CARD_WEIGHT = 1
ARCHETYPE_TECH_CARD_THRESHOLD = .3
ARCHETYPE_TECH_CARD_WEIGHT = .5
GLOBAL_PREVALENCE_THRESHOLD = .7


default_thresholds = {
	ARCHETYPE_CORE_CARD_THRESHOLD: ARCHETYPE_CORE_CARD_WEIGHT,
	ARCHETYPE_TECH_CARD_THRESHOLD: ARCHETYPE_TECH_CARD_WEIGHT,
}


def calculate_player_class_prevalence(cluster_data):
		card_counter = Counter()
		deck_occurrences = 0.0
		for cluster_id, cluster_decks in cluster_data:
			for deck in cluster_decks:
				obs_count = deck["observations"]
				deck_occurrences += obs_count
				for dbf_id, count in deck["cards"].items():
					card_counter[dbf_id] += obs_count

		return {
			str(dbf_id): card_counter[dbf_id] / deck_occurrences for dbf_id in card_counter
		}


def calculate_signature_weights(
	cluster_data,
	thresholds=default_thresholds,
	use_ccp=True,
	use_thresholds=True
):

	pcp_weights = calculate_player_class_prevalence(cluster_data)
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


def generate_ccp_input_weights(input_weights, cutoff=.5):
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
		if pcp_weights[dbf_id] >= GLOBAL_PREVALENCE_THRESHOLD:
			prevalence = prevalence * (1 - pcp_weights[dbf_id] ** 2)

		if use_thresholds:
			for threshold in sorted(thresholds.keys(), reverse=True):
				if prevalence >= threshold:
					weight = float(thresholds[threshold]) * prevalence
					ret[dbf_id] = weight
					break
		else:
			ret[dbf_id] = prevalence

	return ret


def apply_cross_cluster_prevalence(weights, all_other_weights):
	ret = {}

	num_other_archetypes = len(all_other_weights)
	for dbf_id, weight in weights.items():

		count_in_other_archetypes = 0
		for other_archetype, other_weights in all_other_weights.items():
			if dbf_id in other_weights:
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
