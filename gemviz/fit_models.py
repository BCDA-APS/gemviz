"""
Fit models for curve fitting functionality.

This module provides common fit functions and parameter management
for curve fitting in the gemviz application.
"""

from typing import Optional, Any, Callable
import numpy as np
from scipy.optimize import curve_fit


class FitResult:
    """Container for fit results."""

    def __init__(
        self,
        parameters: dict[str, float],
        uncertainties: dict[str, float],
        r_squared: float,
        chi_squared: float,
        reduced_chi_squared: float,
        fit_curve: np.ndarray,
        x_fit: np.ndarray,
    ):
        """
        Initialize fit result.

        Parameters:
        - parameters: Dictionary of fit parameter names and values
        - uncertainties: Dictionary of parameter uncertainties
        - r_squared: R-squared value for fit quality
        - chi_squared: Chi-squared value
        - reduced_chi_squared: Reduced chi-squared value
        - fit_curve: Y values of the fitted curve
        - x_fit: X values used for fitting
        """
        self.parameters = parameters
        self.uncertainties = uncertainties
        self.r_squared = r_squared
        self.chi_squared = chi_squared
        self.reduced_chi_squared = reduced_chi_squared
        self.fit_curve = fit_curve
        self.x_fit = x_fit


class FitModel:
    """Base class for fit models."""

    def __init__(self, name: str, function: Callable, parameters: list[str]):
        """
        Initialize fit model.

        Parameters:
        - name: Display name for the model
        - function: The fitting function
        - parameters: List of parameter names
        """
        self.name = name
        self.function = function
        self.parameters = parameters

    def fit(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        initial_guess: Optional[dict[str, float]] = None,
        bounds: Optional[dict[str, tuple[float, float]]] = None,
    ) -> FitResult:
        """
        Perform fit and return results.

        Parameters:
        - x_data: X values for fitting
        - y_data: Y values for fitting
        - initial_guess: Initial parameter guesses
        - bounds: Parameter bounds (min, max) for each parameter

        Returns:
        - FitResult object with fit parameters and quality metrics
        """
        # Remove any NaN or infinite values
        mask = np.isfinite(x_data) & np.isfinite(y_data)
        x_clean = x_data[mask]
        y_clean = y_data[mask]

        if len(x_clean) < len(self.parameters):
            raise ValueError(
                f"Not enough data points for {len(self.parameters)} parameters"
            )

        # Set default initial guesses if not provided
        if initial_guess is None:
            initial_guess = self._get_default_initial_guess(x_clean, y_clean)

        # Prepare bounds for scipy.curve_fit
        if bounds is not None:
            p0 = [initial_guess.get(param, 1.0) for param in self.parameters]
            bounds_lower = [
                bounds.get(param, (-np.inf, np.inf))[0] for param in self.parameters
            ]
            bounds_upper = [
                bounds.get(param, (-np.inf, np.inf))[1] for param in self.parameters
            ]
            bounds_tuple: tuple[Any, Any] = (bounds_lower, bounds_upper)
        else:
            p0 = [initial_guess.get(param, 1.0) for param in self.parameters]
            bounds_tuple_unbounded: tuple[Any, Any] = (-np.inf, np.inf)
            bounds_tuple = bounds_tuple_unbounded

        try:
            # Perform the fit
            popt, pcov = curve_fit(
                self.function,
                x_clean,
                y_clean,
                p0=p0,
                bounds=bounds_tuple,
                maxfev=10000,
            )

            # Calculate uncertainties
            perr = np.sqrt(np.diag(pcov)) if pcov is not None else np.zeros(len(popt))

            # Calculate fit curve
            y_fit = self.function(x_clean, *popt)

            # Calculate quality metrics
            residuals = y_clean - y_fit
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            chi_squared = np.sum(residuals**2)
            reduced_chi_squared = (
                chi_squared / (len(x_clean) - len(popt))
                if len(x_clean) > len(popt)
                else np.inf
            )

            # Create parameter dictionaries
            parameters = dict(zip(self.parameters, popt))
            uncertainties = dict(zip(self.parameters, perr))

            return FitResult(
                parameters=parameters,
                uncertainties=uncertainties,
                r_squared=r_squared,
                chi_squared=chi_squared,
                reduced_chi_squared=reduced_chi_squared,
                fit_curve=y_fit,
                x_fit=x_clean,
            )

        except (RuntimeError, ValueError) as e:
            raise ValueError(f"Fit failed: {str(e)}")

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """
        Get default initial parameter guesses.

        Parameters:
        - x_data: X values
        - y_data: Y values

        Returns:
        - Dictionary of parameter names and default values
        """
        return {param: 1.0 for param in self.parameters}


