import functools
import json
import requests
from flask import Flask, render_template
from hsarchetypes.clustering import get_decklist_as_vector, scatter_vectors


app = Flask(__name__)


@functools.lru_cache()
def get_archetypes_data():
	# print("Parsing archetypes.json")
	with open("archetypes.json", "r") as f:
		r = json.load(f)["results"]
	return {k["id"]: k for k in r}


@functools.lru_cache()
def query_redshift_data(game_type, rank_range="ALL", time_range="LAST_30_DAYS"):
	endpoint = "https://hsreplay.net/analytics/query/list_decks_by_win_rate/"
	args = {
		"GameType": game_type,
		"RankRange": rank_range,
		"TimeRange": time_range,
	}
	# print(f"Querying {endpoint} with {args}")
	r = requests.get(endpoint, args)

	return r.json()["series"]["data"]


@functools.lru_cache()
def get_decks_data(game_type):
	ret = {}

	archetype_data = get_archetypes_data()
	api_data = query_redshift_data(game_type)

	for player_class, decks_for_class in api_data.items():
		ret[player_class] = []

		max_games = max(decks_for_class, key=lambda dd: dd["total_games"])["total_games"]
		min_games = -(max_games / 2)

		def get_popularity_index(games):
			return (games - min_games) / (max_games - min_games)

		# print(f"Cleaning data for {player_class}")
		for deckdata in decks_for_class:
			deck_list = json.loads(deckdata["deck_list"])
			vector, modifiers = get_decklist_as_vector(deck_list)
			metadata = {
				# "player_class": player_class,
				"games": deckdata["total_games"],
				"deck_list": deck_list,
				"deck_vector": vector,
				"modifiers": modifiers,
				"shortid": deckdata["deck_id"],
				"archetype": deckdata["archetype_id"],
				"avg_turns": deckdata["avg_num_player_turns"],
				"avg_duration": deckdata["avg_game_length_seconds"],
				"win_rate": deckdata["win_rate"],
				"popularity": get_popularity_index(deckdata["total_games"]),
				"url": "https://hsreplay.net/decks/" + deckdata["deck_id"],
			}

			if deckdata["archetype_id"] in archetype_data:
				metadata["archetype_name"] = archetype_data[deckdata["archetype_id"]]["name"]
			else:
				metadata["archetype_name"] = "(unknown archetype)"

			ret[player_class].append(metadata)

	return ret


def decompose_data(data):
	ret = []

	xy = scatter_vectors([dd["deck_vector"] for dd in data])
	for (x, y), metadata in zip(xy, data):
		# delete the vector so that the resulting data isn't too large
		md = metadata.copy()
		del md["deck_vector"]
		ret.append({
			"x": x,
			"y": y,
			"metadata": md,
		})

	return ret


def save_to_image(data, filename):
	"""
	Save the data to an image file, using matplotlib.

	Requires numpy and matplotlib.
	"""
	import numpy
	import matplotlib.patches as mpatches
	import matplotlib.pyplot as plt

	# Clear figure
	plt.clf()
	legend = {}
	archetypes = list(set(x["metadata"]["archetype"] for x in data))
	cmap = plt.get_cmap("jet")
	colors = cmap(numpy.linspace(0, 1, len(archetypes)))

	for point in data:
		color = colors[archetypes.index(point["metadata"]["archetype"])]
		label = point["metadata"]["archetype_name"]
		if label not in legend:
			legend[label] = color

		plt.scatter(
			point["x"], point["y"],
			label=label,
			alpha=point["metadata"]["popularity"],
			color=color
		)

	patches = [mpatches.Patch(label=k, color=v) for k, v in legend.items()]
	plt.legend(handles=patches)
	figure = plt.gcf()
	# print(f"Writing to {filename}")
	figure.savefig(filename)

	return figure


@app.route("/data.json")
def plot_data():
	game_type = "RANKED_STANDARD"
	decks_data = get_decks_data(game_type)

	figures = []
	for player_class, data in decks_data.items():
		# print(f"Plotting for {player_class}")
		class_data = decompose_data(data)
		# figure_id = "{player_class.title()}-{game_type.lower()}".format()
		figures.append({
			# "figure_id": figure_id,
			"game_type": game_type,
			"player_class": player_class,
			"data": class_data,
		})
		# print("Finished plotting", figure_id)

		# save_to_image(class_data, f"{figure_id}.png")

	return json.dumps(figures)


@app.route("/")
def index():
	return render_template("index.html")


if __name__ == "__main__":
	app.run()
