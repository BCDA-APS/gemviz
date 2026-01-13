"""
TAPI: Local support for the tiled API & data structures.

.. autosummary:

    ~connect_tiled_server
    ~get_tiled_runs
    ~QueryTimeSince
    ~QueryTimeUntil
    ~RunMetadata
    ~TiledServerError
"""

import logging

import numpy
import tiled
import tiled.queries
from httpx import ConnectError, HTTPStatusError

logger = logging.getLogger(__name__)


class TiledServerError(RuntimeError):
    """An error from the tiled server."""


class RunMetadata:
    """Cache the metadata for a single run."""

    def __init__(self, cat, uid):
        self.catalog = cat
        self.uid = uid
        self.request_from_tiled_server()

    def __str__(self) -> str:
        return (
            f"{__class__.__name__}(catalog={self.catalog.item['id']!r},"
            f" uid7={self.uid[:7]!r},"
            f" active={self.active})"
        )

    def request_from_tiled_server(self):
        """Get run details from server."""
        self.run = self.catalog[self.uid]
        self.run_md = self.run.metadata
        # Update active status - run is active if it has no stop document or stop is None
        # (Note: use is_active property instead of this attribute for accurate status)
        stop_doc = self.run_md.get("stop")
        self.active = stop_doc is None or stop_doc == {}
        self.streams_md = None
        self.streams_data = None
        logger.debug(f"Run {self.uid[:7]} active status: {self.active}")

    @property
    def is_active(self):
        """Check if this run is currently active (not stopped).

        A run is active if it has no stop document. This is the definitive
        indicator that a run is still acquiring data, regardless of its
        position in the catalog (which may change as new runs are added).

        Note: This property refreshes metadata from the server to ensure
        accurate status.
        """
        # Refresh metadata to get latest status
        self.request_from_tiled_server()

        # A run is active if there's no stop document OR if stop is None
        # (stop key existing with None value means the run is still active)
        stop_doc = self.run_md.get("stop")
        has_stop = stop_doc is not None and stop_doc != {}
        is_active = not has_stop

        logger.info(f"Run {self.uid[:7]}: has_stop={has_stop}, is_active={is_active}")
        if has_stop:
            stop_doc = self.run_md.get("stop")
            if stop_doc and isinstance(stop_doc, dict):
                logger.info(
                    f"Run {self.uid[:7]} has stop document with keys: {list(stop_doc.keys())}"
                )
            else:
                logger.info(
                    f"Run {self.uid[:7]} has 'stop' key in metadata but value is: {stop_doc} (type: {type(stop_doc)})"
                )
        return is_active

    def get_run_md(self, doc, key, default=None):
        """Get metadata by key from run document."""
        return (self.run_md.get(doc) or {}).get(key, default)

    def plottable_signals(self):
        """
        Return a dict with the plottable data for this run.

        * field: any available numeric data keys
        * motors: any data keys for motors declared by the run
        * detectors: any numeric data keys that are not motors or excluded names
        * plot_signal: the first detector signal
        * plot_axes: the first motor signal for each dimension

        * run.metadata[hints][dimensions] show the independent axes object names
        * Any given dimension may have more than one motor object (a2scan, ...)
        * This code chooses to only use the first motor of each dimension.
        * The stream descriptor list is usually length = 1.
        * object_keys are used to get lists of data_keys (fields)
        """

        def find_name_device_or_signal(key):
            if key in stream_hints:  # from ophyd.Device
                return stream_hints[key]["fields"]
            elif key in data_keys:  # from ophyd.Signal
                return [key]
            raise KeyError(f"Could not find {key=}")

        def get_signal(key):
            try:
                return find_name_device_or_signal(key)[0]  # just the first one
            except KeyError:
                if key != "time":
                    raise KeyError(f"Unexpected key: {key!r}")
                return key  # "time" is a special case

        def is_numeric(signal):
            dtype = data_keys[signal]["dtype"]
            if dtype == "array":
                stream_data = self.stream_data(self.stream_name)
                ntype = stream_data["data"][signal].dtype.name
                if ntype.startswith("int") or ntype.startswith("float"):
                    dtype = "number"
            return dtype == "number"

        # dimensions of the run
        run_dims = self.get_run_md("start", "hints", {}).get("dimensions", [])

        # data stream to be used
        streams = [d[1] for d in run_dims]
        if len(set(streams)) != 1:
            # All hinted dimensions should come from the same stream.
            raise ValueError(f"Not handling hinted dimensions: {run_dims=}")
        stream = streams[0]

        # description of the data stream objects
        stream_md = self.stream_metadata(stream)

        # Handle both old (with descriptors) and new (flattened) structures
        if "descriptors" in stream_md:
            descriptors = stream_md.get("descriptors", [])
            if len(descriptors) != 1:
                raise ValueError(f"Not handling situation of {len(descriptors)=}")
            descriptor = descriptors[0]
            # Mapping from object_keys to data_keys.
            stream_hints = descriptor.get("hints", {})
            data_keys = descriptor.get("data_keys", {})
            object_keys = descriptor.get("object_keys", {})
        else:
            stream_hints = stream_md.get("hints", {})
            data_keys = stream_md.get("data_keys", {})
            # Derive object_keys by grouping data_keys by object_name
            object_keys = {}
            for field_name, field_info in data_keys.items():
                obj_name = field_info.get("object_name")
                if obj_name not in object_keys:
                    object_keys[obj_name] = []
                object_keys[obj_name].append(field_name)
            # Create descriptor-like structure for compability
            descriptor = {
                "hints": stream_hints,
                "data_keys": data_keys,
                "object_keys": object_keys,
            }
            descriptors = [descriptor]

        # First motor signal for each dimension.
        # Handle dimensions with empty motor lists by using "time" as fallback
        try:
            axes = [get_signal(d[0][0]) if len(d[0]) > 0 else "time" for d in run_dims]
        except KeyError as exc:
            raise exc

        # All motor signals.
        motors = [
            signal
            for motor in self.get_run_md("start", "motors", [])
            for signal in find_name_device_or_signal(motor)
        ]

        # All detector signals.
        detectors = [
            signal
            for detector in self.get_run_md("start", "detectors")
            for signal in find_name_device_or_signal(detector)
            if is_numeric(signal)
        ]

        fields = []
        for descriptor in descriptors:
            hints = descriptor.get("hints", {})
            for obj_name in descriptor["object_keys"]:
                try:
                    signals = hints.get(obj_name, {})["fields"]
                except KeyError:
                    # ``ophyd.Device`` can have multiple signals
                    signals = descriptor["object_keys"].get(obj_name, [])
                fields.extend([k for k in signals if is_numeric(k)])

        status = self.get_run_md("stop", "exit_status")
        plot_signal = None
        if status != "fail":
            # These runs probably have plottable data fields.

            # Do not choose any of these fields as the default
            # (NeXus-style plottable) signal data.
            not_plottable_signals = """
                timebase
                preset_time
            """.split()

            names_to_avoid = motors + not_plottable_signals
            possible_signals = detectors + fields
            for field in possible_signals:
                if field not in names_to_avoid:
                    plot_signal = field
                    break

        return {
            "catalog": self.catalog.item["id"],
            "uid": self.uid,
            "stream": stream,
            "plot_signal": plot_signal,
            "plot_axes": axes,
            "motors": motors,
            "detectors": detectors,
            "fields": fields,
        }

    def stream_data(self, stream_name):
        """Return the data structure for this stream."""
        if self.streams_data is None:
            self.streams_data = {}

        if stream_name not in self.streams_data:
            try:
                self.streams_data[stream_name] = self.run[stream_name].read()
            except ValueError as exc:
                error_msg = str(exc).lower()
                if "conflicting sizes" in error_msg or "columns" in error_msg:
                    logger.debug(
                        f"Stream {stream_name} not aligned during read; returning raw arrays"
                    )
                    self.streams_data[stream_name] = self._read_stream_arrays(
                        stream_name
                    )
                else:
                    logger.error(f"Failed to read stream data for {stream_name}: {exc}")
                    raise
            except ConnectError as exc:
                logger.warning(f"Connection error reading stream {stream_name}: {exc}")
                raise
            except Exception as exc:
                logger.error(f"Error reading stream data for {stream_name}: {exc}")
                raise

        return self.streams_data[stream_name]

    def force_refresh_stream_data(self, stream_name, raw=False):
        """Force refresh of stream data from server."""
        logger.info(f"Force refreshing stream data for {stream_name}")

        # First, refresh the run metadata to get latest run info
        self.request_from_tiled_server()

        # Clear the cache completely
        self.streams_data = None
        self.streams_md = None

        # Force fresh data read from server
        try:
            logger.info(f"Reading fresh data from run[{stream_name}][data]")
            fresh_data = self.run[stream_name].read()

            if raw:
                arrays = self._dataset_to_arrays(fresh_data)
                logger.debug(
                    f"Returning {stream_name} data as arrays with fields {list(arrays)}"
                )
                return arrays

            # Don't cache this data - return it directly
            logger.info(
                f"Successfully refreshed {stream_name} data, shape: {fresh_data.shape if hasattr(fresh_data, 'shape') else 'unknown'}"
            )
            return fresh_data
        except ValueError as exc:
            error_msg = str(exc).lower()
            if raw and ("conflicting sizes" in error_msg or "columns" in error_msg):
                logger.debug(
                    f"Stream {stream_name} data not aligned yet (conflicting sizes); reading fields individually"
                )
                return self._read_stream_arrays(stream_name)

            logger.error(f"Failed to refresh stream data for {stream_name}: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Error refreshing stream data for {stream_name}: {exc}")
            raise

    def _dataset_to_arrays(self, dataset):
        """Convert xarray Dataset to dict of numpy arrays trimmed to shared length."""
        if dataset is None:
            return {}

        arrays = {}
        min_len = None
        for name, data_array in dataset.data_vars.items():
            values = numpy.asarray(getattr(data_array, "data", data_array))
            arrays[name] = values
            length = values.shape[0] if values.ndim != 0 else 1
            min_len = length if min_len is None else min(min_len, length)

        for name, coord in dataset.coords.items():
            if name in arrays:
                continue
            values = numpy.asarray(getattr(coord, "data", coord))
            arrays[name] = values
            length = values.shape[0] if values.ndim != 0 else 1
            min_len = length if min_len is None else min(min_len, length)

        if min_len is None:
            return arrays

        for name, values in list(arrays.items()):
            if values.ndim != 0 and values.shape[0] > min_len:
                arrays[name] = values[:min_len]
        return arrays

    def _read_stream_arrays(self, stream_name):
        """Read each stream field individually and trim to shared length."""
        arrays = {}
        min_len = None

        data_node = self.run[stream_name]

        # Try iteration first (works with batch_size=1 for both tiled versions)
        try:
            field_names = list(data_node)
            if not field_names:
                # Fall back to metadata if iteration is empty
                raise ValueError("data_node iteration returned empty")
        except (TypeError, AttributeError, ValueError):
            # Fall back to metadata-based approach
            stream_md = self.stream_metadata(stream_name)
            if "descriptors" in stream_md:
                descriptors = stream_md.get("descriptors", [])
                if len(descriptors) != 1:
                    raise ValueError(f"Not handling situation of {len(descriptors)=}")
                data_keys = descriptors[0].get("data_keys", {})
            else:
                data_keys = stream_md.get("data_keys", {})
            field_names = list(data_keys.keys())

        if not field_names:
            logger.warning(f"No fields found for stream {stream_name}")
            return arrays

        # Read fields, skipping those with shape mismatches or not available yet
        for field in field_names:
            try:
                data = data_node[field].read()
                values = getattr(data, "values", getattr(data, "data", data))
                values = numpy.asarray(values)
                arrays[field] = values

                length = values.shape[0] if values.ndim != 0 else 1
                min_len = length if min_len is None else min(min_len, length)
            except (KeyError, AttributeError) as exc:
                # Field doesn't exist yet - skip it
                logger.debug(
                    f"Field {field} not yet available for {stream_name}: {exc}"
                )
                continue
            except Exception as exc:
                # Handle shape mismatch errors (conflicting sizes during live acquisition)
                if (
                    "conflicting sizes" in str(exc).lower()
                    or "expected_shape" in str(exc).lower()
                ):
                    logger.warning(
                        f"Field {field} has conflicting sizes for {stream_name}, skipping: {exc}"
                    )
                    continue
                logger.error(
                    f"Failed to refresh field {field} for {stream_name}: {exc}"
                )
                raise

        if min_len is None:
            return arrays

        for field, values in list(arrays.items()):
            if values.ndim != 0 and values.shape[0] > min_len:
                arrays[field] = values[:min_len]

        logger.debug(
            f"Read {len(arrays)} fields from {stream_name} trimmed to length {min_len}"
        )
        return arrays

    def stream_data_field_shape(self, stream_name, field_name):
        """Shape of this data field."""
        stream = self.stream_data(stream_name)
        try:
            shape = stream[field_name].shape
        except Exception:
            shape = ()
        return shape

    def stream_data_fields(self, stream_name):
        """
        Data field (names) of this BlueskyEventStream.

        Sort the list by relevance.

        First "time" (epoch timestamp for each event document), then "config" (the
        caller provided these names as parameters for this stream), then "data"
        (other signals in this stream, usually added from a Device hint).
        """
        fields = sorted(self.stream_data(stream_name))

        # Promote "time" field to first place.
        if "time" in fields:
            fields.remove("time")
        fields.insert(0, "time")
        return fields

    def stream_data_field_pv(self, stream_name, field_name):
        """EPICS PV name of this field."""
        pv = ""
        try:
            stream_md = self.stream_metadata(stream_name)
            if "descriptors" in stream_md:
                descriptors = stream_md.get("descriptors", [])
                assert len(descriptors) == 1, f"{stream_name=} has {len(descriptors)=}"
                data_keys = descriptors[0]["data_keys"]
            else:
                data_keys = stream_md.get("data_keys", {})
            source = data_keys[field_name].get("source", "")
            if source.startswith("PV:"):
                pv = source[3:]
        except Exception:
            pass
        return pv

    def stream_data_field_units(self, stream_name, field_name):
        """Engineering units of this field."""
        units = ""
        try:
            stream_md = self.stream_metadata(stream_name)
            if "descriptors" in stream_md:
                descriptors = stream_md.get("descriptors", [])
                assert len(descriptors) == 1, f"{stream_name=} has {len(descriptors)=}"
                data_keys = descriptors[0]["data_keys"]
            else:
                data_keys = stream_md.get("data_keys", {})
            units = data_keys[field_name].get("units", "")
        except Exception:
            pass
        return units

    def stream_metadata(self, stream_name=None):
        """Return the metadata dictionary for this stream."""
        if self.streams_md is None:
            # Optimize with a cache.
            self.streams_md = {sname: self.run[sname].metadata for sname in self.run}

        if stream_name is None:
            return self.streams_md
        return self.streams_md[stream_name]

    def summary(self):
        """Summary (text) of this run."""
        return (
            f"{self.get_run_md('start', 'scan_id', '?')}"
            f" {self.get_run_md('start', 'plan_name', '')}"
            f" {self.get_run_md('start', 'title', '')}"
        ).strip()


