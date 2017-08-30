from copy import copy


ARCHETYPE_CORE_CARD_THRESHOLD = .8
ARCHETYPE_CORE_CARD_WEIGHT = 1
ARCHETYPE_TECH_CARD_THRESHOLD = .3
ARCHETYPE_TECH_CARD_WEIGHT = .5


default_thresholds = {
	ARCHETYPE_CORE_CARD_THRESHOLD: ARCHETYPE_CORE_CARD_WEIGHT,
	ARCHETYPE_TECH_CARD_THRESHOLD: ARCHETYPE_TECH_CARD_WEIGHT,
}


def calculate_signature_weights(
	cluster_data,
	thresholds=default_thresholds,
	use_ccp=True,
	use_thresholds=True
):
	# For each archetype generate new signatures.
	raw_new_weights = {}
	for cluster_id, cluster_decks in cluster_data.items():
		raw_new_weights[cluster_id] = calculate_signature_weights_for_cluster(
			cluster_decks,
			thresholds,
			use_thresholds
		)

	if use_ccp:
		final_new_weights = {}

		# Then apply the cross-cluster-prevalence scaling
		for cluster_id, weights in raw_new_weights.items():
			weights_copy = copy(raw_new_weights)
			del weights_copy[cluster_id]
			final_new_weights[cluster_id] = apply_cross_cluster_prevalence(
				weights,
				weights_copy
			)
		return final_new_weights
	else:
		return raw_new_weights


def calculate_signature_weights_for_cluster(decks, thresholds=default_thresholds, use_thresholds=True):
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

	return calculate_prevalences(prevalence_counts, deck_occurrences, thresholds, use_thresholds)


def calculate_prevalences(prevalence_counts, deck_occurrences, thresholds, use_thresholds=True):
	ret = {}

	for dbf_id, observation_count in prevalence_counts.items():
		prevalence = float(observation_count) / float(deck_occurrences)

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
