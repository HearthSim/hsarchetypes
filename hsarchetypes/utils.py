import os
from hearthstone.cardxml import load_dbf
from hearthstone.enums import CardClass

_CARD_DATA_CACHE = {}


def card_db():
	if "db" not in _CARD_DATA_CACHE:
		db, _ = load_dbf()
		_CARD_DATA_CACHE["db"] = db
	return _CARD_DATA_CACHE["db"]


def dbf_id_vector(player_class=None):
	db = card_db()
	if player_class:
		classes = (CardClass[player_class], CardClass.NEUTRAL)
		all_collectibles = [c for c in db.values() if c.collectible and c.card_class in classes]
	else:
		all_collectibles = [c for c in db.values() if c.collectible]

	return [c.dbf_id for c in sorted(all_collectibles, key=lambda c: c.dbf_id)]


def one_hot_encoding():
	if "one_hot_encoding" not in _CARD_DATA_CACHE:
		_CARD_DATA_CACHE["one_hot_encoding"] = {dbf_id: index for index, dbf_id in enumerate(dbf_id_vector())}
	return _CARD_DATA_CACHE["one_hot_encoding"]


def to_prediction_vector_from_dbf_map(dbf_map):
	card_encoding = one_hot_encoding()
	num_features = len(card_encoding)
	result = [[0 for i in range(num_features)]]

	for dbf_id, count in dbf_map.items():
		if int(dbf_id) in card_encoding:
			result[0][card_encoding[int(dbf_id)]] = count

	return result


def plot_loss_graph(history, player_class, output_path):
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot as plt
	plt.plot(history.history['loss'])
	plt.plot(history.history['val_loss'])
	plt.title('%s model loss' % player_class)
	plt.ylabel('loss')
	plt.xlabel('epoch')
	plt.legend(['train', 'test'], loc='upper left')
	plt.savefig(output_path)
	plt.clf()


def plot_accuracy_graph(history, player_class, output_path):
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot as plt
	plt.plot(history.history['acc'])
	plt.plot(history.history['val_acc'])
	plt.title('%s model accuracy' % player_class)
	plt.ylabel('accuracy')
	plt.xlabel('epoch')
	plt.legend(['train', 'test'], loc='upper left')
	plt.savefig(output_path)
	plt.clf()
