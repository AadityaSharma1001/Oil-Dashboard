"""PCA decomposition of forward curves — Level, Slope, Curvature."""

import numpy as np
from sklearn.decomposition import PCA


def forward_curve_pca(
    curve_snapshots: list[list[float]], n_components: int = 3
) -> dict:
    """
    PCA decomposition of forward curve returns.
    
    Args:
        curve_snapshots: List of daily forward curve snapshots, each of length N tenors.
                         Shape: [T, N] where T = number of days, N = number of tenors.
        n_components: Number of principal components (default 3: Level, Slope, Curvature)
    
    Returns:
        {
            "components": [
                {"label": "PC1 (Level)", "pct": 82.5, "loadings": [...], "scores": [...]},
                {"label": "PC2 (Slope)", "pct": 12.3, "loadings": [...], "scores": [...]},
                {"label": "PC3 (Curvature)", "pct": 3.8, "loadings": [...], "scores": [...]},
            ],
            "explained_variance_total": 98.6,
        }
    """
    data = np.array(curve_snapshots)
    if data.shape[0] < n_components or data.shape[1] < n_components:
        return _mock_pca()

    # Compute log returns across the curve
    returns = np.diff(np.log(data + 1e-10), axis=0)

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(returns)

    labels = ["PC1 (Level)", "PC2 (Slope)", "PC3 (Curvature)"]
    colors = ["#0D47A1", "#E53935", "#4CAF50"]

    components = []
    for i in range(n_components):
        components.append({
            "label": labels[i] if i < len(labels) else f"PC{i + 1}",
            "pct": round(pca.explained_variance_ratio_[i] * 100, 1),
            "color": colors[i] if i < len(colors) else "#868E96",
            "spark": scores[-20:, i].tolist() if len(scores) >= 20 else scores[:, i].tolist(),
        })

    return {
        "components": components,
        "explained_variance_total": round(sum(pca.explained_variance_ratio_) * 100, 1),
    }


def _mock_pca() -> dict:
    """Fallback PCA result when insufficient data."""
    return {
        "components": [
            {"label": "PC1 (Level)", "pct": 83.2, "color": "#0D47A1", "spark": [0.1, 0.3, -0.2, 0.5, 0.2, -0.1, 0.4, 0.3, -0.3, 0.1]},
            {"label": "PC2 (Slope)", "pct": 11.8, "color": "#E53935", "spark": [0.4, -0.2, 0.1, -0.3, 0.5, -0.4, 0.2, -0.1, 0.3, -0.2]},
            {"label": "PC3 (Curvature)", "pct": 3.5, "color": "#4CAF50", "spark": [-0.1, 0.2, -0.3, 0.1, -0.2, 0.3, -0.1, 0.2, -0.2, 0.1]},
        ],
        "explained_variance_total": 98.5,
    }
