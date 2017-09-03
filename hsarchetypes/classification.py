
def classify_deck(deck, signature_weights):
	distances = []
	archetype_normalizers, cutoff_threshold = calculate_archetype_normalizers(signature_weights)

	for cluster_id, weights in signature_weights.items():
		distance = 0

		for dbf_id, weight in weights.items():
			if dbf_id in deck:
				distance += weight * float(deck[dbf_id])
		distance *= archetype_normalizers[cluster_id]

		if distance and distance >= cutoff_threshold:
			distances.append((cluster_id, distance))

	if distances:
		distances = sorted(distances, key=lambda t: t[1], reverse=True)
		return distances[0][0]


def calculate_archetype_normalizers(signature_weights):

	largest_signature_id = None
	largest_signature_max_score = 0.0
	for archetype_id, signature in signature_weights.items():
		max_score = float(sum(signature.values()))
		if max_score > largest_signature_max_score:
			largest_signature_max_score = max_score
			largest_signature_id = archetype_id

	cutoff_threshold = largest_signature_max_score * .25
	result = {
		largest_signature_id: 1.0
	}
	for archetype_id, signature in signature_weights.items():
		if archetype_id != largest_signature_id:
			result[archetype_id] = largest_signature_max_score / float(sum(signature.values()))
	return result, cutoff_threshold
