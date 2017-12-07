from hsarchetypes.clustering import signature_similarity


def test_signature_similarity():
	# Verify that identical signatures are a perfect match
	c1_sig = {
		41496: 1.0,
		40494: .98,
		846: .6
	}
	assert signature_similarity(c1_sig, c1_sig) == 1.0

	# Assert that totally disjoint signatures are a 0 match
	c2_sig = {
		922: 1.0,
		39417: .98,
		40596: .6
	}
	assert signature_similarity(c1_sig, c2_sig) == 0.0

	# Assert that signatures with different weights aren't a perfect match
	c3_sig = {
		41496: 1.0,
		40494: .67,
		846: .43
	}
	result = signature_similarity(c1_sig, c3_sig)
	assert result < 1.0
