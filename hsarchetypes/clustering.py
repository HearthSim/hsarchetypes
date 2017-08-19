from collections import defaultdict
from copy import deepcopy
from itertools import combinations
import numpy as np
from hearthstone.enums import GameTag
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from .signatures import calculate_signature_weights
from .utils import card_db, dbf_id_vector


NUM_CLUSTERS = 6
LOW_VOLUME_CLUSTER_MULTIPLIER = 1.5
INHERITENCE_THRESHOLD = .75


db = card_db()


def cluster_similarity(c1, c2):
	c1_signature = c1.signature
	c1_card_list = c1_signature.keys()
	c2_signature = c2.signature
	c2_card_list = c2_signature.keys()

	intersection = list(set(c1_card_list) & set(c2_card_list))
	union = list(set(c1_card_list) | set(c2_card_list))

	values = {}
	for c in union:
		if c in c1_signature and c in c2_signature:
			values[c] = float((c1_signature[c] + c2_signature[c])) / 2.0
		elif c in c1_signature:
			values[c] = c1_signature[c]
		else:
			values[c] = c2_signature[c]

	w_intersection = 0.0
	for c in intersection:
		w_intersection += values[c]

	w_union = 0.0
	for c in union:
		w_union += values[c]

	if w_union == 0.0:
		weighted_score = 0.0
	else:
		weighted_score = float(w_intersection) / float(w_union)

	return weighted_score


def _analyze_cluster_space(clusters, distance_function=cluster_similarity):
	"""Determine reasonable parameters for second phase of clustering.

	clusters are:
	[
		{
			"observations": 23840
			"signature": {
				"dbf_id": "count",
				"dbf_id": "count",
			}
		},
		{
			....
		}
	]
	"""
	distances_all = []
	for c1, c2 in combinations(clusters, 2):
		sim_score = distance_function(c1, c2)
		distances_all.append(round(sim_score, 2))

	wr = np.array(distances_all)
	mean = np.mean(wr, axis=0)
	std = np.std(wr, axis=0)
	similarity_threshold = mean + (std * 2)  # or 3
	# similarity_threshold is how similar two clusters must be to be eligible to be merged
	# As this value gets larger, we will be less aggressive about merging clusters
	print("\nsimilarity threshold: %s, mean:%s, std:%s\n" % (round(similarity_threshold, 2), round(mean,2), round(std, 2)))

	observations = []
	for cluster in clusters:
		observations.append(cluster.observations)
	wr = np.array(observations)
	mean = np.mean(wr, axis=0)
	std = np.std(wr, axis=0)
	max_val = np.max(wr, axis=0)
	min_val = np.min(wr, axis=0)
	observation_threshold = float(mean) / float(LOW_VOLUME_CLUSTER_MULTIPLIER)  # or 3
	# print("observations: %s" % observations)
	# print("observation thresh: %s, mean:%s, std:%s (can't be above)\n" % (round(observation_threshold, 2), round(mean,2), round(std, 2)))

	return similarity_threshold, observation_threshold


def _do_merge_clusters(clusters, distance_function, minimum_simularity):
	next_cluster_id = max([c.cluster_id for c in clusters]) + 1
	current_clusters = list(clusters)

	most_similar = _most_similar_pair(current_clusters, distance_function)
	if most_similar:
		print("%s\n%s\nMost Similar Pair With Score: %s" % most_similar)
	if not most_similar or most_similar[2] < minimum_simularity:
		print("Does Not Meet Minimum Simularity")
		return current_clusters
	else:
		print("They Will Be Merged")

	c1, c2, sim_score = most_similar
	new_cluster_decks = []
	new_cluster_decks.extend(c1.decks)
	new_cluster_decks.extend(c2.decks)
	new_cluster = Cluster(
		# self,
		next_cluster_id,
		new_cluster_decks,
		# parents=[c1, c2],
		# parent_similarity=sim_score
	)
	next_clusters_list = [new_cluster]
	for c in current_clusters:
		if c.cluster_id not in (c1.cluster_id, c2.cluster_id):
			next_clusters_list.append(c)
	return next_clusters_list