def connect_tiled_server(uri):
    """Make connection with the tiled server URI.  Return a client object."""
    from tiled.client import from_uri

    # leave out "dask" and get numpy by default
    # https://examples.dask.org/array.html
    # > Call .compute() when you want your result as a NumPy array.
    client = from_uri(uri, "dask")
    return client


def get_tiled_slice(cat, offset, size, ascending=True):
    end = offset + size
    key_gen = cat.keys()

    try:
        return key_gen[offset:end]
    except HTTPStatusError as exc:
        # fmt: off
        # logger.error("HTTPStatusError: %s", exc)
        raise TiledServerError(
            f"{exc.response.reason_phrase}"
            f" ({exc.response.status_code})"
            "  Adjust filters to reduce the catalog size."
        )
        # fmt: on


def QueryTimeSince(isotime):
    """Tiled client query: all runs since given date/time."""
    from . import utils

    return tiled.queries.Key("time") >= utils.iso2ts(isotime)


def QueryTimeUntil(isotime):
    """Tiled client query: all runs until given date/time."""
    from . import utils

    return tiled.queries.Key("time") <= utils.iso2ts(isotime)


def get_run(uri=None, catalog="training", reference=None):
    """Get referenced run from tiled server catalog."""
    # from gemviz.tapi import connect_tiled_server
    # from gemviz.tapi import get_tiled_runs

    uri = uri or "http://localhost:8020"
    client = connect_tiled_server(uri)
    cat = get_tiled_runs(client[catalog], plan_name="scan")
    reference = reference or -1
    uid = reference if isinstance(reference, str) else cat.keys()[reference]
    run = cat[uid]
    return run


