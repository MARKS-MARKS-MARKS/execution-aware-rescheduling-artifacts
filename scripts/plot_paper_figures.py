#!/usr/bin/env python3
"""Generate formal paper Tables II--III and Figs. 3--4.

The figure functions are the portable versions of the functions used to
produce the manuscript assets in ``generate_final_review_figures.py``.
"""
from __future__ import annotations

import csv
import os
import tempfile
from functools import wraps
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "execution-aware-artifact-matplotlib"),
)

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.transforms import Bbox

from paper_aggregation import (
    METHOD_LABEL,
    METHOD_ORDER,
    event_case_summary,
    method_summary,
    objective_tradeoff,
    progress_summary,
)


FIGURE_FONT = {
    "font.family": "Times New Roman",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
}
PROGRESS_FONT_SIZE = 11.6
PROGRESS_FONT = {
    **FIGURE_FONT,
    "font.size": PROGRESS_FONT_SIZE,
    "axes.labelsize": PROGRESS_FONT_SIZE,
    "axes.titlesize": PROGRESS_FONT_SIZE,
    "xtick.labelsize": PROGRESS_FONT_SIZE,
    "ytick.labelsize": PROGRESS_FONT_SIZE,
    "legend.fontsize": PROGRESS_FONT_SIZE,
}
TARGET_BBOX_PT = {
    "experiment_tradeoffs": {
        "pdf": (518.16, 213.294),
        "svg": (518.15952, 211.591828),
    },
    "progress_sensitivity": {
        "pdf": (328.8, 206.696),
        "svg": (328.79952, 206.417115),
    },
}


def require_paper_font() -> None:
    try:
        font_manager.findfont("Times New Roman", fallback_to_default=False)
    except ValueError as error:
        raise RuntimeError(
            "Times New Roman is required to reproduce the paper figures"
        ) from error