def _most_similar_pair(clusters, distance_function):
	result = []
	# history = []
	# cluster_ids = set()
	for c1, c2 in combinations(clusters, 2):
		# if c1.observations > observation_threshold and c2.observations > observation_threshold:
		# 	print("%s\n%s\nToo Many Observations To Merge " % (str(c1), str(c2)))
		# 	continue

		if not c1.can_merge(c2):
			# print("%s\n%s\nCannot Merge" % (str(c1), str(c2)))
			continue

		# cluster_ids.add("c%s" % c1.cluster_id)
		# cluster_ids.add("c%s" % c2.cluster_id)

		sim_score = distance_function(c1, c2)
		result.append((c1, c2, sim_score))
	# history.append({
	# 		"c1": "c%s" % c1.cluster_id,
	# 		"c2": "c%s" % c2.cluster_id,
	# 		"value": round(sim_score, 3)
	# 	})
	#
	# # Used for pretty printing cluster merging
	# self.merge_history[str(self._merge_pass)] = {
	# 	"cluster_ids": sorted(list(cluster_ids)),
	# 	"scores": history
	# }
	#
	# self._merge_pass += 1
	if len(result):
		sorted_result = sorted(result, key=lambda t: t[2], reverse=True)
		return sorted_result[0]
	else:
		return None


class Cluster:
	"""A cluster is defined by a collection of decks and a signature of card weights."""

	def __init__(self, cluster_id, decks, signature=None, name=None, external_id=None):
		self.cluster_id = cluster_id
		self.decks = decks or []
		self.signature = signature
		self.name = name
		self.external_id = external_id
		self.rules = []
		for deck in self.decks:
			deck["cluster_id"] = cluster_id

	def __str__(self):
		c_id = None
		if self.cluster_id is not None:
			c_id = self.cluster_id
		elif self.name:
			c_id = self.name
		elif self.external_id:
			c_id = self.external_id

		template = "Cluster %s - %i decks (%i games) - %s"
		return template % (str(c_id), len(self.decks), self.observations, self.most_popular_deck["decklist"])

	def __repr__(self):
		return str(self)

	@property
	def most_popular_deck(self):
		return list(sorted(self.decks, key=lambda d: d["observations"], reverse=True))[0]

	@property
	def observations(self):
		return sum(d["observations"] for d in self.decks)

	@property
	def single_deck_max_observations(self):
		return max(d["observations"] for d in self.decks)

	@property
	def pretty_decklists(self):
		return [d["decklist"] for d in self.decks]

	def can_merge(self, other_cluster):
		for r in self.rules:
			for d in other_cluster.decks:
				if not r(d):
					return False

		for r in other_cluster.rules:
			for d in self.decks:
				if not r(d):
					return False

		return True

	def inherit_from_previous(self, previous_class_cluster):
		self.name = previous_class_cluster.name
		self.external_id = previous_class_cluster.external_id

	def pretty_signature_string(self, sep=", "):
		db = card_db()
		components = {}
		for dbf_id, weight in self.signature.items():
			components[db[int(dbf_id)].name] = weight
		sorted_components = sorted(components.items(), key=lambda t: t[1], reverse=True)
		return sep.join(["%s - %s" % (n, str(round(w, 2))) for n, w in sorted_components])


class ClassClusters:
	"""A collection of Clusters for a single player class."""

	def __init__(self, player_class, clusters):
		self.player_class = player_class
		self.clusters = clusters

	def __str__(self):
		return "%s - %i clusters" % (self.player_class, len(self.clusters))

	def __repr__(self):
		return str(self)

	def items(self):
		# Act like a dictionary when passed to calculate_signature_weights(...)
		for cluster in self.clusters:
			yield (cluster.cluster_id, cluster.decks)

	def inherit_from_previous(self, previous_class_cluster):
		consumed_external_cluster_ids = set()
		for current_cluster in self.clusters:
			best_match_score = 0.0
			best_match_cluster = None
			for previous_cluster in previous_class_cluster.clusters:
				if previous_cluster.external_id not in consumed_external_cluster_ids:
					similarity = cluster_similarity(previous_cluster, current_cluster)
					if similarity >= INHERITENCE_THRESHOLD and similarity > best_match_score:
						best_match_score = similarity
						best_match_cluster = previous_cluster
			if best_match_cluster:
				current_cluster.inherit_from_previous(best_match_cluster)
				consumed_external_cluster_ids.add(best_match_cluster.external_id)

	def update_cluster_signatures(self):
		signature_weights = calculate_signature_weights(self)
		for cluster in self.clusters:
			cluster.signature = signature_weights[cluster.cluster_id]

	def consolidate_clusters(self, distance_function=cluster_similarity):
		consolidation_successful = True
		self.update_cluster_signatures()
		similarity_threshold, obsv = _analyze_cluster_space(self.clusters, distance_function)
		while consolidation_successful and len(self.clusters) > 1:
			consolidation_successful = self._attempt_consolidation(similarity_threshold, distance_function)
			self.update_cluster_signatures()

	def _attempt_consolidation(self, similarity_threshold, distance_function=cluster_similarity):
		new_clusters = _do_merge_clusters(self.clusters, distance_function, similarity_threshold)
		success = len(new_clusters) < len(self.clusters)
		self.clusters = new_clusters
		return success


