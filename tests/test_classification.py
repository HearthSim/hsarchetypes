from hsarchetypes.classification import classify_deck


def test_kft_warlock_classification(kft_standard_warlock_signatures, kft_control_warlock):
	DEMON_CONTROL_WARLOCK = 63
	archetype_id = classify_deck(kft_control_warlock, kft_standard_warlock_signatures)
	assert archetype_id == DEMON_CONTROL_WARLOCK

