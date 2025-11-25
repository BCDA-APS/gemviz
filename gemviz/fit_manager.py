"""
Fit manager for handling curve fitting operations.

This module manages fit operations for curves, handles fit parameter storage
and retrieval, and coordinates between UI and fit calculations.
"""

from typing import Optional, Tuple, Dict
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from .fit_models import FitResult, get_available_models


class FitData:
    """Container for fit data associated with a curve."""

    def __init__(
        self,
        model_name: str,
        fit_result: FitResult,
        x_range: Optional[Tuple[float, float]] = None,
    ):
        """
        Initialize fit data.

        Parameters:
        - model_name: Name of the fit model used
        - fit_result: FitResult object containing fit parameters and metrics
        - x_range: Optional range of x values used for fitting
        """
        self.model_name = model_name
        self.fit_result = fit_result
        self.x_range = x_range


class FitManager(QObject):
    """Manages fit operations for curves."""

    fitAdded = pyqtSignal(str)  # curveID
    fitUpdated = pyqtSignal(str)  # curveID
    fitRemoved = pyqtSignal(str)  # curveID

    def __init__(self, parent=None):
        """
        Initialize fit manager.

        Parameters:
        - parent: Parent QObject
        """
        super().__init__(parent)
        self._fit: dict[str, FitData] = {}  # {curveID: FitData}
        self._models = get_available_models()

    def addFit(
        self,
        curveID: str,
        model_name: str,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_range: Optional[tuple[float, float]] = None,
        initial_params: Optional[dict[str, float]] = None,
        bounds: Optional[dict[str, tuple[float, float]]] = None,
    ) -> None:
        """
        Add or replace a fit for a curve.

        Parameters:
        - curveID: ID of the curve to fit
        - model_name: Name of the fit model to use
        - x_data: X values for fitting
        - y_data: Y values for fitting
        - x_range: Optional range of x values to use for fitting
        - initial_params: Optional initial parameter guesses
        - bounds: Optional parameter bounds

        Raises:
        - ValueError: If model_name is not available or fit fails
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not available")

        model = self._models[model_name]

        # Apply x_range if specified
        if x_range is not None:
            # Ensure x_data and y_data are numpy arrays
            if not isinstance(x_data, np.ndarray):
                x_data = np.array(x_data, dtype=float)
            if not isinstance(y_data, np.ndarray):
                y_data = np.array(y_data, dtype=float)

            # Ensure arrays are contiguous
            x_data = np.ascontiguousarray(x_data, dtype=float)
            y_data = np.ascontiguousarray(y_data, dtype=float)

            # Check for valid range
            if x_range[0] >= x_range[1]:
                raise ValueError("Invalid range: start must be less than end")

            # Create mask for the range
            mask = (x_data >= x_range[0]) & (x_data <= x_range[1])

            # Check if any data points fall within the range
            if not np.any(mask):
                raise ValueError(
                    f"No data points found in range [{x_range[0]}, {x_range[1]}]"
                )

            x_fit = x_data[mask]
            y_fit = y_data[mask]
        else:
            # Ensure x_data and y_data are numpy arrays
            if not isinstance(x_data, np.ndarray):
                x_data = np.array(x_data, dtype=float)
            if not isinstance(y_data, np.ndarray):
                y_data = np.array(y_data, dtype=float)

            # Ensure arrays are contiguous
            x_data = np.ascontiguousarray(x_data, dtype=float)
            y_data = np.ascontiguousarray(y_data, dtype=float)

            x_fit = x_data
            y_fit = y_data

        # Perform the fit
        try:
            # Check for NaNs in data
            if np.isnan(x_fit).any() or np.isnan(y_fit).any():
                raise ValueError("Input data contains NaN values.")
            fit_result = model.fit(x_fit, y_fit, initial_params, bounds)
        except Exception as e:
            raise ValueError(f"Fit failed: {str(e)}")

        # Check if curve already has a fit
        had_existing_fit = curveID in self._fit

        # Store fit data (replaces existing fit if any)
        fit_data = FitData(
            model_name=model_name, fit_result=fit_result, x_range=x_range
        )

        self._fit[curveID] = fit_data

        # Emit appropriate signal
        if had_existing_fit:
            self.fitUpdated.emit(curveID)
        else:
            self.fitAdded.emit(curveID)

    def removeFit(self, curveID: str) -> None:
        """
        Remove the fit from a curve.

        Parameters:
        - curveID: ID of the curve
        """
        if curveID in self._fit:
            del self._fit[curveID]
            self.fitRemoved.emit(curveID)

    def getFitData(self, curveID: str) -> Optional[FitData]:
        """
        Get fit data for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - FitData object if found, None otherwise
        """
        return self._fit.get(curveID)

    def getFitCurveData(self, curveID: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get the fitted curve data for plotting.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Tuple of (x_fit, y_fit) arrays if found, None otherwise
        """
        fit_data = self.getFitData(curveID)
        if not fit_data:
            return None

        # Get the mmodel
        available_models = get_available_models()
        model = available_models.get(fit_data.model_name)
        if not model:
            # Falls back to original data if model not found
            return fit_data.fit_result.x_fit, fit_data.fit_result.fit_curve

        # Get parameters
        parameters = fit_data.fit_result.parameters

        # Determine x range for smooth curve
        x_original = fit_data.fit_result.x_fit
        x_min, x_max = np.min(x_original), np.max(x_original)

        # Generate smooth x array (500 points for smooth plotting)
        num_points = 500
        x_smooth = np.linspace(x_min, x_max, num_points)

        # Evaluate the fit function at smooth points
        # Convert parameters dict to ordered list matching model.parameters
        param_values = [parameters[param] for param in model.parameters]
        y_smooth = model.function(x_smooth, *param_values)

        return x_smooth, y_smooth

    def getFitParameters(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameters for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of parameter names and values if found, None otherwise
        """
        fit_data = self.getFitData(curveID)
        return fit_data.fit_result.parameters if fit_data else None

    def getFitUncertainties(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit parameter uncertainties for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of parameter names and uncertainties if found, None otherwise
        """
        fit_data = self.getFitData(curveID)
        return fit_data.fit_result.uncertainties if fit_data else None

    def getFitQualityMetrics(self, curveID: str) -> Optional[Dict[str, float]]:
        """
        Get fit quality metrics for a curve.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - Dictionary of quality metrics if found, None otherwise
        """
        fit_data = self.getFitData(curveID)
        if fit_data:
            return {
                "r_squared": fit_data.fit_result.r_squared,
                "chi_squared": fit_data.fit_result.chi_squared,
                "reduced_chi_squared": fit_data.fit_result.reduced_chi_squared,
            }
        return None

    def hasFit(self, curveID: str) -> bool:
        """
        Check if a curve has a fit.

        Parameters:
        - curveID: ID of the curve

        Returns:
        - True if curve has a fit, False otherwise
        """
        return curveID in self._fit
