from collections import defaultdict
from random import randint, shuffle
from hearthstone.enums import GameTag, Race, CardType
from .utils import card_db, one_hot_encoding


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
	GameTag.JADE_GOLEM,
]


def to_mechanic_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	mechanics_count = []
	for mechanic in mechanics:
		num_occurs = float(0)
		for dbf_id, count in deck["cards"].items():
			card = db[int(dbf_id)]
			if card.tags.get(mechanic, 0) or card.referenced_tags.get(mechanic, 0):
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


def to_neural_net_training_data(
		class_cluster,
		num_examples=1000000,  # Actually train on 10MM
		max_dropped_cards=15,
		stratified=False,
		min_cards_for_determination=5  # Minimum cards needed to make a determination
	):
	import numpy as np
	print("Generating %i examples of training data with %i max dropped cards" % (num_examples, max_dropped_cards))

	card_encoding = one_hot_encoding()
	id_encoding = class_cluster.one_hot_external_ids()

	num_features = len(card_encoding)
	num_classes = len(id_encoding)

	train_x = np.zeros((num_examples, num_features))
	train_Y = np.zeros((num_examples, num_classes))
	row_id = 0

	total_observations_for_class = 0.0
	for c in class_cluster.clusters:
		if c.external_id is not None:
			total_observations_for_class += c.observations

	print("total observations across the player class is: %i" % total_observations_for_class)
	for cluster in class_cluster.clusters:
		if cluster.external_id is None:
			continue

		total_observations = float(cluster.observations)
		if stratified:
			examples_for_cluster = int(num_examples * (total_observations / total_observations_for_class))
		else:
			examples_for_cluster = int(num_examples / num_classes)

		tmpl = "Total observations in cluster with external_id %i and %i data points is %i, will generate %i examples"
		number_of_decks = len(cluster.data_points)
		print(tmpl % (cluster.external_id, number_of_decks, total_observations, examples_for_cluster))
		for data_point in cluster.data_points:
			cards = []
			for dbf_id, count in data_point["cards"].items():
				cards.append([card_encoding[int(dbf_id)], count])

			if stratified:
				examples = int(examples_for_cluster * (data_point["observations"] / total_observations))
			else:
				examples = int(examples_for_cluster / number_of_decks)

			for i in range(examples):
				shuffle(cards)
				truncate_deck_count = len(cards) - randint(0, max_dropped_cards)
				if truncate_deck_count < min_cards_for_determination:
					truncate_deck_count = min_cards_for_determination

				for c in cards[:truncate_deck_count]:
					train_x[row_id][c[0]] = randint(0, c[1])

				train_Y[row_id][id_encoding[cluster.external_id]] = 1
				row_id += 1

				if row_id >= num_examples:
					break

	assert train_x.shape[0] == num_examples
	return train_x, train_Y