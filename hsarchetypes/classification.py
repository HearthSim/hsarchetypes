from .utils import to_prediction_vector_from_dbf_map


def classify_deck(deck, signature_weights):
	distances = []
	archetype_normalizers, cutoff_threshold = calculate_archetype_normalizers(signature_weights)

	for cluster_id, weights in signature_weights.items():
		distance = 0

		for dbf_id, weight in weights.items():
			if dbf_id in deck:
				distance += weight * float(deck[dbf_id])
		distance *= archetype_normalizers[cluster_id]

		if distance and distance >= cutoff_threshold:
			distances.append((cluster_id, distance))

	if distances:
		distances = sorted(distances, key=lambda t: t[1], reverse=True)
		return distances[0][0]


def calculate_archetype_normalizers(signature_weights):
	largest_signature_id = None
	largest_signature_max_score = 0.0
	for archetype_id, signature in signature_weights.items():
		max_score = float(sum(signature.values()))
		if max_score > largest_signature_max_score:
			largest_signature_max_score = max_score
			largest_signature_id = archetype_id

	cutoff_threshold = largest_signature_max_score * .25
	result = {
		largest_signature_id: 1.0
	}
	for archetype_id, signature in signature_weights.items():
		if archetype_id != largest_signature_id:
			result[archetype_id] = largest_signature_max_score / float(sum(signature.values()))
	return result, cutoff_threshold


def train_neural_net(
	train_x,
	train_Y,
	model_data_path,
	batch_size=1000,
	num_epochs=10,
	base_layer_size=128,
	hidden_layer_size=64,
	num_hidden_layers=2
):
	import tensorflow as tf
	tf.Session(config=tf.ConfigProto(log_device_placement=True))

	from keras.callbacks import EarlyStopping
	from keras.models import Sequential
	from keras.layers import Dense, Dropout

	num_features = train_x.shape[1]
	num_classes = train_Y.shape[1]

	model = Sequential()
	model.add(Dense(base_layer_size, input_dim=num_features, activation="relu"))
	model.add(Dropout(0.2))
	for i in range(num_hidden_layers):
		model.add(Dense(hidden_layer_size, activation="relu"))
		model.add(Dropout(0.2))
	model.add(Dense(num_classes, activation="softmax"))

	model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
	history = model.fit(
		train_x,
		train_Y,
		validation_split=0.10,
		batch_size=batch_size,
		epochs=num_epochs,
		callbacks=[EarlyStopping(monitor="val_acc", patience=2, verbose=1)]
	)
	model.save(model_data_path)

	return history


def load_model(model_data_path):
	from keras.models import load_model
	return load_model(model_data_path)


def predict_external_id(model, class_cluster, data_point):
	prediction = model.predict_classes(to_prediction_vector_from_dbf_map(data_point["cards"]))
	return class_cluster.one_hot_external_ids(inverse=True)[prediction[0]]
