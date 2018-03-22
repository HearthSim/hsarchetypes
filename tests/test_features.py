import json

import os
import pytest
from hsarchetypes.clustering import create_cluster_set
from hsarchetypes.features import to_neural_net_training_data

from .conftest import CLUSTERING_DATA


@pytest.mark.skip(reason="Skipping while refactoring fixture format")
def test_clustering_aug12_to_aug19_standard():
	data_path = os.path.join(
		CLUSTERING_DATA,
		"frozen_throne_ranked_standard_aug19_to_aug12.json"
	)
	data = json.load(open(data_path, "r"))

	cluster_set = create_cluster_set(data)

	num_examples = 10000
	for class_cluster in cluster_set.class_clusters:
		train_x, train_Y = to_neural_net_training_data(
			class_cluster,
			num_examples=num_examples
		)
		assert len(train_x) == num_examples
