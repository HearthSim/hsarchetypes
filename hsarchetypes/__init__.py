import logging

from .classification import classify_deck
from .signatures import calculate_signature_weights


__all__ = ["calculate_signature_weights", "classify_deck"]

logger = logging.getLogger("hsarchetypes")
logger.setLevel(logging.INFO)
