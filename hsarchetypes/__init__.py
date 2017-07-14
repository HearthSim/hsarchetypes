def get_signature_components(matching_decks, observation_counts, thresholds, other_sigs):
	prevalence_counts = {}
	deck_occurrences = 0

	for digest, cards in matching_decks.items():
		obs_count = observation_counts[digest]
		deck_occurrences += obs_count
		for include in cards:
			key = (include["card_id"], include["dbf_id"])
			if key not in prevalence_counts:
				prevalence_counts[key] = 0
			prevalence_counts[key] += obs_count

	if not deck_occurrences:
		# Could not find any matching deck, break early
		return []

	return calculate_prevalences(prevalence_counts, deck_occurrences, thresholds, other_sigs)


def calculate_prevalences(prevalence_counts, deck_occurrences, thresholds, other_sigs):
	ret = []

	for (card_id, dbf_id), observation_count in prevalence_counts.items():
		prevalence = float(observation_count) / float(deck_occurrences)

		count_in_other_archetypes = sum(
			other_sigs.values(),
			key=lambda x: int(dbf_id in x)
		)
		cluster_freq_modifier = _calc_cross_cluster_modifier(count_in_other_archetypes, len(other_sigs))

		for threshold in sorted(thresholds.keys(), reverse=True):
			if prevalence >= threshold:
				weight = float(threshold) * prevalence * cluster_freq_modifier
				ret.append(({"card_id": card_id, "dbf_id": dbf_id}, weight))
				break

	return ret


def _calc_cross_cluster_modifier(count_in_other_archetypes, num_other_archetypes):
	if num_other_archetypes == 0:
		return 1

	p = (1 - count_in_other_archetypes / num_other_archetypes)
	cluster_freq_modifier = p * p
	return cluster_freq_modifier


def classify_deck(deck, archetype_ids, signature_weights, distance_cutoff):
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


		if distance and distance >= 0.25: #distance_cutoff:
			distances.append((archetype_id, distance))

	if distances:
		distances = sorted(distances, key=lambda t: t[1], reverse=True)
		return distances[0][0]


# ToDo:
	# Regenerate all signatures for a class at the same time
	# Figure out distance cutoff?
	# Write a reprocess command, e.g. water rogue and elemental rogue
	# Add component category names to SignatureComponent
	# Write a big ass test suite
	# Add instrumentation around match strengths, frequency, distance to second best match
	# Dealing with multiple close matches (e.g. 3 signature matches within 1% of each other)
		# Throw it all out
		# Randomly pick one
		# Let the highest value win.
		# Select the most popular archetype
		# Use the one with strongest single card match
		# Look at other features, e.g. game duration