def get_tiled_runs(cat, since=None, until=None, text=[], text_case=[], **keys):
    """
    Return a new catalog, filtered by search terms.

    Runs will be selected with start time `>=since` and `< until`.
    If either is `None`, then the corresponding filter will not be
    applied.

    Parameters

    `cat` obj :
        This is the catalog to be searched.
        `Node` object returned by tiled.client.
    `since` str :
        Earliest start date (& time), in ISO8601 format.
    `until` str :
        Latest start date (& time), in ISO8601 format.
    `text` [str] :
        List of full text searches.  Not sensitive to case.
    `text_case` [str] :
        List of full text searches.  Case sensitive.
    `keys` dict :
        Dictionary of metadata keys and values to be matched.
    """
    if since is not None:
        cat = cat.search(QueryTimeSince(since))
    if until is not None:
        cat = cat.search(QueryTimeUntil(until))

    for k, v in keys.items():
        cat = cat.search(tiled.queries.Key(k) == v)

    for v in text:
        cat = cat.search(tiled.queries.FullText(v, case_sensitive=False))
    for v in text_case:
        cat = cat.search(tiled.queries.FullText(v, case_sensitive=True))
    return cat


def is_catalog_of_bluesky_runs(node):
    """
    Check if a tiled node is a CatalogOfBlueskyRuns.

    Parameters:
    -----------
    node : tiled client node
        The node to check

    Returns:
    --------
    bool
        True if node is a CatalogOfBlueskyRuns
    """
    try:
        if hasattr(node, "specs") and len(node.specs) > 0:
            spec = node.specs[0]
            return spec.name == "CatalogOfBlueskyRuns"
    except Exception:
        pass
    return False


