import json
import os
from .conftest import CLUSTERING_DATA
from hsarchetypes.clustering import ClusterSet
from hsarchetypes.utils import card_db


db = card_db()


def assert_at_least_N_clusters_contain(N, clusters, dbf_id):
	num_clusters = 0
	for cluster in clusters:
		if str(dbf_id) in cluster.signature:
			num_clusters += 1

	assert num_clusters >= N


def print_pretty_decks(player_class, clusters):
	print("Printing Clusters For: %s" % player_class)
	for cluster in clusters:
		print("%s" % str(cluster))
		for deck in cluster.pretty_decklists:
			print("\t%s" % deck)


def test_clustering_aug12_to_aug19_standard():
	data_path = os.path.join(
		CLUSTERING_DATA,
		"frozen_throne_ranked_standard_aug19_to_aug12.json"
	)
	data = json.load(open(data_path, "r"))

	cluster_set = ClusterSet.create_cluster_set(data)

	# Druid 4 + Experimental
	JADE_IDOL = 40372
	YSHAARJ = 38312
	STRONGSHELL = 43022
	POWER_OF_WILD = 503

	druid_clusters = cluster_set.get_class_cluster_by_name("DRUID").clusters
	print_pretty_decks("DRUID", druid_clusters)
	assert_at_least_N_clusters_contain(1, druid_clusters, JADE_IDOL) # Jade Druid
	assert_at_least_N_clusters_contain(1, druid_clusters, YSHAARJ) # Big Druid
	assert_at_least_N_clusters_contain(1, druid_clusters, STRONGSHELL) # Taunt Druid
	assert_at_least_N_clusters_contain(2, druid_clusters, POWER_OF_WILD) # Aggro Druid
	assert len(druid_clusters) >= 5
	# Potentially we might discover a Jungle Giants Archetype

	# Hunter 2 + Experimental
	CLOAKED_HUNTRESS = 39492
	HIGHMANE = 1261
	NZOTH = 38496

	hunter_clusters = cluster_set.get_class_cluster_by_name("HUNTER").clusters
	print_pretty_decks("HUNTER", hunter_clusters)
	assert_at_least_N_clusters_contain(1, hunter_clusters, CLOAKED_HUNTRESS) # Secret Hunter
	assert_at_least_N_clusters_contain(1, hunter_clusters, HIGHMANE) # Midrange Hunter
	assert_at_least_N_clusters_contain(1, hunter_clusters, NZOTH)  # Deathrattle Hunter
	assert len(hunter_clusters) >= 4

	# Mage 4 + Experimental
	WAYGATE = 41168
	MEDIVH = 39841
	PYROS = 41162
	CRYSTAL_RUNNER = 40583

	mage_clusters = cluster_set.get_class_cluster_by_name("MAGE").clusters
	print_pretty_decks("MAGE", mage_clusters)
	assert_at_least_N_clusters_contain(1, mage_clusters, WAYGATE) # Quest Mage
	assert_at_least_N_clusters_contain(1, mage_clusters, MEDIVH) # Control Mage
	assert_at_least_N_clusters_contain(1, mage_clusters, PYROS) # Elemental Mage
	assert_at_least_N_clusters_contain(1, mage_clusters, CRYSTAL_RUNNER) # Secret Mage
	assert len(mage_clusters) >= 5

	# Paladin 4 + Experimental
	ARGENT_SQUIRE = 757
	WARLEADER = 1063
	SMUGGLERS_RUN = 40371
	EQUALITY = 756

	paladin_clusters = cluster_set.get_class_cluster_by_name("PALADIN").clusters
	print_pretty_decks("PALADIN", paladin_clusters)
	assert_at_least_N_clusters_contain(1, paladin_clusters, ARGENT_SQUIRE) # Aggro Paladin
	assert_at_least_N_clusters_contain(1, paladin_clusters, WARLEADER) # Murloc Paladin
	assert_at_least_N_clusters_contain(1, paladin_clusters, SMUGGLERS_RUN) # Grime Street Paladin
	assert_at_least_N_clusters_contain(1, paladin_clusters, EQUALITY) # Control Paladin
	assert len(paladin_clusters) >= 5

	# Priest 4 + Experimental
	SHADOW_ESSENCE = 42804
	RAZORLEAF = 41925
	NETHERSPITE_HISTORIAN = 39554
	KAZAKUS = 40408

	priest_clusters = cluster_set.get_class_cluster_by_name("PRIEST").clusters
	print_pretty_decks("PRIEST", priest_clusters)
	assert_at_least_N_clusters_contain(1, priest_clusters, SHADOW_ESSENCE) # Resurrect Priest
	# assert_at_least_N_clusters_contain(1, priest_clusters, RAZORLEAF) # Silence Priest
	assert_at_least_N_clusters_contain(1, priest_clusters, NETHERSPITE_HISTORIAN) # Dragon Priest
	assert_at_least_N_clusters_contain(1, priest_clusters, KAZAKUS) # Highlander Priest
	assert len(priest_clusters) >= 4

	# Rogue 5 + Experimental
	AUCTIONEER = 932
	COLDLIGHT = 1016
	COLDBLOOD = 268
	BLAZECALLER = 41928
	JADE_SWARMER = 40697
	SOUTHSEA_CAPTAIN = 680

	rogue_clusters = cluster_set.get_class_cluster_by_name("ROGUE").clusters
	print_pretty_decks("ROGUE", rogue_clusters)
	assert_at_least_N_clusters_contain(1, rogue_clusters, AUCTIONEER) # Miracle Rogue
	assert_at_least_N_clusters_contain(1, rogue_clusters, COLDLIGHT) # Mill Rogue
	assert_at_least_N_clusters_contain(1, rogue_clusters, COLDBLOOD) # Tempo Rogue
	assert_at_least_N_clusters_contain(1, rogue_clusters, BLAZECALLER) # Elemental Rogue
	assert_at_least_N_clusters_contain(1, rogue_clusters, JADE_SWARMER) # Jade Rogue
	assert_at_least_N_clusters_contain(1, rogue_clusters, SOUTHSEA_CAPTAIN)  # Pirate Rogue
	assert len(rogue_clusters) >= 7

	# Shaman 3 + Experimental
	DOPPLEGANGSTER = 40953
	ICE_FISHING = 42763
	ALAKIR = 32

	shaman_clusters = cluster_set.get_class_cluster_by_name("SHAMAN").clusters
	print_pretty_decks("SHAMAN", shaman_clusters)
	assert_at_least_N_clusters_contain(1, shaman_clusters, DOPPLEGANGSTER) # Evolve Shaman
	# assert_N_clusters_contain(1, shaman_clusters, ICE_FISHING) # Murloc Shaman
	# assert_N_clusters_contain(1, shaman_clusters, ALAKIR) # Control Shaman
	assert len(shaman_clusters) >= 2

	# Warlock 4 + Experimental
	DREAD_INFERNAL = 1019
	MOUNTAIN_GIANT = 993
	SILVERWARE_GOLEM = 39380
	DARKSHIRE_COUNCILMAN = 38452

	warlock_clusters = cluster_set.get_class_cluster_by_name("WARLOCK").clusters
	print_pretty_decks("WARLOCK", warlock_clusters)
	assert_at_least_N_clusters_contain(1, warlock_clusters, DREAD_INFERNAL) # Demon Warlock
	assert_at_least_N_clusters_contain(1, warlock_clusters, MOUNTAIN_GIANT) # Handlock
	assert_at_least_N_clusters_contain(1, warlock_clusters, SILVERWARE_GOLEM) # Discard Warlock
	assert_at_least_N_clusters_contain(1, warlock_clusters, DARKSHIRE_COUNCILMAN) # Zoo Warlock
	assert len(warlock_clusters) >= 5

	# Warrior 4 + Experimental
	BLOODSAIL_RAIDER = 999
	BLOOD_WARRIORS = 38848
	FIRE_PLUMES_HEART = 41427
	ALLEY_ARMORSMITH = 40574
	GROMMASH = 338
	NZOTH = 38496

	warrior_clusters = cluster_set.get_class_cluster_by_name("WARRIOR").clusters
	print_pretty_decks("WARRIOR", warrior_clusters)
	assert_at_least_N_clusters_contain(1, warrior_clusters, FIRE_PLUMES_HEART)  # Quest Warrior
	assert_at_least_N_clusters_contain(1, warrior_clusters, BLOODSAIL_RAIDER) # Pirate Warrior
	assert_at_least_N_clusters_contain(1, warrior_clusters, ALLEY_ARMORSMITH)  # Control Warrior
	assert_at_least_N_clusters_contain(1, warrior_clusters, BLOOD_WARRIORS) # Blood Warrior
	assert_at_least_N_clusters_contain(1, warrior_clusters, GROMMASH)  # Enrage Warrior
	assert_at_least_N_clusters_contain(1, warrior_clusters, NZOTH)  # N'Zoth Warrior
	# Training shows an additional archetype even though production doesn't
	assert len(warrior_clusters) >= 6

	chart_data = cluster_set.to_chart_data()
	assert chart_data is not None
