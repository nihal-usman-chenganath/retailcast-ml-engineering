"""Export the implemented local architecture as PNG/SVG portfolio artifacts."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402


def main():
    root = Path(__file__).resolve().parents[1]
    plt.rcParams["svg.fonttype"] = "none"
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set(xlim=(0, 13), ylim=(0, 8))
    ax.axis("off")
    ax.text(.3, 7.6, "RetailCast: from transactions to a versioned forecast", fontsize=18,
            fontweight="bold", color="#17385C")
    ax.text(.3, 7.2, "Implemented local system • Historical replay • Forecast limits documented",
            fontsize=11, color="#555555")

    def box(x, y, title, detail, color="#EAF1F8"):
        ax.add_patch(FancyBboxPatch((x, y), 3.5, 1.15, boxstyle="round,pad=0.12",
                                   facecolor=color, edgecolor="#2463A6", linewidth=1.2))
        ax.text(x + 1.75, y + .78, title, fontsize=12, fontweight="bold", ha="center", va="center", color="#17385C")
        ax.text(x + 1.75, y + .34, detail, fontsize=10, ha="center", va="center", color="#333333")

    def arrow(start, end, connection="arc3"):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=17,
                                    linewidth=1.6, color="#57718A", connectionstyle=connection))

    box(.4, 5.55, "Original retail workbook", "UCI data • Attribution recorded")
    box(4.6, 5.55, "Validate and prepare", "Daily histories • Time-safe splits")
    box(8.8, 5.55, "Compare and track", "Baselines + Ridge/forest • MLflow")
    arrow((4.0, 6.1), (4.4, 6.1))
    arrow((8.2, 6.1), (8.6, 6.1))
    box(.4, 3.4, "Client request", "Product code + forecast date")
    box(4.6, 3.4, "FastAPI service", "Pydantic • Shared history features")
    box(8.8, 3.4, "Verified serving bundle", "Saved pipeline • Metadata • History")
    arrow((4.0, 3.95), (4.4, 3.95))
    arrow((8.2, 3.95), (8.6, 3.95))
    arrow((10.55, 5.45), (10.55, 4.7))
    box(4.6, 1.5, "Prediction response", "Seven-day units + exact model version")
    arrow((10.55, 3.25), (8.2, 2.2), "arc3,rad=-0.25")
    ax.text(6.35, 2.95, "Historical dates only; earlier sales supply inputs",
            fontsize=10, color="#555555", ha="center")
    ax.add_patch(FancyBboxPatch((.4, .25), 11.9, .65, boxstyle="round,pad=0.12",
                               facecolor="#FFF4E8", edgecolor="#CB651D"))
    ax.text(6.35, .57, "Docker local deployment • Tests + lint • Logs + timing counters\n"
            "GitHub Actions: lint, 54 tests, Docker build, and HTTP smoke checks passed",
            ha="center", va="center", fontsize=10, color="#713F12")
    directory = root / "reports/figures"
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "svg"]:
        output = directory / f"retailcast-architecture.{extension}"
        fig.savefig(output, dpi=180,
                    bbox_inches="tight", facecolor="white")
        if extension == "svg":
            output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
    plt.close(fig)
    print("Exported architecture PNG and editable SVG.")


if __name__ == "__main__":
    main()
