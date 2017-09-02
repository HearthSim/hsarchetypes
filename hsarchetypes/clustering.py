from copy import deepcopy
from itertools import combinations
from hearthstone.enums import CardClass
from .features import *
from .rules import *
from .signatures import calculate_signature_weights
from .utils import card_db, dbf_id_vector


NUM_CLUSTERS = 20
LOW_VOLUME_CLUSTER_MULTIPLIER = 1.5
INHERITENCE_THRESHOLD = .85
SMALL_CLUSTER_CUTOFF = 1500
SIMILARITY_THRESHOLD_FLOOR = .85


USE_THRESHOLDS = False

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
	import numpy as np
	distances_all = []
	for c1, c2 in combinations(clusters, 2):
		sim_score = distance_function(c1, c2)
		distances_all.append(round(sim_score, 2))

	wr = np.array(distances_all)
	mean = np.mean(wr, axis=0)
	std = np.std(wr, axis=0)

	similarity_threshold = SIMILARITY_THRESHOLD_FLOOR
	# similarity_threshold = max(SIMILARITY_THRESHOLD_FLOOR, mean + (std * 1.8))
	# similarity_threshold is how similar two clusters must be to be eligible to be merged
	# As this value gets larger, we will be less aggressive about merging clusters
	msg = "\nsimilarity threshold: %s, mean:%s, std:%s\n"
	values = (round(similarity_threshold, 2), round(mean,2), round(std, 2))
	print(msg % values)

	return similarity_threshold


def _do_merge_clusters(cluster_factory, cluster_set, clusters, distance_function, minimum_simularity):
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
	new_cluster = merge_clusters(cluster_factory, cluster_set, next_cluster_id, [c1, c2])
	next_clusters_list = [new_cluster]
	for c in current_clusters:
		if c.cluster_id not in (c1.cluster_id, c2.cluster_id):
			next_clusters_list.append(c)
	return next_clusters_list


def _most_similar_pair(clusters, distance_function):
	result = []

	for c1, c2 in combinations(clusters, 2):
		if not c1.can_merge(c2):
			continue

		sim_score = distance_function(c1, c2)
		result.append((c1, c2, sim_score))

	if len(result):
		sorted_result = sorted(result, key=lambda t: t[2], reverse=True)
		return sorted_result[0]
	else:
		return None


def merge_clusters(cluster_factory, cluster_set, new_cluster_id, clusters):
	new_cluster_data_points = []
	new_cluster_rules = []
	external_id = None
	name = "NEW"
	for cluster in clusters:
		new_cluster_data_points.extend(cluster.data_points)
		for rule_name in cluster.rules:
			if rule_name not in new_cluster_rules:
				new_cluster_rules.append(rule_name)

		if cluster.external_id:
			if not external_id or external_id == cluster.external_id:
				external_id = cluster.external_id
				name = cluster.name
			else:
				msg = "Cannot merge clusters with different external IDs: (%s, %s)"
				raise RuntimeError(
					msg % (external_id, cluster.external_id)
				)

	for rule_name in new_cluster_rules:
		rule = FALSE_POSITIVE_RULES[rule_name]
		if not all(rule(d) for d in new_cluster_data_points):
			msg = "Not all data points in clusters to be merged pass rule: %s"
			raise RuntimeError(
				msg % (rule_name)
			)

	return Cluster.create(
		cluster_factory,
		cluster_set,
		cluster_id=new_cluster_id,
		data_points=new_cluster_data_points,
		external_id=external_id,
		name=name,
		rules=new_cluster_rules,
	)


