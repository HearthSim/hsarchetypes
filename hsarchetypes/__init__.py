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