def is_run(node):
    """
    Check if a tiled node is a BlueskyRun.

    Parameters:
    -----------
    node : tiled client node
        The node to check

    Returns:
    --------
    bool
        True if node is a Run (has BlueskyRun spec)
    """
    try:
        if hasattr(node, "specs") and len(node.specs) > 0:
            spec = node.specs[0]
            return spec.name == "BlueskyRun"
    except Exception:
        pass
    return False


def is_not_container(node):
    """
    Return True if node is not a tiled container.

    Args:
        node: tiled client node
        The node to check

    Returns:
    --------
    bool
        True if node is a not a container
    """
    try:
        if hasattr(node, "item"):
            attrs = node.item.get("attributes", {})
            structure_family = attrs.get("structure_family")
            return structure_family != "container"
        # If there is no .item, treat it as not-a-container
        return True
    except Exception:
        # On any error, be conservative and skip it as not-a-container
        return True


def is_pure_container(node):
    """
    Check if a tiled node is a pure Container (not a Catalog, not a Run).

    A pure container has:
    - structure_family == 'container'
    - specs == [] (empty)

    Pure containers can contain other containers, files, or other items.
    We want to recurse into pure containers to find nested Catalogs.

    Parameters:
    -----------
    node : tiled client node
        The node to check

    Returns:
    --------
    bool
        True if node is a pure Container (empty specs, not a Catalog or Run)
    """
    try:
        # Must be a container
        if hasattr(node, "item"):
            structure_family = node.item.get("attributes", {}).get("structure_family")
            if structure_family != "container":
                return False
        # Must have empty specs (not a Catalog, not a Run)
        if hasattr(node, "specs"):
            return len(node.specs) == 0
    except Exception:
        pass
    return False