class Cluster:
	"""A cluster is a collection of data points representing decks that share a similar strategy"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._factory = None
		self._cluster_set = None

	@staticmethod
	def create(factory, cluster_set, cluster_id, data_points, signature=None, name="NEW", external_id=None, rules=None):
		self = factory()
		self._factory = factory
		self._cluster_set = cluster_set

		self.cluster_id = cluster_id
		self.data_points = data_points or []
		self.signature = signature
		self.name = "Experimental" if cluster_id == -1 else name
		self.external_id = external_id
		self.rules = rules or []
		self._augment_data_points()
		return self

	def _augment_data_points(self):
		for data_point in self.data_points:
			data_point["cluster_id"] = self.cluster_id
			data_point["archetype_name"] = self.name
			data_point["external_id"] = self.external_id

	def __str__(self):
		c_id = None
		if self.cluster_id is not None:
			c_id = self.cluster_id
		elif self.name:
			c_id = self.name
		elif self.external_id:
			c_id = self.external_id

		template = "Cluster %s - %i data points (%i games) - %s"
		pretty_sig = []
		for dbf, w in sorted(self.signature.items(), key=lambda t: t[1], reverse=True):
			card = db[int(dbf)]
			pretty_sig.append("%s:%s" % (card.name, round(w, 2)))
		return template % (str(c_id), len(self.data_points), self.observations, ", ".join(pretty_sig))

	def __repr__(self):
		return str(self)

	@property
	def most_popular_deck(self):
		return list(sorted(self.data_points, key=lambda d: d["observations"], reverse=True))[0]

	@property
	def observations(self):
		return sum(d["observations"] for d in self.data_points)

	@property
	def single_deck_max_observations(self):
		return max(d["observations"] for d in self.data_points)

	@property
	def pretty_decklists(self):
		sorted_decks = list(sorted(self.data_points, key=lambda d: d["observations"], reverse=True))
		return [d["decklist"] for d in sorted_decks[:10]]

	def satisfies_rules(self, rules):
		for rule_name in rules:
			r = FALSE_POSITIVE_RULES[rule_name]
			for d in self.data_points:
				if not r(d):
					return False
		return True

	def can_merge(self, other_cluster):
		other_satisfies_self = self.satisfies_rules(other_cluster.rules)
		self_satisfies_other = other_cluster.satisfies_rules(self.rules)

		return self_satisfies_other and other_satisfies_self

	def inherit_from_previous(self, previous_cluster):
		self.name = previous_cluster.name
		self.external_id = previous_cluster.external_id
		self._augment_data_points()

	def pretty_signature_string(self, sep=", "):
		db = card_db()
		components = {}
		for dbf_id, weight in self.signature.items():
			components[db[int(dbf_id)].name] = weight
		sorted_components = sorted(components.items(), key=lambda t: t[1], reverse=True)
		return sep.join(["%s:%s" % (n, str(round(w, 4))) for n, w in sorted_components])


class ClassClusters:
	"""A collection of Clusters for a single player class."""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._factory = None
		self._cluster_set = None

	@staticmethod
	def create(factory, cluster_set, player_class, clusters):
		self = factory()
		self._factory = factory
		self._cluster_set = cluster_set

		self.player_class = player_class
		self.clusters = clusters
		return self

	def __str__(self):
		return "%s - %i clusters" % (self.player_class, len(self.clusters))

	def __repr__(self):
		return str(self)

	def items(self):
		# Act like a dictionary when passed to calculate_signature_weights(...)
		for cluster in self.clusters:
			yield (cluster.cluster_id, cluster.data_points)

	def inherit_from_previous(self, previous_class_cluster):
		consumed_external_cluster_ids = set()
		for current_cluster in self.clusters:
			if current_cluster.cluster_id != -1:
				best_match_score = 0.0
				best_match_cluster = None
				for previous in previous_class_cluster.clusters:
					has_external_id = previous.external_id is not None
					not_consumed = previous.external_id not in consumed_external_cluster_ids
					if has_external_id and not_consumed:
						similarity = cluster_similarity(previous, current_cluster)
						if similarity >= INHERITENCE_THRESHOLD and similarity > best_match_score:
							best_match_score = similarity
							best_match_cluster = previous
				if best_match_cluster:
					current_cluster.inherit_from_previous(best_match_cluster)
					consumed_external_cluster_ids.add(best_match_cluster.external_id)

	def update_cluster_signatures(self):
		signature_weights = calculate_signature_weights(
			[(c.cluster_id, c.data_points) for c in self.clusters],
			use_ccp=False,
			use_thresholds=USE_THRESHOLDS
		)

		for cluster in self.clusters:
			cluster.signature = signature_weights.get(cluster.cluster_id, {})

		ccp_signature_weights = calculate_signature_weights(
			[(c.cluster_id, c.data_points) for c in self.clusters if c.external_id],
			use_ccp=True,
			use_thresholds=USE_THRESHOLDS
		)

		for cluster in self.clusters:
			cluster.ccp_signature = ccp_signature_weights.get(cluster.cluster_id, {})

	def consolidate_clusters(
		self,
		merge_similarity=SIMILARITY_THRESHOLD_FLOOR,
		distance_function=cluster_similarity
	):
		consolidation_successful = True
		self.update_cluster_signatures()
		similarity_threshold = merge_similarity
		while consolidation_successful and len(self.clusters) > 1:
			consolidation_successful = self._attempt_consolidation(similarity_threshold, distance_function)
			self.update_cluster_signatures()

	def _attempt_consolidation(self, similarity_threshold, distance_function=cluster_similarity):
		new_clusters = _do_merge_clusters(
			self._cluster_set.CLUSTER_FACTORY,
			self._cluster_set,
			self.clusters,
			distance_function,
			similarity_threshold
		)
		success = len(new_clusters) < len(self.clusters)
		self.clusters = new_clusters
		return success


class ClusterSet:
	"""A collection of ClassClusters."""
	CLASS_CLUSTER_FACTORY = ClassClusters
	CLUSTER_FACTORY = Cluster

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._factory = None

	def __str__(self):
		ccs = sorted(self.class_clusters, key=lambda cc: cc.player_class)
		return ", ".join(str(cc) for cc in ccs)

	def __repr__(self):
		return str(self)

	def get_class_cluster_by_name(self, player_class_name):
		player_class = int(CardClass[player_class_name])
		for class_cluster in self.class_clusters:
			if class_cluster.player_class == player_class:
				return class_cluster
		return None

	def inherit_from_previous(self, previous_cluster_set):
		if previous_cluster_set:
			for previous_cc in previous_cluster_set.class_clusters:
				for current_cc in self.class_clusters:
					if current_cc.player_class == previous_cc.player_class:
						current_cc.inherit_from_previous(previous_cc)
						current_cc.update_cluster_signatures()

	def items(self):
		for class_cluster in self.class_clusters:
			yield (class_cluster.player_class, class_cluster.clusters)

	def to_chart_data(self, with_external_ids=False, include_ccp_signature=False):
		result = []
		for player_class, clusters in self.items():
			player_class_result = {
				"player_class": CardClass(int(player_class)).name,
				"data": [],
				"signatures": {},
				"ccp_signatures": {},
				"cluster_map": {},
				"cluster_names": {}
			}
			for c in clusters:
				if with_external_ids and not c.external_id:
					continue
				sig = [[int(dbf), weight] for dbf, weight in c.signature.items()]
				player_class_result["signatures"][c.cluster_id] = sig
				if include_ccp_signature:
					ccp_sig = [[int(dbf), weight] for dbf, weight in c.ccp_signature.items()]
					player_class_result["ccp_signatures"][c.cluster_id] = ccp_sig
				player_class_result["cluster_map"][c.cluster_id] = c.external_id
				for data_point in c.data_points:
					cur_arch_name = str(data_point["archetype_name"] or data_point["cluster_id"])
					player_class_result["cluster_names"][c.cluster_id] = cur_arch_name
					metadata = {
						"games": int(data_point["observations"]),
						"cluster_name": cur_arch_name,
						"cluster_id": int(data_point["cluster_id"]),
						"win_rate": data_point["win_rate"],
						"shortid": data_point.get("shortid", None),
						"deck_list": data_point.get("card_list", None),
					}
					player_class_result["data"].append({
						"x": data_point["x"],
						"y": data_point["y"],
						"metadata": metadata
					})
			result.append(player_class_result)

		return result


def create_cluster_set(
	input_data,
	factory=ClusterSet,
	num_clusters=NUM_CLUSTERS,
	merge_similarity=SIMILARITY_THRESHOLD_FLOOR,
	consolidate=True,
	create_experimental_cluster=True,
	use_mana_curve=True,
	use_tribes=True,
	use_card_types=True,
	use_mechanics=True,
):
	from sklearn import manifold
	from sklearn.cluster import KMeans
	from sklearn.preprocessing import StandardScaler

	self = factory()
	self._factory = factory

	data = deepcopy(input_data)
	base_vector = dbf_id_vector()

	class_clusters = []
	for player_class, data_points in data.items():
		X = []
		for data_point in data_points:
			cards = data_point["cards"]
			vector = [float(cards.get(str(dbf_id), 0)) / 2.0 for dbf_id in base_vector]

			for rule_name, rule in FALSE_POSITIVE_RULES.items():
				rule_outcome = rule(data_point)
				vector.append(float(rule_outcome))

			if use_mana_curve:
				mana_curve_vector = to_mana_curve_vector(data_point)
				vector.extend(mana_curve_vector)

			if use_tribes:
				# Murloc, Dragon, Pirate, etc.
				tribe_vector = to_tribe_vector(data_point)
				vector.extend(tribe_vector)

			if use_card_types:
				# Weapon, Spell, Minion, Hero, Secret
				card_type_vector = to_card_type_vector(data_point)
				vector.extend(card_type_vector)

			if use_mechanics:
				# Secret, Deathrattle, Battlecry, Lifesteal,
				mechanic_vector = to_mechanic_vector(data_point)
				vector.extend(mechanic_vector)

			X.append(vector)

		if len(data_points) > 1:
			tsne = manifold.TSNE(n_components=2, init='pca', random_state=0)
			xy = tsne.fit_transform(deepcopy(X))
			for (x, y), data_point in zip(xy, data_points):
				data_point["x"] = float(x)
				data_point["y"] = float(y)
		elif len(data_points) == 1:
			# Place a single deck at the origin by default
			data_points[0]["x"] = 0.0
			data_points[0]["y"] = 0.0
		else:
			# No data points for this class so don't include it
			continue


		X = StandardScaler().fit_transform(X)
		clusterizer = KMeans(n_clusters=min(int(num_clusters), len(X)))
		clusterizer.fit(X)

		data_points_in_cluster = defaultdict(list)
		for data_point, cluster_id in zip(data_points, clusterizer.labels_):
			data_points_in_cluster[int(cluster_id)].append(data_point)

		clusters = []
		for id, data_points in data_points_in_cluster.items():
			clusters.append(
				Cluster.create(factory.CLUSTER_FACTORY, self, id, data_points)
			)

		next_cluster_id = max(data_points_in_cluster.keys()) + 1
		next_clusters = []
		for rule_name, rule in FALSE_POSITIVE_RULES.items():
			for cluster in clusters:

				# If any data points match the rule than split the cluster
				if any(rule(d) for d in cluster.data_points):
					data_point_matches = [d for d in cluster.data_points if rule(d)]
					matches = Cluster.create(
						factory.CLUSTER_FACTORY,
						self,
						next_cluster_id,
						data_point_matches
					)
					matches.rules.extend(cluster.rules)
					if rule_name not in matches.rules:
						matches.rules.append(rule_name)
					next_clusters.append(matches)
					next_cluster_id += 1

					data_point_misses = [d for d in cluster.data_points if not rule(d)]
					if len(data_point_misses):
						misses = Cluster.create(
							factory.CLUSTER_FACTORY,
							self,
							next_cluster_id,
							data_point_misses
						)
						misses.rules.extend(cluster.rules)
						next_clusters.append(misses)
						next_cluster_id += 1
				else:
					next_clusters.append(cluster)
			clusters = next_clusters
			next_clusters = []

		class_cluster = ClassClusters.create(
			factory.CLASS_CLUSTER_FACTORY,
			self,
			int(CardClass[player_class]),
			clusters
		)
		class_cluster.update_cluster_signatures()

		if consolidate:
			print("\n\n****** Consolidating: %s ******" % player_class)
			class_cluster.consolidate_clusters(merge_similarity)

		if create_experimental_cluster:
			final_clusters = []
			experimental_cluster_data_points = []
			for cluster in class_cluster.clusters:
				# check single_deck_max to make sure there will be at least one deck
				# eligible for global stats
				if cluster.observations >= SMALL_CLUSTER_CUTOFF: # and cluster.single_deck_max_observations >= 1000:
					final_clusters.append(cluster)
				else:
					experimental_cluster_data_points.extend(cluster.data_points)

			if len(experimental_cluster_data_points):
				experimental_cluster = Cluster.create(
					factory.CLUSTER_FACTORY,
					self,
					-1,
					experimental_cluster_data_points
				)
				final_clusters.append(experimental_cluster)

			class_cluster = ClassClusters.create(
				factory.CLASS_CLUSTER_FACTORY,
				self,
				int(CardClass[player_class]),
				final_clusters
			)
			class_cluster.update_cluster_signatures()

		class_clusters.append(class_cluster)

	self.class_clusters = class_clusters
	return self
