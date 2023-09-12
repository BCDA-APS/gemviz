"""
Analyze a tiled run for its plottable data.

.. autosummary::

    ~SignalAxesFields
"""

import logging
import warnings

from . import tapi

logger = logging.getLogger(__name__)
DEFAULT_STREAM = "primary"


class SignalAxesFields:
    """
    Identify the signal and axes data fields from the run.

    .. autosummary::

        ~to_dict
        ~descriptors
        ~hints
        ~identify_axes
        ~identify_detectors
        ~identify_fields
        ~identify_chart
        ~object_names
        ~object_name_to_fields
    """

    # runs with these exit_status probably have plottable data fields
    status__with_data = """
        abort
        success
    """.split()

    # do not choose any of these fields as the default (NeXus-style plottable) signal data.
    not_signals = """
        timebase
        preset_time
    """.split()

    def __init__(self, run, default_stream=DEFAULT_STREAM) -> None:
        self.run = run

        self._cleanup_motor_heuristic = False
        self.plot_axes = []
        self.plot_signal = None
        self.positioners = []
        self.stream_name = default_stream
        self.fields = []
        self.detectors = []
        self.chart_type = None

        self._descriptors = None

        self.plan_name = tapi.get_md(run, "start", "plan_name")
        self.scan_id = tapi.get_md(run, "start", "scan_id")
        self.status = tapi.get_md(run, "stop", "exit_status")
        self.time = tapi.get_md(run, "start", "time")
        self.title = tapi.get_md(run, "start", "title")
        self.uid = tapi.get_md(run, "start", "uid")

        if self.status in self.status__with_data:
            self.identify_axes()  # call first, redefines self.stream_name

            self.identify_detectors()
            self.identify_fields()
            self.identify_chart()

    def __repr__(self) -> str:
        s = (
            f"uid7:{self.uid[:7]}"
            f" ScanID:{self.scan_id}"
            f" plan:{self.plan_name}"
            f" status:{self.status}"
            f" title:{self.title!r}"
        )
        if self.plot_signal is not None:
            s += (
                f" stream:{self.stream_name}"
                f" signal:{self.plot_signal}"
                f" axes:{self.plot_axes}"
                f" detectors:{self.detectors}"
                f" fields:{self.fields}"
            )
        # fmt: off
        if (
            (
                self.plot_signal is None
                or self.positioners != self.plot_axes
            )
            and len(self.positioners)
        ):
            s += f" all_dim_fields:{self.positioners}"
        return s
        # fmt: on

    def descriptors(self, stream=None, use_cache=True):
        """Return the list of descriptor documents."""
        if use_cache and self._descriptors is not None:
            # optimize slow process by cacheing
            return self._descriptors

        # (re)discover the descriptors for this stream and cache them
        run_stream = self.run.get(stream or self.stream_name)
        if run_stream is None:
            return []  # nothing that is plottable

        self._descriptors = run_stream.metadata.get("descriptors") or []
        return self._descriptors

    def hints(self, stream=None):
        """Return the hints for this stream."""
        hints = {}
        for descriptor in self.descriptors(stream=stream):
            hints.update(descriptor.get("hints", {}))
        return hints

    def identify_axes(self) -> None:
        """Discover the motor (independent axis) fields."""
        hints = tapi.get_md(self.run, "start", "hints", {})
        motors = tapi.get_md(self.run, "start", "motors")
        logger.debug("motors=%s", motors)

        # Prepare a guess about the dimensions (independent variables) in case
        # we need it.
        guess = (
            [(["time"], self.stream_name)]
            if motors is None
            else [([motor], self.stream_name) for motor in motors]
        )
        logger.debug("guess=%s", guess)

        # Ues the guess if there is nothint about dimensions.
        dimensions = hints.get("dimensions")
        if dimensions is None:
            self._cleanup_motor_heuristic = True
            dimensions = guess

        # We can only cope with all the dimensions belonging to the same
        # stream unless we resample. We are not doing to handle that yet.
        if len(set(d[1] for d in dimensions)) != 1:
            self._cleanup_motor_heuristic = True
            dimensions = guess  # Fall back on our GUESS.
            warnings.warn(
                "We are ignoring the dimensions hinted because we cannot combine streams."
            )

        logger.debug("dimensions=%s", dimensions)

        # for each dimension, choose one field only
        # the plan can supply a list of fields. It's assumed the first
        # of the list is always the one plotted against
        self.plot_axes = [
            fields[0] for fields, stream_name in dimensions if len(fields) > 0
        ]
        logger.debug("plot_axes=%s", self.plot_axes)

        # make distinction between flattened fields and plotted fields
        # motivation for this is that when plotting, we find dependent variable
        # by finding elements that are not independent variables
        self.positioners = [
            field for fields, stream_name in dimensions for field in fields
        ]

        _, self.stream_name = dimensions[0]

    def identify_chart(self) -> None:
        """Identify the type of chart fot this run's data."""
        rank = len(self.plot_axes)
        if rank == 1 and self.plot_signal is not None:
            shape = self.descriptors()[0]["data_keys"][self.plot_signal]["shape"]
            if len(shape) in (0, 1):
                n_events = tapi.get_md(self.run, "stop", "num_events", {})
                events = n_events.get(self.stream_name)
                if events > 1:
                    self.chart_type = "line_1D"
            elif len(shape) in (2, 3):
                self.chart_type = f"unknown{len(shape)}D"
        elif rank == 2 and self.plot_signal is not None:
            hints = tapi.get_md(self.run, "start", "hints", {})
            gridding = hints.get("gridding")
            self.chart_type = "grid_2D" if gridding == "rectilinear" else "scatter_2D"
        else:
            self.chart_type = None

    def identify_detectors(self) -> None:
        """
        Discover the list of detectors defined by the run.

        Return the fields (the names of the actual data), not the object names.
        """

        def is_numeric(detector, descriptor):
            dtype = descriptor["data_keys"][detector]["dtype"]
            if dtype == "array":
                ntype = self.run[self.stream_name]["data"][detector].dtype.name
                if ntype.startswith("int") or ntype.startswith("float"):
                    dtype = "number"
            return dtype == "number"

        detectors = []
        for det_name in tapi.get_md(self.run, "start", "detectors", []):
            detectors.extend(self.object_name_to_fields(det_name))

        # fmt: off
        self.detectors = [
            det  # only numeric data
            for det in detectors
            for descriptor in self.descriptors(stream=self.stream_name)
            if is_numeric(det, descriptor)
        ]

    def identify_fields(self) -> None:
        """
        Discover the data (both dependent and independent axis) fields.

        We will see if the object_names hint at whether a subset of their data
        keys ("fields") are interesting. Use them if they are hinted.
        Otherwise, we know that the RunEngine *always* records the complete list
        of fields in each stream, so we can use them all unselectively.
        """
        for obj_name in self.object_names():
            try:
                fields = self.hints().get(obj_name, {})["fields"]
            except KeyError:
                fields = self.object_name_to_fields(obj_name)
            self.fields.extend(fields)

        # identify the first plottable field, NeXus uses this, for example
        names_to_avoid = self.positioners + self.not_signals
        possible_signals = self.detectors + self.fields
        for field in possible_signals:
            if field not in names_to_avoid:
                self.plot_signal = field
                break

    def object_names(self, stream=None):
        """Return the names of objects used in the run."""
        obj_names = []
        for descriptor in self.descriptors(stream=stream):
            obj_names.extend(list(descriptor["object_keys"]))
        return obj_names

    def object_name_to_fields(self, obj_name, stream=None):
        """
        Return the fields for a given object name.

        The run may have recorded data identified by either the name of the
        ``ophyd.Signal`` (field) or the name of the ``ophyd.Device`` (object).
        """
        fields = []
        for descriptor in self.descriptors(stream=stream):
            fields.extend(descriptor["object_keys"].get(obj_name, []))
        return fields

    def to_dict(self) -> dict:
        """Return the essential results in a dictionary"""
        return {
            "scan_id": self.scan_id,
            "plan": self.plan_name,
            "chart_type": self.chart_type,
            "stream": self.stream_name,
            "rank": len(self.plot_axes),
            "uid7": self.uid[:7],
            "plot_signal": self.plot_signal,
            "plot_axes": self.plot_axes,
            "detectors": self.detectors,
            "positioners": self.positioners,
        }
