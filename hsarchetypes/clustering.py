from hearthstone import cardxml
from hearthstone.enums import GameTag, Race


DBF_DB, _ = cardxml.load_dbf()
COLLECTIBLES = [k for k in DBF_DB.values() if k.collectible]


def get_decklist_as_vector(deck_list):
	vec = []
	modifiers = {
		"races": {
			Race.MURLOC: 0,
			Race.ELEMENTAL: 0,
			Race.BEAST: 0
		},
		"tags": {
			GameTag.DEATHRATTLE: 0,
			GameTag.QUEST: 0,
		}
	}

	for card in COLLECTIBLES:
		dbf_id = card.dbf_id
		for id, count in deck_list:
			if dbf_id == id:
				vec.append(count)

				for race in modifiers["races"]:
					if card.race == race:
						modifiers["races"][race] += count

				for tag in modifiers["tags"]:
					if card.tags.get(tag):
						modifiers["tags"][tag] += count

				break
		else:
			vec.append(0)

	return vec, modifiers


def scatter_vectors(vectors):
	from sklearn.decomposition import PCA
	return PCA(n_components=2).fit_transform(vectors)
