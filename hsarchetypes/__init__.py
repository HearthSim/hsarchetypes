from copy import copy


ARCHETYPE_CORE_CARD_THRESHOLD = .8
ARCHETYPE_CORE_CARD_WEIGHT = 1
ARCHETYPE_TECH_CARD_THRESHOLD = .3
ARCHETYPE_TECH_CARD_WEIGHT = .5


default_thresholds = {
	ARCHETYPE_CORE_CARD_THRESHOLD: ARCHETYPE_CORE_CARD_WEIGHT,
	ARCHETYPE_TECH_CARD_THRESHOLD: ARCHETYPE_TECH_CARD_WEIGHT,
}


def calculate_signature_weights(training_data, thresholds=default_thresholds):
	# For each archetype generate new signatures.
	raw_new_weights = {}
	for archetype_id, training_decks in training_data.items():
		raw_new_weights[archetype_id] = calculate_signature_weights_for_archetype(
			training_decks,
			thresholds
		)

	final_new_weights = {}

	# Then apply the cross-cluster-prevalence scaling
	for archetype_id, weights in raw_new_weights.items():
		weights_copy = copy(raw_new_weights)
		del weights_copy[archetype_id]
		final_new_weights[archetype_id] = apply_cross_cluster_prevalence(
			weights,
			weights_copy
		)
	return final_new_weights


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


def calculate_signature_weights_for_archetype(training_decks, thresholds):
	prevalence_counts = {}
	deck_occurrences = 0

	for digest, deck_data in training_decks.items():
		obs_count = deck_data["total_games"]
		deck_occurrences += obs_count
		for dbf_id, count in deck_data["cards"].items():
			if dbf_id not in prevalence_counts:
				prevalence_counts[dbf_id] = 0
			prevalence_counts[dbf_id] += obs_count

	if not deck_occurrences:
		# Could not find any matching deck, break early
		return []

	return calculate_prevalences(prevalence_counts, deck_occurrences, thresholds)


def calculate_prevalences(prevalence_counts, deck_occurrences, thresholds):
	ret = {}

	for dbf_id, observation_count in prevalence_counts.items():
		prevalence = float(observation_count) / float(deck_occurrences)

		for threshold in sorted(thresholds.keys(), reverse=True):
			if prevalence >= threshold:
				weight = float(thresholds[threshold]) * prevalence
				ret[dbf_id] = weight
				break

	return ret


def _calc_cross_cluster_modifier(count_in_other_archetypes, num_other_archetypes):
	if num_other_archetypes == 0:
		return 1

	p = (1 - count_in_other_archetypes / num_other_archetypes)
	cluster_freq_modifier = p * p
	return cluster_freq_modifier


def classify_deck(deck, archetype_ids, signature_weights, distance_cutoff=0.25):
	distances = []
	for archetype_id in archetype_ids:
		distance = 0
		if archetype_id in signature_weights:
			for dbf_id, weight in signature_weights[archetype_id].items():
				if dbf_id in deck:
					distance += weight
					# * float(deck.count(dbf_id)) if we want to account for copies
					# but we must also normalize for that somehow
			distance /= sum(signature_weights[archetype_id].values())

		if distance and distance >= distance_cutoff:
			distances.append((archetype_id, distance))

	if distances:
		distances = sorted(distances, key=lambda t: t[1], reverse=True)
		return distances[0][0]
