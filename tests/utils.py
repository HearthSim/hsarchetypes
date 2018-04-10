from hearthstone.deckstrings import parse_deckstring


def get_data_point_from_deckstring(deckstring):
	cardlist, _, _ = parse_deckstring(deckstring)
	cards = {dbf_id: count for (dbf_id, count) in cardlist}
	return {
		"cards": cards,
	}
