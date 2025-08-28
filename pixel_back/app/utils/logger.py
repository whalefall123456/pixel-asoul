import logging
import sys

# Create logger
logger = logging.getLogger("pixel_canvas")
logger.setLevel(logging.INFO)

# Create console handler and set level to info
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add formatter to handler
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)