def discover_catalogs(
    client, path="", deep_search=False, max_depth=None, root_client=None
):
    """
    Recursively discover all CatalogOfBlueskyRuns in a tiled server.

    Parameters:
    -----------
    client : tiled client node
        Starting point (server root or Container)
    path : str
        Current path prefix
    deep_search : bool
        If True, also search inside Catalogs for nested Containers
    max_depth : int, optional
        Maximum recursion depth (None = unlimited)
    root_client : tiled client node
        Root server client. Required for path-based access when inside Catalogs.

    Returns:
    --------
    list of tuples
        [(path, catalog_node), ...] where path is the full path to the catalog
    """
    if root_client is None:
        root_client = client
    catalogs = []

    if max_depth is not None and max_depth <= 0:
        logger.debug(f"discover_catalogs: Max depth reached at path={path!r}")
        return catalogs

    logger.debug(
        f"discover_catalogs: Starting discovery at path={path!r}, "
        f"deep_search={deep_search}, max_depth={max_depth}"
    )

    try:
        if is_catalog_of_bluesky_runs(client):
            logger.debug(f"discover_catalogs: Found Catalog at path={path!r}")
            catalogs.append((path, client))
            if deep_search:
                try:
                    children = list(client)
                    logger.debug(
                        f"discover_catalogs: Searching inside Catalog {path!r}, "
                        f"found {len(children)} children"
                    )
                    for key in reversed(children):
                        # Skip "processed" nodes; do not contain runs
                        if key == "processed":
                            logger.debug(
                                f"discover_catalogs: Skipping 'processed' at {path!r}"
                            )
                            continue
                        child_path = f"{path}/{key}" if path else key
                        try:
                            child = root_client[child_path]
                            # Runs come after container when iterating in reversed; earlier items are all runs too → stop.
                            if is_run(child):
                                logger.debug(
                                    f"discover_catalogs: Hit first run at {child_path!r}, "
                                    f"stopping iteration (containers come first in reverse)"
                                )
                                break
                            # Skip non-container nodes (files, etc.)
                            if is_not_container(child):
                                logger.debug(
                                    f"discover_catalogs: Skipping non-container at {child_path!r}"
                                )
                                continue
                            if is_catalog_of_bluesky_runs(child) or is_pure_container(
                                child
                            ):
                                node_type = (
                                    "Catalog"
                                    if is_catalog_of_bluesky_runs(child)
                                    else "pure Container"
                                )
                                logger.debug(
                                    f"discover_catalogs: Recursing into {node_type} at {child_path!r}"
                                )
                                catalogs.extend(
                                    discover_catalogs(
                                        child,
                                        child_path,
                                        deep_search,
                                        max_depth - 1 if max_depth else None,
                                        root_client=root_client,
                                    )
                                )
                        except Exception as exc:
                            logger.debug(f"Error processing child {child_path}: {exc}")
                            continue
                except Exception as exc:
                    logger.debug(f"Error searching inside catalog {path}: {exc}")
            logger.debug(
                f"discover_catalogs: Returning {len(catalogs)} catalog(s) from path={path!r}"
            )
            return catalogs

        if is_pure_container(client):
            try:
                children = list(client)
                logger.debug(
                    f"discover_catalogs: Searching pure Container at path={path!r}, "
                    f"found {len(children)} children"
                )
                for key in reversed(children):
                    # Skip "processed" nodes; do not contain runs
                    if key == "processed":
                        logger.debug(
                            f"discover_catalogs: Skipping 'processed' at {path!r}"
                        )
                        continue
                    child_path = f"{path}/{key}" if path else key
                    try:
                        child = root_client[child_path]
                        # Skip Bluesky runs
                        if is_run(child):
                            logger.debug(
                                f"discover_catalogs: Skipping run at {child_path!r}"
                            )
                            continue
                        # Skip non-container nodes (files, etc.)
                        if is_not_container(child):
                            logger.debug(
                                f"discover_catalogs: Skipping non-container at {child_path!r}"
                            )
                            continue
                        node_type = (
                            "Catalog"
                            if is_catalog_of_bluesky_runs(child)
                            else "pure Container"
                        )
                        logger.debug(
                            f"discover_catalogs: Recursing into {node_type} at {child_path!r}"
                        )
                        catalogs.extend(
                            discover_catalogs(
                                child,
                                child_path,
                                deep_search,
                                max_depth - 1 if max_depth else None,
                                root_client=root_client,
                            )
                        )
                    except Exception as exc:
                        logger.debug(f"Error processing child {child_path}: {exc}")
                        continue
            except Exception as exc:
                logger.debug(f"Error searching Container {path}: {exc}")
    except Exception as exc:
        logger.debug(f"Error processing node at {path}: {exc}")

    logger.debug(
        f"discover_catalogs: Returning {len(catalogs)} catalog(s) from path={path!r}"
    )
    return catalogs


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
