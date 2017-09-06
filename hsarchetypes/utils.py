from hearthstone.cardxml import load_dbf

_CARD_DATA_CACHE = {}


def card_db():
	if "db" not in _CARD_DATA_CACHE:
		db, _ = load_dbf()
		_CARD_DATA_CACHE["db"] = db
	return _CARD_DATA_CACHE["db"]


def dbf_id_vector():
	db = card_db()

	all_collectibles = [c for c in db.values() if c.collectible]
	return [c.dbf_id for c in sorted(all_collectibles, key=lambda c: c.dbf_id)]


def one_hot_encoding():
	return {dbf_id: index for index, dbf_id in enumerate(dbf_id_vector())}


def to_prediction_vector(data_point):
	import numpy as np
	card_encoding = one_hot_encoding()
	num_features = len(card_encoding) + 1
	result = np.zeros((1, num_features))

	for dbf_id, count in data_point['cards'].items():
		result[0][card_encoding[int(dbf_id)]] = count

	return result