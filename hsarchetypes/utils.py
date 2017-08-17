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
