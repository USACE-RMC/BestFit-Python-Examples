"""Canonical BestFit rendering with readable labels for dense CDF contours."""
from pathlib import Path


def render_plot(spec, ax=None):
    """Keep source geometry; distribute CDF contour labels and allow edge padding."""
    from bestfit_plots import render_plot as canonical_render
    import matplotlib.pyplot as plt
    import numpy as np

    if spec.get("plotId") != "bivariate.distribution" or not spec.get("variant", "").endswith("_cdf") or not any(
        series["kind"] == "contour" for series in spec["series"]
    ):
        return canonical_render(spec, ax=ax)
    own_axes = ax is None
    if own_axes:
        _, ax = plt.subplots(figsize=(10, 6.5), layout="constrained")
    original_clabel = ax.clabel
    ax.use_sticky_edges = False
    ax.margins(0.06)

    def contour_labels(contours, *args, **kwargs):
        # Automatic labels cluster at the probability-domain edges. Choose
        # separated positions on the existing contour paths, never new levels.
        segments_by_level = contours.allsegs
        populated = [segment for segments in segments_by_level for segment in segments if len(segment)]
        if not populated:
            return []
        all_vertices = np.concatenate(populated)
        xlo, xhi = all_vertices[:, 0].min(), all_vertices[:, 0].max()
        texts = []
        for index, (level, segments) in enumerate(zip(contours.levels, segments_by_level)):
            segments = [segment for segment in segments if len(segment)]
            if not segments:
                continue
            vertices = np.concatenate(segments)
            target = xlo + (xhi - xlo) * (0.8 - 0.7 * index / max(1, len(contours.levels) - 1))
            distance = abs(vertices[:, 0] - target)
            candidates = vertices[distance <= distance.min() + 0.005 * (xhi - xlo)]
            point = candidates[candidates[:, 1].argmax()]
            texts = original_clabel(contours, levels=[level], manual=[point], inline=True, fontsize=8, fmt="%.5g")
        for text in texts:
            text.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 0.5})
            text.set_zorder(5)
        return texts

    ax.clabel = contour_labels
    try:
        return canonical_render(spec, ax=ax)
    except Exception:
        if own_axes:
            plt.close(ax.figure)
        raise
    finally:
        ax.clabel = original_clabel


def export_plot(spec, output_prefix):
    """Export the same layout used by Case.plot and the notebooks."""
    import matplotlib.pyplot as plt
    figure = render_plot(spec)
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = [Path(str(prefix) + suffix) for suffix in (".png", ".svg")]
    try:
        for path in paths:
            figure.savefig(path, dpi=180, facecolor="white")
            if path.suffix == ".svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    finally:
        plt.close(figure)
    return paths
