from tiled.client import from_uri
from tiled.client.cache import Cache
from tiled.utils import tree
import tiled.queries

host="localhost"  # or "localhost" or whatever name the tiled server is using
port=8000

client = from_uri(f"http://{host}:{port}", cache=Cache.in_memory(2e9))