class GaussianFit(FitModel):
    """Gaussian fit model."""

    def __init__(self):
        """Initialize Gaussian fit model."""
        super().__init__(
            "Gaussian",
            self._gaussian_function,
            ["amplitude", "center", "sigma", "offset"],
        )

    def _gaussian_function(
        self,
        x: np.ndarray,
        amplitude: float,
        center: float,
        sigma: float,
        offset: float,
    ) -> np.ndarray:
        """
        Gaussian function.

        Parameters:
        - x: X values
        - amplitude: Peak amplitude
        - center: Center position
        - sigma: Standard deviation
        - offset: Vertical offset

        Returns:
        - Y values of Gaussian function
        """
        return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma**2)) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for Gaussian fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_max_idx = np.argmax(y_data)
        x_max = x_data[x_max_idx]

        # Estimate sigma from FWHM
        half_max = (y_max + y_min) / 2
        left_idx = np.where(y_data <= half_max)[0]
        if len(left_idx) > 0:
            left_idx = left_idx[left_idx < x_max_idx]
            if len(left_idx) > 0:
                left_x = x_data[left_idx[-1]]
                right_idx = np.where(y_data <= half_max)[0]
                right_idx = right_idx[right_idx > x_max_idx]
                if len(right_idx) > 0:
                    right_x = x_data[right_idx[0]]
                    fwhm = right_x - left_x
                    sigma_est = fwhm / (2 * np.sqrt(2 * np.log(2)))
                else:
                    sigma_est = (x_data[-1] - x_data[0]) / 10
            else:
                sigma_est = (x_data[-1] - x_data[0]) / 10
        else:
            sigma_est = (x_data[-1] - x_data[0]) / 10

        return {
            "amplitude": y_max - y_min,
            "center": x_max,
            "sigma": sigma_est,
            "offset": y_min,
        }


class NegativeGaussianFit(FitModel):
    """Negative Gaussian fit model (for valleys/dips)."""

    def __init__(self):
        """Initialize negative Gaussian fit model."""
        super().__init__(
            "Negative Gaussian",
            self._gaussian_function,  # Same function, just negative amplitude
            ["amplitude", "center", "sigma", "offset"],
        )

    def _gaussian_function(
        self,
        x: np.ndarray,
        amplitude: float,
        center: float,
        sigma: float,
        offset: float,
    ) -> np.ndarray:
        """Same as Gaussian - amplitude will be negative."""
        return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma**2)) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for negative Gaussian fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_min_idx = np.argmin(y_data)
        x_min = x_data[x_min_idx]

        # Always assume negative peak (valley)
        amplitude = y_min - y_max  # negative
        center = x_min
        offset = y_max  # baseline

        # Estimate sigma from FWHM (similar to Gaussian but use x_min_idx)
        half_max = (y_max + y_min) / 2
        left_idx = np.where(y_data <= half_max)[0]
        if len(left_idx) > 0:
            left_idx = left_idx[left_idx < x_min_idx]
            if len(left_idx) > 0:
                left_x = x_data[left_idx[-1]]
                right_idx = np.where(y_data <= half_max)[0]
                right_idx = right_idx[right_idx > x_min_idx]
                if len(right_idx) > 0:
                    right_x = x_data[right_idx[0]]
                    fwhm = right_x - left_x
                    sigma_est = fwhm / (2 * np.sqrt(2 * np.log(2)))
                else:
                    sigma_est = (x_data[-1] - x_data[0]) / 10
            else:
                sigma_est = (x_data[-1] - x_data[0]) / 10
        else:
            sigma_est = (x_data[-1] - x_data[0]) / 10

        return {
            "amplitude": amplitude,
            "center": center,
            "sigma": sigma_est,
            "offset": offset,
        }


