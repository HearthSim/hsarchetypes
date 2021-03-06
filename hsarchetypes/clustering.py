# flake8: noqa (fix features and rules imports)
import json
import logging
from copy import deepcopy
from itertools import combinations
from typing import Optional

from hearthstone.enums import CardClass

from .features import *
from .rules import *
from .signatures import calculate_signature_weights
from .utils import card_db, dbf_id_vector


logger = logging.getLogger("hsarchetypes")


NUM_CLUSTERS = 20
LOW_VOLUME_CLUSTER_MULTIPLIER = 1.5
INHERITENCE_THRESHOLD = .85
SMALL_CLUSTER_CUTOFF = 1500
SIMILARITY_THRESHOLD_FLOOR = .85
SIGNATURE_SIMILARITY_THRESHOLD = .25

USE_THRESHOLDS = False

db = card_db()


def cluster_similarity(c1, c2):
	c1_signature = c1.signature
	c2_signature = c2.signature
	return signature_similarity(c1_signature, c2_signature)


def signature_similarity(c1_signature, c2_signature, verbose=False):
	c1_card_list = [k for k,v in c1_signature.items() if v >= SIGNATURE_SIMILARITY_THRESHOLD]
	c2_card_list = [k for k,v in c2_signature.items() if v >= SIGNATURE_SIMILARITY_THRESHOLD]

	intersection = list(set(c1_card_list) & set(c2_card_list))
	union = list(set(c1_card_list) | set(c2_card_list))

	values = {}
	intersection_values = {}
	for c in union:
		if c in c1_signature and c in c2_signature:
			union_val = float((c1_signature[c] + c2_signature[c]) / 2.0)
			values[c] = union_val
			max_val = max(c1_signature[c], c2_signature[c])
			abs_diff = abs(c1_signature[c] - c2_signature[c])
			intersection_modifier = (max_val - abs_diff) / max_val
			intersection_values[c] = intersection_modifier * union_val
		elif c in c1_signature:
			values[c] = c1_signature[c]
		else:
			values[c] = c2_signature[c]

	w_intersection = 0.0
	intersection_elements = []
	for c in intersection:
		w_intersection += intersection_values[c]
		intersection_elements.append((db[int(c)].name, round(intersection_values[c], 3)))

	w_union = 0.0
	union_elements = []
	difference_elements = []
	for c in union:
		w_union += values[c]
		if c in intersection:
			union_elements.append((db[int(c)].name, round(values[c], 3)))
		else:
			difference_elements.append((db[int(c)].name, round(values[c], 3)))

	if verbose:
		sorted_intersection = sorted(intersection_elements, key=lambda t: t[1], reverse=True)
		intersection_elements = ["%s:%s" % t for t in sorted_intersection]

		sorted_union = sorted(union_elements, key=lambda t: t[1], reverse=True)
		union_elements = ["%s:%s" % t for t in sorted_union]

		sorted_difference = sorted(difference_elements, key=lambda t: t[1], reverse=True)
		difference_elements = ["%s:%s" % t for t in sorted_difference]

		logger.info("INTERSECTION:\n\t%s" % "\n\t".join(intersection_elements))
		logger.info("UNION:\n\t%s" % "\n\t".join(union_elements))
		logger.info("DIFFERENCE:\n\t%s" % "\n\t".join(difference_elements))

	if w_union == 0.0:
		weighted_score = 0.0
	else:
		weighted_score = float(w_intersection) / float(w_union)

	return weighted_score


def find_closest_cluster_pair(clusterset_a, clusterset_b, cmp=cluster_similarity):
	"""
	Take from two clustersets a and b and find the closest pair of its member
	clusters. Optionally takes a `cmp` comparator function argument.

	Returns: member_a, member_b, similarity_score
	"""
	best_match = (None, None, -1)

	for cluster_a in clusterset_a:
		for cluster_b in clusterset_b:
			similarity = cmp(cluster_a, cluster_b)
			if similarity > best_match[2]:
				best_match = (cluster_a, cluster_b, similarity)

	return best_match


