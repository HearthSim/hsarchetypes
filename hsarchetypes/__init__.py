def get_signature_components(matching_decks, observation_counts, thresholds):
	card_prevalence_counts = {}
	deck_occurrences = 0
	ret = []

	for digest, cards in matching_decks.items():
		obs_count = observation_counts[digest]
		deck_occurrences += obs_count
		for include in cards:
			key = (include["card_id"], include["dbf_id"])
			if key not in card_prevalence_counts:
				card_prevalence_counts[key] = 0
			card_prevalence_counts[key] += obs_count

	if not deck_occurrences:
		# Could not find any matching deck, break early
		return ret

	for (card_id, dbf_id), observation_count in card_prevalence_counts.items():
		prevalence = float(observation_count) / deck_occurrences

		for threshold in sorted(thresholds.keys(), reverse=True):
			if prevalence >= threshold:
				weight = thresholds[threshold]
				ret.append(({"card_id": card_id, "dbf_id": dbf_id}, weight))
				break

	return ret


def classify_deck(deck, archetype_ids, signature_weights, distance_cutoff):
	distances = []
	for archetype_id in archetype_ids:
		distance = 0
		if archetype_id in signature_weights:
			for dbf_id, weight in signature_weights[archetype_id].items():
				if dbf_id in deck:
					distance += weight * deck.count(dbf_id)

		if distance and distance >= distance_cutoff:
			distances.append((archetype_id, distance))

	if distances:
		distances = sorted(distances, key=lambda t: t[1], reverse=True)
		return distances[0][0]
