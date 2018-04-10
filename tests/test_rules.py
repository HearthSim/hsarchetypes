from hsarchetypes.rules import is_highlander_deck

from .utils import get_data_point_from_deckstring


def test_is_highlander_deck():
	KAZAKUS_PRIEST = get_data_point_from_deckstring("AAEBAa0GHh6XAuEE5QS5BskGjQjTCtcK8gzVEe4R6BLpEokUpBT6FLAVwxaFF7cXxxeqsgKStAKCtQKDuwK6uwLYuwLwuwLqvwIAAA==")
	assert is_highlander_deck(KAZAKUS_PRIEST)

	RENOLOCK = get_data_point_from_deckstring("AAEBAf0GHooB8gXbBpIHtgfECLkN/g2BDo4Owg/1D60Q1hH9EcMWhRfgrALYuwLexALfxALnywKuzQL3zQKgzgLy0AL40AKX0wLo5wLD6gIAAA==")
	assert is_highlander_deck(RENOLOCK)

	SECRET_MAGE = get_data_point_from_deckstring("AAECAf0EBsABqwS/CKO2Atm7AqLTAgxxuwKVA+YElgXsBde2Auu6Aoe9AsHBApjEAo/TAgA=")
	assert not is_highlander_deck(SECRET_MAGE)
