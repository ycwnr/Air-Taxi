"""reporting/visualizer.py — matplotlib plots: GA convergence, SoC curves,
fleet Gantt chart. Kept dependency-light (matplotlib only)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_convergence(history, path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(history, color="#00B4FF", linewidth=2)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best fitness (fleet size + penalties)")
    ax.set_title("GA Convergence — Charging Station Siting")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_soc_curves(selected_cycles, path, max_cycles=12):
    fig, ax = plt.subplots(figsize=(8, 5))
    for cycle in selected_cycles[:max_cycles]:
        if not cycle.soc_trace:
            continue
        xs = list(range(1, len(cycle.soc_trace) + 1))
        ys = [s * 100 for s in cycle.soc_trace]
        ax.plot(xs, ys, marker="o", alpha=0.7, label=f"cycle#{cycle.cycle_id}")
    ax.axhline(15, color="red", linestyle="--", label="15% SoC floor")
    ax.set_xlabel("Leg number within duty cycle")
    ax.set_ylabel("State of Charge (%)")
    ax.set_title("Battery SoC Trajectories (sample of selected duty cycles)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_fleet_gantt(schedule, path):
    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(schedule))))
    for row_i, aircraft in enumerate(schedule):
        for leg in aircraft["legs"]:
            ax.barh(row_i, leg["duration_min"], left=leg["depart_min"], height=0.6,
                    color="#00B4FF", edgecolor="white")
            ax.text(leg["depart_min"] + leg["duration_min"] / 2, row_i,
                    f"{leg['from']}\u2192{leg['to']}", va="center", ha="center",
                    fontsize=6, color="black")
    ax.set_yticks(range(len(schedule)))
    ax.set_yticklabels([a["tail_no"] for a in schedule], fontsize=7)
    ax.set_xlabel("Minutes into duty cycle")
    ax.set_title("Fleet Duty-Cycle Gantt Chart")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
