from collections import defaultdict
from hearthstone.enums import GameTag, Race, CardType
from .utils import card_db


db = card_db()


def to_mana_curve_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	num_cards_by_cost = defaultdict(int)
	for dbf_id, count in deck["cards"].items():
		card = db[int(dbf_id)]
		num_cards_by_cost[card.cost] += count

	return [float(num_cards_by_cost[c]) / num_cards for c in range(0, 11)]


mechanics = [
	GameTag.ADAPT,
	GameTag.BATTLECRY,
	GameTag.CHARGE,
	GameTag.CHOOSE_ONE,
	GameTag.COMBO,
	GameTag.DEATHRATTLE,
	GameTag.DISCOVER,
	GameTag.DIVINE_SHIELD,
	GameTag.ENRAGED,
	GameTag.FORGETFUL,
	GameTag.FREEZE,
	GameTag.GRIMY_GOONS,
	GameTag.INSPIRE,
	GameTag.JADE_LOTUS,
	GameTag.KABAL,
	GameTag.LIFESTEAL,
	GameTag.OVERLOAD,
	GameTag.POISONOUS,
	GameTag.RITUAL,
	GameTag.SECRET,
	GameTag.SPELLPOWER,
	GameTag.SILENCE,
	GameTag.TAUNT,
	GameTag.WINDFURY,
]


def to_mechanic_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	mechanics_count = []
	for mechanic in mechanics:
		num_occurs = float(0)
		for dbf_id, count in deck["cards"].items():
			card = db[int(dbf_id)]
			if card.tags.get(mechanic, 0):
				num_occurs += float(count)
		mechanics_count.append(num_occurs / num_cards)

	return mechanics_count


def to_card_type_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	card_type_count = defaultdict(int)
	for dbf_id, count in deck["cards"].items():
		card = db[int(dbf_id)]
		card_type_count[card.type] += count

	return [float(card_type_count[t]) / num_cards for t in CardType]


def to_tribe_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	tribe_count = defaultdict(int)
	for dbf_id, count in deck["cards"].items():
		card = db[int(dbf_id)]
		tribe_count[card.race] += count

	return [float(tribe_count[r]) / num_cards for r in Race]
