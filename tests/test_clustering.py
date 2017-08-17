import json
import os
from .conftest import CLUSTERING_DATA
from hsarchetypes.clustering import ClusterSet


def test_clustering():
	for data_set in os.listdir(CLUSTERING_DATA):
		print("\n\n*** Fixture: %s ***" % data_set)

		data_set_path = os.path.join(CLUSTERING_DATA, data_set)
		data = json.load(open(data_set_path, "r"))

		cluster_set = ClusterSet.create_cluster_set(data)
		chart_data = cluster_set.to_chart_data()
		print(json.dumps(chart_data))