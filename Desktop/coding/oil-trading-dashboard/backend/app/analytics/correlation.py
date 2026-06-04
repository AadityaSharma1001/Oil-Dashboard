"""Correlation analytics — Pearson, rolling correlation, EWMA covariance."""

import numpy as np
from typing import Optional


def pearson_correlation(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def rolling_correlation(
    x: list[float], y: list[float], window: int = 60
) -> list[Optional[float]]:
    """Rolling Pearson correlation."""
    result = [None] * len(x)
    for i in range(window - 1, len(x)):
        x_win = x[i - window + 1:i + 1]
        y_win = y[i - window + 1:i + 1]
        result[i] = pearson_correlation(x_win, y_win)
    return result


def ewma_covariance(
    returns_matrix: list[list[float]], lmbda: float = 0.94
) -> tuple[list[list[float]], list[list[float]]]:
    """
    Compute EWMA covariance and correlation matrix.
    
    Args:
        returns_matrix: N series of returns, each of length T. Shape: [N, T]
        lmbda: Decay factor (RiskMetrics default: 0.94)
    
    Returns:
        (covariance_matrix, correlation_matrix) — both [N, N]
    """
    returns = np.array(returns_matrix)
    n, t = returns.shape

    # Initialize with sample covariance
    cov = np.cov(returns)

    # EWMA update
    for i in range(t):
        outer = np.outer(returns[:, i], returns[:, i])
        cov = lmbda * cov + (1 - lmbda) * outer

    # Correlation from covariance
    std = np.sqrt(np.diag(cov))
    std_outer = np.outer(std, std)
    std_outer[std_outer == 0] = 1  # Avoid division by zero
    corr = cov / std_outer

    return cov.tolist(), corr.tolist()


def ewma_variance(returns: list[float], lmbda: float = 0.94) -> list[float]:
    """EWMA variance for a single series."""
    var = [returns[0] ** 2 if returns else 0]
    for i in range(1, len(returns)):
        var.append(lmbda * var[-1] + (1 - lmbda) * returns[i] ** 2)
    return var
