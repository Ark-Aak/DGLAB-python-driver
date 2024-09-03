import logging, os

LOGFORMAT = "%(module)s [%(levelname)s]: %(message)s"

_logger = logging.getLogger(__name__)

if bool(os.environ.get("BLEAK_LOGGING", False)):
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(fmt=LOGFORMAT))
    _logger.addHandler(handler)

from .service import dglab, dglab_v3
from .model import *
from .bthandler import scan
from .model_v3 import *
from .bthandler_v3 import scan