class LorentzianFit(FitModel):
    """Lorentzian fit model."""

    def __init__(self):
        """Initialize Lorentzian fit model."""
        super().__init__(
            "Lorentzian",
            self._lorentzian_function,
            ["amplitude", "center", "gamma", "offset"],
        )

    def _lorentzian_function(
        self,
        x: np.ndarray,
        amplitude: float,
        center: float,
        gamma: float,
        offset: float,
    ) -> np.ndarray:
        """
        Lorentzian function.

        Parameters:
        - x: X values
        - amplitude: Peak amplitude
        - center: Center position
        - gamma: Half-width at half-maximum
        - offset: Vertical offset

        Returns:
        - Y values of Lorentzian function
        """
        return amplitude * gamma**2 / ((x - center) ** 2 + gamma**2) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for Lorentzian fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_max_idx = np.argmax(y_data)
        x_max = x_data[x_max_idx]

        # Estimate gamma from FWHM
        half_max = (y_max + y_min) / 2
        left_idx = np.where(y_data <= half_max)[0]
        if len(left_idx) > 0:
            left_idx = left_idx[left_idx < x_max_idx]
            if len(left_idx) > 0:
                left_x = x_data[left_idx[-1]]
                right_idx = np.where(y_data <= half_max)[0]
                right_idx = right_idx[right_idx > x_max_idx]
                if len(right_idx) > 0:
                    right_x = x_data[right_idx[0]]
                    fwhm = right_x - left_x
                    gamma_est = fwhm / 2
                else:
                    gamma_est = (x_data[-1] - x_data[0]) / 10
            else:
                gamma_est = (x_data[-1] - x_data[0]) / 10
        else:
            gamma_est = (x_data[-1] - x_data[0]) / 10

        return {
            "amplitude": y_max - y_min,
            "center": x_max,
            "gamma": gamma_est,
            "offset": y_min,
        }


class NegativeLorentzianFit(FitModel):
    """Negative Lorentzian fit model (for valleys/dips)."""

    def __init__(self):
        """Initialize negative Lorentzian fit model."""
        super().__init__(
            "Negative Lorentzian",
            self._lorentzian_function,  # Same function, just negative amplitude
            ["amplitude", "center", "gamma", "offset"],
        )

    def _lorentzian_function(
        self,
        x: np.ndarray,
        amplitude: float,
        center: float,
        gamma: float,
        offset: float,
    ) -> np.ndarray:
        """Same as Lorentzian - amplitude will be negative."""
        return amplitude * gamma**2 / ((x - center) ** 2 + gamma**2) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for negative Lorentzian fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_min_idx = np.argmin(y_data)
        x_min = x_data[x_min_idx]

        # Always assume negative peak (valley)
        amplitude = y_min - y_max  # negative
        center = x_min
        offset = y_max  # baseline

        # Estimate gamma from FWHM (similar to Lorentzian but use x_min_idx)
        half_max = (y_max + y_min) / 2
        left_idx = np.where(y_data <= half_max)[0]
        if len(left_idx) > 0:
            left_idx = left_idx[left_idx < x_min_idx]
            if len(left_idx) > 0:
                left_x = x_data[left_idx[-1]]
                right_idx = np.where(y_data <= half_max)[0]
                right_idx = right_idx[right_idx > x_min_idx]
                if len(right_idx) > 0:
                    right_x = x_data[right_idx[0]]
                    fwhm = right_x - left_x
                    gamma_est = fwhm / 2
                else:
                    gamma_est = (x_data[-1] - x_data[0]) / 10
            else:
                gamma_est = (x_data[-1] - x_data[0]) / 10
        else:
            gamma_est = (x_data[-1] - x_data[0]) / 10

        return {
            "amplitude": amplitude,
            "center": center,
            "gamma": gamma_est,
            "offset": offset,
        }


class LinearFit(FitModel):
    """Linear fit model."""

    def __init__(self):
        """Initialize linear fit model."""
        super().__init__("Linear", self._linear_function, ["slope", "intercept"])

    def _linear_function(
        self, x: np.ndarray, slope: float, intercept: float
    ) -> np.ndarray:
        """
        Linear function.

        Parameters:
        - x: X values
        - slope: Slope of the line
        - intercept: Y-intercept

        Returns:
        - Y values of linear function
        """
        return slope * x + intercept

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for linear fit."""
        # Use numpy's polyfit for initial estimates
        coeffs = np.polyfit(x_data, y_data, 1)
        return {"slope": coeffs[0], "intercept": coeffs[1]}


class ExponentialFit(FitModel):
    """Exponential fit model."""

    def __init__(self):
        """Initialize exponential fit model."""
        super().__init__(
            "Exponential", self._exponential_function, ["amplitude", "decay", "offset"]
        )

    def _exponential_function(
        self, x: np.ndarray, amplitude: float, decay: float, offset: float
    ) -> np.ndarray:
        """
        Exponential function.

        Parameters:
        - x: X values
        - amplitude: Initial amplitude
        - decay: Decay constant
        - offset: Vertical offset

        Returns:
        - Y values of exponential function
        """
        return amplitude * np.exp(-decay * x) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for exponential fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_range = x_data[-1] - x_data[0]

        return {
            "amplitude": y_max - y_min,
            "decay": 1.0 / x_range if x_range > 0 else 1.0,
            "offset": y_min,
        }


class PolynomialFit(FitModel):
    """Polynomial fit model."""

    def __init__(self, degree: int = 2):
        """
        Initialize polynomial fit model.

        Parameters:
        - degree: Degree of the polynomial (default: 2 for quadratic)
        """
        self.degree = degree
        param_names = [f"coeff_{i}" for i in range(degree + 1)]
        super().__init__(
            f"Polynomial (deg={degree})", self._polynomial_function, param_names
        )

    def _polynomial_function(self, x: np.ndarray, *coefficients: float) -> np.ndarray:
        """
        Polynomial function.

        Parameters:
        - x: X values
        - coefficients: Polynomial coefficients (highest degree first)

        Returns:
        - Y values of polynomial function
        """
        return np.polyval(coefficients[::-1], x)  # Reverse coefficients for polyval

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for polynomial fit."""
        # Use numpy's polyfit for initial estimates
        coeffs = np.polyfit(x_data, y_data, self.degree)
        return {f"coeff_{i}": coeff for i, coeff in enumerate(coeffs[::-1])}