def _most_similar_pair(clusters, distance_function):
	result = []

	for c1, c2 in combinations(clusters, 2):
		if not c1.can_merge(c2):
			continue

		if c1.must_merge(c2):
			logger.info("External IDs Match.\n%s\n%s\nMust Merge" % (c1, c2))
			return c1, c2, 1.0

		sim_score = distance_function(c1, c2)
		result.append((c1, c2, sim_score))

	if result:
		sorted_result = sorted(result, key=lambda t: t[2], reverse=True)
		return sorted_result[0]


def merge_clusters(cluster_factory, cluster_set, new_cluster_id, clusters):
	new_cluster_data_points = []
	new_cluster_required_cards = []
	new_cluster_rules = []
	external_id = None
	name = "NEW"
	for cluster in clusters:
		new_cluster_data_points.extend(cluster.data_points)
		for required_card in cluster.required_cards:
			if required_card not in new_cluster_required_cards:
				new_cluster_required_cards.append(required_card)

		for rule_name in cluster.rules:
			if rule_name not in new_cluster_rules:
				new_cluster_rules.append(rule_name)

		if cluster.external_id:
			if not external_id or external_id == cluster.external_id:
				external_id = cluster.external_id
				name = cluster.name
			else:
				raise RuntimeError(
					"Cannot merge clusters with different external IDs: %r, %r" % (
						external_id, cluster.external_id
					)
				)

	for c in new_cluster_required_cards:
		for d in new_cluster_data_points:
			if str(c) not in d["cards"]:
				raise RuntimeError(
					"Not all data points in clusters to be merged include card: %s" % (c)
				)

	for rule_name in new_cluster_rules:
		rule = FALSE_POSITIVE_RULES[rule_name]
		if not all(rule(d) for d in new_cluster_data_points):
			raise RuntimeError(
				"Not all data points in clusters to be merged pass rule: %s" % (rule_name)
			)

	return Cluster.create(
		cluster_factory,
		cluster_set,
		cluster_id=new_cluster_id,
		data_points=new_cluster_data_points,
		external_id=external_id,
		name=name,
		required_cards=new_cluster_required_cards,
		rules=new_cluster_rules,
	)


