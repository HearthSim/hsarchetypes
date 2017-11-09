import logging
from .signatures import calculate_signature_weights
from .classification import classify_deck


logger = logging.getLogger("hsarchetypes")
logger.setLevel(logging.INFO)