class ErrorFunctionFit(FitModel):
    """Error function fit model."""

    def __init__(self):
        """Initialize error function fit model."""
        super().__init__(
            "Error Function",
            self._error_function,
            ["amplitude", "center", "sigma", "offset"],
        )

    def _error_function(
        self,
        x: np.ndarray,
        amplitude: float,
        center: float,
        sigma: float,
        offset: float,
    ) -> np.ndarray:
        """
        Error function (erf) with scaling and offset.

        Parameters:
        - x: X values
        - amplitude: Amplitude scaling factor
        - center: Center position (shift)
        - sigma: Width parameter
        - offset: Vertical offset

        Returns:
        - Y values of error function
        """
        from scipy.special import erf

        return amplitude * erf((x - center) / (sigma * np.sqrt(2))) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for error function fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_range = x_data[-1] - x_data[0]

        # Estimate center as midpoint of data range
        center_est = (x_data[0] + x_data[-1]) / 2

        # Estimate sigma as 1/4 of the data range
        sigma_est = x_range / 4 if x_range > 0 else 1.0

        return {
            "amplitude": (y_max - y_min) / 2,  # erf goes from -1 to 1, so scale by 2
            "center": center_est,
            "sigma": sigma_est,
            "offset": (y_max + y_min) / 2,  # Center the function
        }


class TopHatFit(FitModel):
    """Top-hat fit model (difference of two error functions)."""

    def __init__(self):
        """Initialize top-hat fit model."""
        super().__init__(
            "Top Hat",
            self._tophat_function,
            ["amplitude", "a", "b", "sigma", "offset"],
        )

    def _tophat_function(
        self,
        x: np.ndarray,
        amplitude: float,
        a: float,
        b: float,
        sigma: float,
        offset: float,
    ) -> np.ndarray:
        """
        Top-hat function (difference of two error functions).

        Parameters:
        - x: X values
        - amplitude: Amplitude scaling factor
        - a: Left edge position
        - b: Right edge position
        - sigma: Width parameter
        - offset: Vertical offset

        Returns:
        - Y values of top-hat function
        """
        from scipy.special import erf

        return (amplitude / 2) * (
            erf((x - a) / (sigma * np.sqrt(2))) - erf((x - b) / (sigma * np.sqrt(2)))
        ) + offset

    def _get_default_initial_guess(
        self, x_data: np.ndarray, y_data: np.ndarray
    ) -> dict[str, float]:
        """Get default initial guesses for top-hat fit."""
        y_max = np.max(y_data)
        y_min = np.min(y_data)
        x_range = x_data[-1] - x_data[0]

        # Estimate edges at 1/4 and 3/4 of the data range
        a_est = x_data[0] + x_range / 4
        b_est = x_data[0] + 3 * x_range / 4

        # Estimate sigma as 1/10 of the data range
        sigma_est = x_range / 10 if x_range > 0 else 1.0

        return {
            "amplitude": y_max - y_min,
            "a": a_est,
            "b": b_est,
            "sigma": sigma_est,
            "offset": y_min,
        }


# Factory function to get available fit models
def get_available_models() -> dict[str, FitModel]:
    """
    Get dictionary of available fit models.

    Returns:
    - Dictionary mapping model names to FitModel instances
    """
    return {
        "Gaussian": GaussianFit(),
        "Lorentzian": LorentzianFit(),
        "Negative Gaussian": NegativeGaussianFit(),
        "Negative Lorentzian": NegativeLorentzianFit(),
        "Linear": LinearFit(),
        "Exponential": ExponentialFit(),
        "Quadratic": PolynomialFit(degree=2),
        "Cubic": PolynomialFit(degree=3),
        "Error Function": ErrorFunctionFit(),
        "Top Hat": TopHatFit(),
    }