class Cluster:
	"""
	A collection of data points representing decks that share a similar strategy.
	"""

	def __init__(self, *args, **kwargs):
		self._factory = None
		self._cluster_set = None

	@staticmethod
	def create(
		factory, cluster_set, cluster_id, data_points,
		signature=None, ccp_signature=None,
		name="NEW", external_id=None, required_cards=None, rules=None
	):
		self = factory()
		self._factory = factory
		self._cluster_set = cluster_set

		self.cluster_id = cluster_id
		self.data_points = data_points or []
		self.signature = signature
		self.ccp_signature = ccp_signature
		self.name = "Experimental" if cluster_id == -1 else name
		self.external_id = external_id
		self.required_cards = required_cards or []
		self.rules = rules or []
		self._augment_data_points()
		return self

	def _augment_data_points(self):
		for data_point in self.data_points:
			data_point["cluster_id"] = self.cluster_id
			data_point["archetype_name"] = self.name
			data_point["external_id"] = self.external_id

	def __str__(self):
		c_id = self.get_id()

		template = "Cluster %s - %i data points (%i games) - %s"
		pretty_sig = []
		if self.signature is not None:
			id_sorted = sorted(self.signature.items(), key=lambda t: t[0])
			weight_sorted = reversed(sorted(id_sorted, key=lambda t: round(t[1], 2)))
			for dbf, w in weight_sorted:
				card = db[int(dbf)]
				pretty_sig.append("%s:%s" % (card.name, round(w, 2)))
		return template % (str(c_id), len(self.data_points), self.observations, ", ".join(pretty_sig))

	def get_id(self):
		c_id = None
		if self.cluster_id is not None:
			c_id = self.cluster_id
		elif self.name:
			c_id = self.name
		elif self.external_id:
			c_id = self.external_id
		return c_id

	def __repr__(self):
		return str(self)

	def to_json(self):
		result = {
			"cluster_id": self.cluster_id,
			"experimental": self.experimental,
			"signature": self.signature,
			"name": self.name,
			"required_cards": self.required_cards,
			"rules": self.rules,
			"data_points": self.data_points,
			"external_id": self.external_id,
			"ccp_signature": self.ccp_signature
		}
		return result

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

	def satisfies_required_cards(self, required_cards):
		"""Return True iff every deck in the cluster includes the specified cards."""

		for required_card in required_cards:
			for d in self.data_points:
				if str(required_card) not in d["cards"]:
					return False
		return True

	def must_merge(self, other_cluster):
		self_has_id = self.external_id is not None
		other_has_id = other_cluster.external_id is not None
		# use can_merge to ensure they have compatible FP rule sets
		can_merge = self.can_merge(other_cluster)
		return self_has_id and other_has_id and can_merge

	def can_merge(self, other_cluster):
		other_satisfies_self = \
			self.satisfies_rules(other_cluster.rules) and \
			self.satisfies_required_cards(other_cluster.required_cards)
		self_satisfies_other = \
			other_cluster.satisfies_rules(self.rules) and \
			other_cluster.satisfies_required_cards(self.required_cards)

		no_external_id_conflict = self.external_id == other_cluster.external_id

		return self_satisfies_other and other_satisfies_self and no_external_id_conflict

	def inherit_from_previous(self, previous_cluster):
		self.name = previous_cluster.name
		self.external_id = previous_cluster.external_id
		self.required_cards = previous_cluster.required_cards
		self._augment_data_points()

	def pretty_signature_string(self, sep=", "):
		return self._to_pretty_string(self.signature)

	def pretty_ccp_signature_string(self, sep=", "):
		return self._to_pretty_string(self.ccp_signature)

	def _to_pretty_string(self, sig, sep=", "):
		db = card_db()
		components = {}
		for dbf_id, weight in sig.items():
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

	@property
	def player_class_name(self):
		return CardClass(self.player_class).name

	def to_json(self):
		result = {
			"player_class": self.player_class.name,
			"clusters": []
		}
		for cluster in self.clusters:
			result["clusters"].append(cluster.to_json())

		return result

	def items(self):
		# Act like a dictionary when passed to calculate_signature_weights(...)
		for cluster in self.clusters:
			yield (cluster.cluster_id, cluster.data_points)

	def one_hot_external_ids(self, inverse=False):
		external_ids = set()
		for c in self.clusters:
			if c.external_id is not None:
				external_ids.add(c.external_id)

		if inverse:
			return {index: id for index, id in enumerate(sorted(list(external_ids)))}
		else:
			return {id: index for index, id in enumerate(sorted(list(external_ids)))}

	def create_experimental_cluster(self, experimental_cluster_threshold):
		final_clusters = []
		experimental_cluster_data_points = []
		for cluster in self.clusters:
			if cluster.observations >= experimental_cluster_threshold:
				final_clusters.append(cluster)
			else:
				experimental_cluster_data_points.extend(cluster.data_points)

		if len(experimental_cluster_data_points):
			experimental_cluster = Cluster.create(
				self._cluster_set.CLUSTER_FACTORY,
				self._cluster_set,
				-1,
				experimental_cluster_data_points,
				external_id=-1,
			)
			final_clusters.append(experimental_cluster)
		self.clusters = final_clusters
		self.update_cluster_signatures()

	def inherit_from_previous(self, previous_cc, merge_threshold):
		EXPERIMENTAL = -1
		old_clusters = [
			c for c in previous_cc.clusters
			if c.external_id and c.external_id != EXPERIMENTAL
		]
		new_clusters = [
			c for c in self.clusters if c.external_id != EXPERIMENTAL
		]
		logger.info("Attempting inheritance for: %s" % self.player_class_name)

		while old_clusters:
			old, new, similarity = find_closest_cluster_pair(old_clusters, new_clusters)
			if similarity >= merge_threshold:
				logger.info("Found pair with similarity %r: %r, %r", similarity, old, new)
				new.inherit_from_previous(old)
				old_clusters.remove(old)
				new_clusters.remove(new)
			else:
				logger.info("Similarity hit %r, stopping inheritance", similarity)
				break

		return set(old.external_id for old in old_clusters)

	def update_cluster_signatures(self, use_pcp_adjustment=True):
		logger.info("Updating Signatures For: %s" % self.player_class_name)
		signature_weights = calculate_signature_weights(
			[(c.cluster_id, c.data_points) for c in self.clusters],
			use_ccp=False,
			use_thresholds=USE_THRESHOLDS,
			use_pcp_adjustment=use_pcp_adjustment
		)

		for cluster in self.clusters:
			cluster.signature = signature_weights.get(cluster.cluster_id, {})

		ccp_signature_weights = calculate_signature_weights(
			[(c.cluster_id, c.data_points) for c in self.clusters if c.external_id and c.external_id != -1],
			use_ccp=True,
			use_thresholds=USE_THRESHOLDS,
			use_pcp_adjustment=use_pcp_adjustment
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
		new_clusters = self._do_merge_clusters(distance_function, similarity_threshold)
		success = len(new_clusters) < len(self.clusters)
		self.clusters = new_clusters
		return success

	def _do_merge_clusters(self, distance_function, minimum_simularity):
		cluster_set = self._cluster_set
		cluster_factory = cluster_set.CLUSTER_FACTORY
		next_cluster_id = max(c.cluster_id for c in self.clusters) + 1
		current_clusters = list(self.clusters)

		most_similar = _most_similar_pair(current_clusters, distance_function)
		if most_similar:
			logger.info(
				"Most similar clusters: %r: %r - %r score = %r",
				CardClass(self.player_class).name, most_similar[0].cluster_id,
				most_similar[1].cluster_id, most_similar[2]
			)
			logger.info(most_similar[0])
			logger.info(most_similar[1])

			# verbose=True to log the cluster comparison
			signature_similarity(
				most_similar[0].signature,
				most_similar[1].signature,
				verbose=True
			)

		if not most_similar or most_similar[2] < minimum_simularity:
			logger.info("Clusters do not meet minimum similarity")
			return current_clusters

		logger.info("Clusters will be merged into new cluster with ID: %i" % next_cluster_id)
		c1, c2, sim_score = most_similar
		new_cluster = merge_clusters(cluster_factory, cluster_set, next_cluster_id, [c1, c2])
		next_clusters_list = [new_cluster]
		for c in current_clusters:
			if c.cluster_id not in (c1.cluster_id, c2.cluster_id):
				next_clusters_list.append(c)

		return next_clusters_list

	def merge_cluster_into_external_cluster(self, external_cluster, to_be_merged):
		# Method used to merge clusters together during Archetype Maintenance
		if not external_cluster.external_id:
			raise RuntimeError(
				"The surviving cluster must have an external ID assigned."
			)

		if to_be_merged.external_id:
			raise RuntimeError(
				"The cluster to be merged cannot have an external ID assigned."
			)

		cluster_set = self.cluster_set
		cluster_factory = cluster_set.CLUSTER_FACTORY
		next_cluster_id = max(c.cluster_id for c in self.clusters) + 1
		current_clusters = list(self.clusters)

		new_cluster_data_points = []
		new_cluster_required_cards = []
		new_cluster_rules = []
		external_id = external_cluster.external_id
		name = external_cluster.name

		for cluster in [external_cluster, to_be_merged]:
			new_cluster_data_points.extend(cluster.data_points)
			for rule_name in cluster.rules:
				if rule_name not in new_cluster_rules:
					new_cluster_rules.append(rule_name)
			for required_card in cluster.required_cards:
				if required_card not in new_cluster_required_cards:
					new_cluster_required_cards.append(required_card)

		# Ensure that all data points in the two clusters satisfy each others' required
		# cards and false positive rules before merging them.

		for required_card in [str(c) for c in new_cluster_required_cards]:
			if not all(required_card in d["cards"] for d in new_cluster_data_points):
				raise RuntimeError(
					"Not all data points in clusters to be merged include req. card: %s" % (
						required_card
					)
				)

		for rule_name in new_cluster_rules:
			rule = FALSE_POSITIVE_RULES[rule_name]
			if not all(rule(d) for d in new_cluster_data_points):
				raise RuntimeError(
					"Not all data points in clusters to be merged pass rule: %s" % (rule_name)
				)

		new_cluster = Cluster.create(
			cluster_factory,
			cluster_set,
			cluster_id=next_cluster_id,
			data_points=new_cluster_data_points,
			external_id=external_id,
			name=name,
			required_cards=new_cluster_required_cards,
			rules=new_cluster_rules,
		)

		next_clusters_list = [new_cluster]
		for c in current_clusters:
			if c.cluster_id not in (external_cluster.cluster_id, to_be_merged.cluster_id):
				next_clusters_list.append(c)

		self.clusters = next_clusters_list


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

	def inherit_from_previous(self, previous_cluster_set, merge_threshold):
		if previous_cluster_set:
			uninherited_ids = []
			for previous_cc in previous_cluster_set.class_clusters:
				for current_cc in self.class_clusters:
					if current_cc.player_class == previous_cc.player_class:
						uninherited_class_ids = current_cc.inherit_from_previous(
							previous_cc,
							merge_threshold
						)
				uninherited_ids.extend(uninherited_class_ids)
			return set(uninherited_ids)

	def items(self):
		for class_cluster in self.class_clusters:
			yield (class_cluster.player_class, class_cluster.clusters)

	def to_json(self):
		result = {
			"as_of": self.as_of,
			"game_format": self.game_format.name,
			"live_in_production": self.live_in_production,
			"latest": self.latest,
			"class_clusters": []
		}

		for class_cluster in self.class_clusters:
			result["class_clusters"].append(class_cluster.to_json())

		return json.dumps(result, indent=4)

	def consolidate_clusters(self, merge_similarity):
		for class_cluster in self.class_clusters:
			class_cluster_name = CardClass(class_cluster.player_class).name
			logger.info("****** Consolidating: %s ******", class_cluster_name)
			class_cluster.consolidate_clusters(merge_similarity)

	def create_experimental_clusters(self, experimental_cluster_thresholds):
		for class_cluster in self.class_clusters:
			threshold = experimental_cluster_thresholds.get(
				class_cluster.player_class_name,
				SMALL_CLUSTER_CUTOFF
			)
			class_cluster.create_experimental_cluster(threshold)

	def to_chart_data(self, with_external_ids=False, include_ccp_signature=False, as_of="", external_names={}):
		result = []
		for player_class, clusters in self.items():
			player_class_result = {
				"player_class": CardClass(int(player_class)).name,
				"data": [],
				"signatures": {},
				"ccp_signatures": {},
				"cluster_map": {},
				"cluster_names": {},
				"cluster_required_cards": {},
				"as_of": as_of
			}
			for c in clusters:
				if with_external_ids and (not c.external_id or c.external_id == -1):
					continue
				sig = [[int(dbf), weight] for dbf, weight in c.signature.items()]
				player_class_result["signatures"][c.cluster_id] = sig
				if c.external_id:
					if c.external_id in external_names and c.cluster_id not in player_class_result["cluster_names"]:
						player_class_result["cluster_names"][c.cluster_id] = external_names.get(c.external_id, "NEW")
				if include_ccp_signature:
					ccp_sig = [[int(dbf), weight] for dbf, weight in c.ccp_signature.items()]
					player_class_result["ccp_signatures"][c.cluster_id] = ccp_sig
				player_class_result["cluster_map"][c.cluster_id] = c.external_id
				player_class_result["cluster_required_cards"][c.cluster_id] = c.required_cards
				for data_point in c.data_points:
					external_name = external_names.get(c.external_id, "")
					arch_name = data_point["archetype_name"]
					cluster_id = data_point["cluster_id"]
					cur_arch_name = str(external_name or arch_name or cluster_id)
					# player_class_result["cluster_names"][c.cluster_id] = cur_arch_name
					metadata = {
						"games": int(data_point["observations"]),
						"cluster_name": cur_arch_name,
						"cluster_id": int(data_point["cluster_id"]),
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
	cls=ClusterSet,
	num_clusters=NUM_CLUSTERS,
	merge_similarity=SIMILARITY_THRESHOLD_FLOOR,
	consolidate=True,
	use_mana_curve=True,
	use_tribes=True,
	use_card_types=True,
	use_mechanics=True,
	use_sample_weights: bool = False,
	experimental_threshold_pct: Optional[float] = 0.01,
):
	from sklearn import manifold
	from sklearn.cluster import KMeans
	from sklearn.preprocessing import StandardScaler

	cluster_set = cls()
	cluster_set._factory = cls

	data = deepcopy(input_data)

	class_clusters = []
	for player_class, data_points in data.items():
		logger.info("\nStarting Clustering For: %s" % player_class)
		X = []
		sample_weights = []

		base_vector = dbf_id_vector(player_class=player_class)
		logger.info("Base Cluster Length: %s" % len(base_vector))
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
			sample_weights.append(int(data_point["observations"]))

		logger.info("Full Feature Vector Length: %s" % len(X[0]))

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

		if use_sample_weights:
			clusterizer.fit(X, sample_weight=sample_weights)
		else:
			clusterizer.fit(X)

		data_points_in_cluster = defaultdict(list)
		for data_point, cluster_id in zip(data_points, clusterizer.labels_):
			data_points_in_cluster[int(cluster_id)].append(data_point)

		clusters = []
		for id, data_points in data_points_in_cluster.items():
			clusters.append(
				Cluster.create(cls.CLUSTER_FACTORY, cluster_set, id, data_points)
			)

		next_cluster_id = max(data_points_in_cluster.keys()) + 1
		next_clusters = []
		for rule_name, rule in FALSE_POSITIVE_RULES.items():
			for cluster in clusters:

				# If any data points match the rule than split the cluster
				if any(rule(d) for d in cluster.data_points):
					data_point_matches = [d for d in cluster.data_points if rule(d)]
					matches = Cluster.create(
						cls.CLUSTER_FACTORY,
						cluster_set,
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
							cls.CLUSTER_FACTORY,
							cluster_set,
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
			cls.CLASS_CLUSTER_FACTORY,
			cluster_set,
			int(CardClass[player_class]),
			clusters
		)
		class_cluster.update_cluster_signatures()
		class_clusters.append(class_cluster)

	cluster_set.class_clusters = class_clusters

	if consolidate:
		cluster_set.consolidate_clusters(merge_similarity)

	if experimental_threshold_pct is not None:
		experimental_thresholds = {}
		for player_class_name, data_points in data.items():
			observations_for_class = sum(d["observations"] for d in data_points)
			threshold_for_class = int(observations_for_class * experimental_threshold_pct)
			experimental_thresholds[player_class_name] = threshold_for_class

		cluster_set.create_experimental_clusters(experimental_thresholds)

	return cluster_set
