
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
