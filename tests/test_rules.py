from hsarchetypes.rules import (
	is_even_only_deck, is_highlander_deck, is_odd_only_deck, is_quest_deck
)

from .utils import get_data_point_from_deckstring


def test_is_highlander_deck():
	KAZAKUS_PRIEST = get_data_point_from_deckstring("AAEBAa0GHh6XAuEE5QS5BskGjQjTCtcK8gzVEe4R6BLpEokUpBT6FLAVwxaFF7cXxxeqsgKStAKCtQKDuwK6uwLYuwLwuwLqvwIAAA==")
	assert is_highlander_deck(KAZAKUS_PRIEST)

	RENOLOCK = get_data_point_from_deckstring("AAEBAf0GHooB8gXbBpIHtgfECLkN/g2BDo4Owg/1D60Q1hH9EcMWhRfgrALYuwLexALfxALnywKuzQL3zQKgzgLy0AL40AKX0wLo5wLD6gIAAA==")
	assert is_highlander_deck(RENOLOCK)

	SECRET_MAGE = get_data_point_from_deckstring("AAECAf0EBsABqwS/CKO2Atm7AqLTAgxxuwKVA+YElgXsBde2Auu6Aoe9AsHBApjEAo/TAgA=")
	assert not is_highlander_deck(SECRET_MAGE)


def test_is_quest_deck():
	QUEST_MAGE = get_data_point_from_deckstring("AAECAf0EBooB7QS4CNDBArnRApbkAgzAAZwCyQOrBMsE5gT4B5KsAoGyAsHBApjEAtrFAgA=")
	assert is_quest_deck(QUEST_MAGE)

	QUEST_ROGUE = get_data_point_from_deckstring("AAECAaIHBM0DhsICz+ECw+oCDcQBnALtAp8DiAXUBfgHhgn4vQKXwQL8wQLrwgLH0wIA")
	assert is_quest_deck(QUEST_ROGUE)

	QUEST_WARRIOR = get_data_point_from_deckstring("AAECAQcIkAP8BPsM0q4CubIC08MC38QCoM4CC0uRBoKtAv68ApvCAsbDAsrDAqLHAsnHApvLAszNAgA=")
	assert is_quest_deck(QUEST_WARRIOR)

	QUEST_DRUID = get_data_point_from_deckstring("AAECAZICBMIG4q8C4LsCi8ECDV+TBOQIy7wCxsIC98wCoM0Ch84CmNICntICi+ECmuQChOYCAA==")
	assert is_quest_deck(QUEST_DRUID)

	QUEST_PRIEST = get_data_point_from_deckstring("AAECAa0GCJ8D7QXgrAKKsAKWxALPxwKQ0wLD6gILigH7AbW7AuW8AsPBAtHBAtXBAujQAovhAqniAurmAgA=")
	assert is_quest_deck(QUEST_PRIEST)

	QUEST_PALADIN = get_data_point_from_deckstring("AAECAZ8FBvIF9AWKxwKMxwLj4wLD6gIM+wGvB/YH3QrZrgLdrgLfxAKIxwLYxwLjywLt0gL40gIA")
	assert is_quest_deck(QUEST_PALADIN)

	QUEST_SHAMAN = get_data_point_from_deckstring("AAEBAaoIBsAHkwn2vQLjvgLkwgKbxAIMxQP+BdAHpwigtgLjuwKRwQKdwgKxwgKGxAK2zQKLzgIA")
	assert is_quest_deck(QUEST_SHAMAN)

	QUEST_HUNTER = get_data_point_from_deckstring("AAECAR8IuwX+DJjDAt7EAobTApziAtDnAsPqAgu7A/UFx64Cl8EC68ICisMCxscClc4C6+MCi+UC1+sCAA==")
	assert is_quest_deck(QUEST_HUNTER)

	QUEST_WARLOCK = get_data_point_from_deckstring("AAEBAf0GBoDHApTHAs/HArjQApfTAtjnAgz3BM4HxAjzDK+sAtSzAry2AuTCAt7EApHHAvjQAs7pAgA=")
	assert is_quest_deck(QUEST_WARLOCK)

	SECRET_MAGE = get_data_point_from_deckstring("AAECAf0EBsABqwS/CKO2Atm7AqLTAgxxuwKVA+YElgXsBde2Auu6Aoe9AsHBApjEAo/TAgA=")
	assert not is_quest_deck(SECRET_MAGE)


def test_is_even_only_deck():
	EVEN_MAGE = get_data_point_from_deckstring("AAEBAf0EBIAEpRDyE/LTAg0piwOuA5YGvwiNELoR8RONrAL0rwLBwQLczQKIzgIA")
	assert is_even_only_deck(EVEN_MAGE)

	SECRET_MAGE = get_data_point_from_deckstring("AAECAf0EBsABqwS/CKO2Atm7AqLTAgxxuwKVA+YElgXsBde2Auu6Aoe9AsHBApjEAo/TAgA=")
	assert not is_even_only_deck(SECRET_MAGE)


def test_is_odd_only_deck():
	ODD_MAGE = get_data_point_from_deckstring("AAEBAf0ECIUD7AeTD4QQo7YC+L8C1+ECo+sCC8ABwwHtBMoI7ROBsgLnvwKhwgK50QLu0wKW5AIA")
	assert is_odd_only_deck(ODD_MAGE)

	SECRET_MAGE = get_data_point_from_deckstring("AAECAf0EBsABqwS/CKO2Atm7AqLTAgxxuwKVA+YElgXsBde2Auu6Aoe9AsHBApjEAo/TAgA=")
	assert not is_odd_only_deck(SECRET_MAGE)
