from hearthstone.enums import GameTag
from .utils import card_db


db = card_db()


def is_highlander_deck(data_point):
	return len(data_point["cards"]) == 30


def is_quest_deck(data_point):
	for dbf_id in data_point["cards"]:
		card = db[int(dbf_id)]
		if GameTag.QUEST in card.tags:
			return True
	return False


FALSE_POSITIVE_RULES = {
	"is_highlander_deck": is_highlander_deck,
	"is_quest_deck": is_quest_deck
}