def with_figure_font(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with plt.rc_context(FIGURE_FONT):
            return function(*args, **kwargs)

    return wrapped


def with_progress_font(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with plt.rc_context(PROGRESS_FONT):
            return function(*args, **kwargs)

    return wrapped


def save(fig, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = TARGET_BBOX_PT[stem]
    fig.canvas.draw()
    tight = fig.get_tightbbox(fig.canvas.get_renderer())
    for extension in ("pdf", "svg"):
        width_pt, height_pt = targets[extension]
        width_in, height_in = width_pt / 72, height_pt / 72
        fixed = Bbox.from_bounds(
            tight.x0 - (width_in - tight.width) / 2,
            tight.y0 - (height_in - tight.height) / 2,
            width_in,
            height_in,
        )
        fig.savefig(output_dir / f"{stem}.{extension}", bbox_inches=fixed)
    plt.close(fig)


def progress_lookup(
    records: list[dict[str, str]],
) -> dict[tuple[str, float], float]:
    return {
        (str(row["method"]), float(row["progress"])): float(row["time_ms"])
        for row in progress_summary(records)
    }


@with_progress_font
def progress_sensitivity(
    records: list[dict[str, str]], output_dir: Path
) -> None:
    data = progress_lookup(records)
    styles = {
        "greedy": {
            "marker": "o",
            "linestyle": "-",
            "color": "0.10",
            "markerfacecolor": "white",
            "zorder": 3,
        },
        "greedy_ls": {
            "marker": "s",
            "linestyle": "--",
            "color": "0.35",
            "markerfacecolor": "0.80",
            "zorder": 4,
        },
        "dynamic_ails": {
            "marker": "^",
            "linestyle": "-.",
            "color": "0.00",
            "markerfacecolor": "black",
            "zorder": 7,
        },
        "global_replan": {
            "marker": "D",
            "linestyle": ":",
            "color": "0.50",
            "markerfacecolor": "white",
            "zorder": 6,
        },
    }
    progress = (0.25, 0.50, 0.75)
    fig, axis = plt.subplots(figsize=(4.45, 2.75), constrained_layout=True)
    for method in METHOD_ORDER:
        axis.plot(
            progress,
            [data[(method, value)] for value in progress],
            label=METHOD_LABEL[method],
            linewidth=1.35,
            markersize=5.0,
            markeredgewidth=0.9,
            **styles[method],
        )
    axis.set(
        xlabel="Route-local execution progress",
        ylabel="Online replanning time (ms)",
        yscale="log",
        xticks=progress,
        xticklabels=("25%", "50%", "75%"),
    )
    axis.grid(color="0.84", linewidth=0.45, which="both")
    axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        frameon=True,
        framealpha=0.96,
        ncol=2,
        fontsize=PROGRESS_FONT_SIZE,
        columnspacing=0.8,
        handletextpad=0.4,
        labelspacing=0.25,
    )
    save(fig, output_dir, "progress_sensitivity")


@with_figure_font
def experiment_tradeoffs(
    records: list[dict[str, str]], output_dir: Path
) -> None:
    methods = method_summary(records)
    tradeoff = objective_tradeoff(records)
    style = {
        "greedy": {
            "marker": "o",
            "facecolors": "white",
            "edgecolors": "black",
        },
        "greedy_ls": {
            "marker": "s",
            "facecolors": "0.75",
            "edgecolors": "black",
        },
        "dynamic_ails": {
            "marker": "^",
            "facecolors": "black",
            "edgecolors": "black",
        },
        "global_replan": {
            "marker": "D",
            "facecolors": "white",
            "edgecolors": "0.25",
        },
    }
    offsets = {
        "greedy": (6, 7),
        "greedy_ls": (6, -11),
        "dynamic_ails": (6, 7),
        "global_replan": (-58, -13),
    }
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(7.08, 2.82), constrained_layout=True
    )
    for row in methods:
        method = str(row["method"])
        left.scatter(
            float(row["time_ms"]),
            float(row["cost"]),
            s=40,
            linewidths=0.9,
            zorder=4,
            **style[method],
        )
        left.annotate(
            str(row["label"]),
            (float(row["time_ms"]), float(row["cost"])),
            xytext=offsets[method],
            textcoords="offset points",
            fontsize=8,
        )
    left.set(
        xlabel="Online replanning time (ms)",
        ylabel="Maximum cumulative route cost",
        xscale="log",
    )
    left.grid(color="0.84", linewidth=0.45, which="both")
    left.set_title(
        "(a) Online replanning time versus route cost", fontsize=8
    )

    x = (0, 1)
    width = 0.22
    metrics = (
        ("reassigned", "Reassigned tasks", "//", "0.83"),
        ("changed_locations", "Optional location changes", "xx", "0.63"),
        ("changed_edges", "Changed suffix edges", "..", "0.42"),
    )
    bars = []
    for offset, (field, label, hatch, shade) in zip(
        (-width, 0.0, width), metrics
    ):
        container = right.bar(
            [value + offset for value in x],
            [float(row[field]) for row in tradeoff],
            width=width,
            color=shade,
            edgecolor="black",
            linewidth=0.6,
            hatch=hatch,
            label=label,
        )
        bars.append(container[0])
    right.set(
        xticks=x,
        xticklabels=[str(row["label"]) for row in tradeoff],
        ylabel="Plan-change count",
    )
    right.grid(axis="y", color="0.84", linewidth=0.45)
    twin = right.twinx()
    (cost_line,) = twin.plot(
        x,
        [float(row["cost"]) for row in tradeoff],
        color="black",
        marker="D",
        markerfacecolor="white",
        markeredgewidth=0.9,
        linewidth=1.25,
        markersize=5,
        label="Maximum cumulative route cost",
        zorder=5,
    )
    twin.set_ylabel("Maximum cumulative route cost")
    right.legend(
        [*bars, cost_line],
        [item[1] for item in metrics]
        + ["Maximum cumulative route cost"],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=2,
        frameon=True,
        framealpha=0.96,
        fontsize=8,
        columnspacing=0.8,
        handletextpad=0.4,
        labelspacing=0.25,
    )
    right.set_title("(b) D-AILS objective trade-off", fontsize=8)
    save(fig, output_dir, "experiment_tradeoffs")


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_tables(records: list[dict[str, str]], output_dir: Path) -> None:
    recovery = event_case_summary(records)
    methods = method_summary(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "event_recovery.csv", recovery)
    write_csv(output_dir / "method_results.csv", methods)

    event_lines = [
        "\\begin{table}[!b]",
        "\\centering",
        "\\caption{Feasibility over distinct scenario cases and algorithm runs.}",
        "\\label{tab:event-recovery}",
        "\\setlength{\\tabcolsep}{5pt}",
        "\\begin{tabular}{lcc}",
        "\\toprule",
        "Event",
        "& \\shortstack{Feasible\\\\scenario cases}",
        "& \\shortstack{Successful\\\\algorithm runs} \\\\",
        "\\midrule",
    ]
    event_lines += [
        f"{row['label']} & {int(row['feasible_cases'])}/"
        f"{int(row['total_cases'])} & {int(row['successful_runs'])}/"
        f"{int(row['total_runs'])} \\\\"
        for row in recovery
    ]
    event_lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    (output_dir / "event_tradeoff.tex").write_text(
        "\n".join(event_lines), encoding="utf-8"
    )

    lowest = min(float(row["cost"]) for row in methods)
    method_lines = [
        "\\begin{table}[!b]",
        "\\centering",
        "\\caption{Primary-objective results on the 66 scenario cases "
        "feasible for all four methods.}",
        "\\label{tab:method-results}",
        "\\footnotesize",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\renewcommand{\\arraystretch}{1.0}",
        "\\begin{tabular}{@{}lrrrrr@{}}",
        "\\toprule",
        "Method",
        "& \\shortstack{Max.\\\\cumulative\\\\route cost}",
        "& \\shortstack{Online\\\\time (ms)}",
        "& \\shortstack{Reassigned\\\\tasks}",
        "& \\shortstack{Optional\\\\location\\\\changes}",
        "& \\shortstack{Changed\\\\suffix\\\\edges} \\\\",
        "\\midrule",
    ]
    for row in methods:
        cost = f"{float(row['cost']):.3f}"
        if abs(float(row["cost"]) - lowest) < 1e-12:
            cost = f"\\textbf{{{cost}}}"
        method_lines.append(
            f"{row['label']} & {cost} & {float(row['time_ms']):.3f} & "
            f"{float(row['reassigned']):.3f} & "
            f"{float(row['changed_locations']):.3f} & "
            f"{float(row['changed_edges']):.3f} \\\\"
        )
    method_lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    (output_dir / "method_results.tex").write_text(
        "\n".join(method_lines), encoding="utf-8"
    )


def write_figure_data(
    records: list[dict[str, str]], output_dir: Path
) -> None:
    write_csv(output_dir / "progress_sensitivity.csv", progress_summary(records))
    write_csv(output_dir / "objective_tradeoff.csv", objective_tradeoff(records))
    write_csv(output_dir / "method_tradeoff.csv", method_summary(records))


def generate_all(records: list[dict[str, str]], output_root: Path) -> None:
    require_paper_font()
    write_tables(records, output_root / "tables")
    write_figure_data(records, output_root / "figure_data")
    experiment_tradeoffs(records, output_root / "figures")
    progress_sensitivity(records, output_root / "figures")