def is_highlander_deck(deck):
	return len(deck["cards"]) == 30


def is_quest_deck(deck):
	for dbf_id in deck["cards"]:
		card = db[int(dbf_id)]
		if GameTag.QUEST in card.tags:
			return True
	return False


FALSE_POSITIVE_RULES = [
	is_highlander_deck,
	is_quest_deck,
]


def to_mana_curve_vector(deck):
	num_cards = float(sum(deck["cards"].values()))
	num_cards_by_cost = defaultdict(int)
	for dbf_id, count in deck["cards"].items():
		card = db[int(dbf_id)]
		num_cards_by_cost[card.cost] += count

	return [float(num_cards_by_cost[c]) / num_cards for c in range(0, 11)]


class ClusterSet:
	"""A collection of ClassClusters."""

	def __init__(self, class_clusters):
		self.class_clusters = class_clusters or []

	def __str__(self):
		ccs = sorted(self.class_clusters, key=lambda cc: cc.player_class)
		return ", ".join(str(cc) for cc in ccs)

	def __repr__(self):
		return str(self)

	def get_class_cluster_by_name(self, player_class_name):
		for class_cluster in self.class_clusters:
			if class_cluster.player_class == player_class_name:
				return class_cluster
		return None

	@classmethod
	def create_cluster_set(
		cls,
		input_data,
		consolidate=True,
		discard_trivial_clusters=True,
		use_mana_curve=True,
		use_tribes=False,
		use_card_types=False,
		use_mechanics=False,
	):
		"""
		Expected input_data format:

		{
			"DRUID": [
				...
			],
			"PALADIN": [
				{
					"observations": 265,
					"decklist": "[Acherus Veteran x 2, Argent Squire x 2, ...],
					"deck_id": 326974234,
					"url": "https://hsreplay.net/decks/xkWJYJTH6KWTdwwpQucxsg",
					"cards": {
						"45392": 1,
						"42467": 2,
						"41139": 2,
						"38745": 2,
						"41145": 1,
						"757": 2,
						"42773": 2,
						"41864": 1,
						"679": 2,
						"40465": 1,
						"38740": 2,
						"42462": 2,
						"847": 2,
						"1022": 2,
						"943": 2,
						"878": 2,
						"42469": 2
					},
					"win_rate": 50.42,
					"avg_num_turns": 17.0
				},
				{
					...
				}
			],
		}
		"""
		data = deepcopy(input_data)
		base_vector = dbf_id_vector()

		class_clusters = []
		for player_class, decks in data.items():
			X = []
			for deck in decks:
				cards = deck["cards"]
				vector = [float(cards.get(str(dbf_id), 0)) / 2.0 for dbf_id in base_vector]

				for rule in FALSE_POSITIVE_RULES:
					rule_outcome = rule(deck)
					vector.append(float(rule_outcome))

				if use_mana_curve:
					mana_curve_vector = to_mana_curve_vector(deck)
					vector.extend(mana_curve_vector)

				if use_tribes:
					vector.extend([])

				if use_card_types:
					# Weapon, Spell, Minion, Hero, Secret
					vector.extend([])

				if use_mechanics:
					# Secret, Deathrattle, Battlecry, Lifesteal,
					vector.extend([])

				X.append(vector)

			if len(decks) > 1:
				from sklearn import manifold
				tsne = manifold.TSNE(n_components=2, init='pca', random_state=0)
				xy = tsne.fit_transform(X)
				# xy = PCA(n_components=2).fit_transform(deepcopy(X))
				for (x, y), deck in zip(xy, decks):
					deck["x"] = float(x)
					deck["y"] = float(y)
			elif len(decks) == 1:
				# Place a single deck at the origin by default
				decks[0]["x"] = 0.0
				decks[0]["y"] = 0.0
			else:
				# No decks for this class so don't include it
				continue

			X = StandardScaler().fit_transform(X)
			clusterizer = KMeans(n_clusters=min(int(NUM_CLUSTERS), len(X)))
			clusterizer.fit(X)

			decks_in_cluster = defaultdict(list)
			for deck, cluster_id in zip(decks, clusterizer.labels_):
				decks_in_cluster[int(cluster_id)].append(deck)

			clusters = [Cluster(id, decks) for id, decks in decks_in_cluster.items()]
			next_cluster_id = max(decks_in_cluster.keys()) + 1
			next_clusters = []
			for rule in FALSE_POSITIVE_RULES:
				for cluster in clusters:

					# If any decks match the rule than split the cluster
					if any(rule(d) for d in cluster.decks):
						matches = Cluster(next_cluster_id, [d for d in cluster.decks if rule(d)])
						matches.rules.extend(cluster.rules)
						matches.rules.append(rule)
						next_clusters.append(matches)
						next_cluster_id += 1

						deck_misses = [d for d in cluster.decks if not rule(d)]
						if len(deck_misses):
							misses = Cluster(next_cluster_id, deck_misses)
							misses.rules.extend(cluster.rules)
							next_clusters.append(misses)
							next_cluster_id += 1
					else:
						next_clusters.append(cluster)
				clusters = next_clusters
				next_clusters = []

			class_cluster = ClassClusters(player_class, clusters)
			class_cluster.update_cluster_signatures()

			if consolidate:
				print("\n\n****** Consolidating: %s ******" % player_class)
				class_cluster.consolidate_clusters()

			if discard_trivial_clusters:
				final_clusters = []
				misc_cluster_decks = []
				for cluster in class_cluster.clusters:
					# check single_deck_max to make sure there will be at least one deck
					# eligible for global stats
					if cluster.observations >= 1000: # and cluster.single_deck_max_observations >= 1000:
						final_clusters.append(cluster)
					else:
						misc_cluster_decks.extend(cluster.decks)

				misc_cluster = Cluster(-1, misc_cluster_decks )
				final_clusters.append(misc_cluster)

				class_cluster = ClassClusters(player_class, final_clusters)
				class_cluster.update_cluster_signatures()

			class_clusters.append(class_cluster)

		return ClusterSet(class_clusters)

	def inherit_from_previous(self, previous_cluster_set):
		for previous_class_cluster in previous_cluster_set.class_clusters:
			for current_class_cluster in self.class_clusters:
				if current_class_cluster.player_class == previous_class_cluster.player_class:
					current_class_cluster.inherit_from_previous(previous_class_cluster)

	def items(self):
		for class_cluster in self.class_clusters:
			yield (class_cluster.player_class, class_cluster.clusters)

	def to_chart_data(self):
		result = []
		for player_class, clusters in self.items():
			player_class_result = {
				"player_class": player_class,
				"data": [],
				"signatures": {}
			}
			for cluster in clusters:
				player_class_result["signatures"][cluster.cluster_id] = cluster.signature
				for deck in cluster.decks:
					metadata = {
						"games": int(deck["observations"]),
						"archetype_name": str(deck["cluster_id"]),
						"archetype": int(deck["cluster_id"]),
						# "url": deck["url"],
						# "deck_id": deck["deck_id"],
						"win_rate": deck["win_rate"],
						"shortid": deck.get("shortid", None),
						"deck_list": deck.get("card_list", None),
						# "pretty_decklist": deck["decklist"]
					}
					player_class_result["data"].append({
						"x": deck["x"],
						"y": deck["y"],
						"metadata": metadata
					})
			result.append(player_class_result)

		return result
