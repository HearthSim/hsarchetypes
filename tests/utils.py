from hearthstone.deckstrings import parse_deckstring


def get_deck_from_deckstring(deckstring):
	cardlist, _, _ = parse_deckstring(deckstring)
	return {dbf_id: count for (dbf_id, count) in cardlist}


def get_data_point_from_deckstring(deckstring):
	return {
		"cards": get_deck_from_deckstring(deckstring),
	}
