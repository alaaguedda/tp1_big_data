"""
TP02 - Pandas vs Chunking vs Dask on a multi-GB CSV (CPU only).

Each method runs in its own process. A guard watches the RAM: if the PC reaches
80 % the method is killed ("SKIPPED") and the next method starts.
At the end a dark chart is saved as benchmark_comparison.png.

Run:  python tp02_benchmark.py                       (CSV expected at data/HIGGS.csv)
      python tp02_benchmark.py data/HIGGS.csv 60     (custom file, custom RAM limit %)
"""
import multiprocessing as mp
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import psutil

CSV = sys.argv[1] if len(sys.argv) > 1 else "data/HIGGS.csv"
RAM_LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else 80   # kill a method at this RAM %
CHUNK = 100_000                                               # rows per chunk (method 2)


# ---------------- The 3 methods: each one computes the mean of every column ----------------
def pandas_full(q):
    import pandas as pd
    df = pd.read_csv(CSV, header=None)               # the WHOLE file goes into RAM
    df.mean()
    q.put("done")


def pandas_chunks(q):
    import pandas as pd
    rows, total = 0, 0
    for chunk in pd.read_csv(CSV, header=None, chunksize=CHUNK):   # a small piece at a time
        rows += len(chunk)
        total = total + chunk.sum()                  # keep only the running sum
    total / rows
    q.put("done")


def dask_blocks(q):
    import dask
    import dask.dataframe as dd
    free_gb = psutil.virtual_memory().available / 2**30
    ddf = dd.read_csv(CSV, header=None, blocksize="16MB" if free_gb < 8 else "32MB")  # lazy: nothing read yet
    dask.compute(ddf.mean(), ddf.count())            # ONE parallel pass over all the blocks
    q.put("done")


# ---------------- The guard: run a method in a child process and watch the RAM ----------------
def run(name, method):
    q = mp.Queue()
    child = mp.Process(target=method, args=(q,))
    start = time.time()
    child.start()
    proc = psutil.Process(child.pid)
    status, peak = "OK", 0
    ram = [(0, psutil.virtual_memory().percent)]     # (seconds, system RAM %) for the chart

    while child.is_alive():
        pct = psutil.virtual_memory().percent
        try:
            peak = max(peak, proc.memory_info().rss / 2**30)       # memory used by the method
        except psutil.Error:
            pass
        ram.append((time.time() - start, pct))
        print(f"\r  {name}: {time.time() - start:5.1f}s | RAM {pct:4.1f}%", end="")
        if pct >= RAM_LIMIT:                         # too much RAM -> kill it, go to next method
            child.kill()
            status = "SKIPPED"
            break
        time.sleep(0.1)

    child.join()
    if status == "OK":
        try:
            q.get(timeout=1)                         # the method sends "done" when it finishes
        except Exception:
            status = "FAILED"
    seconds = time.time() - start
    print(f"\r  {name}: {status} after {seconds:.1f}s, peak {peak:.2f} GB" + " " * 20)
    return {"name": name, "status": status, "time": seconds, "peak": peak, "ram": ram}


# ---------------- Main: run the 3 methods, then draw the chart ----------------
if __name__ == "__main__":
    methods = [("Standard Pandas", pandas_full),
               ("Pandas Chunking", pandas_chunks),
               ("Dask", dask_blocks)]
    results = [run(name, method) for name, method in methods]

    plt.style.use("dark_background")
    plt.rcParams.update({"figure.facecolor": "#0b0f19", "axes.facecolor": "#131a2b"})
    colors = ["#ff5d73", "#36d1ff", "#6dffb0"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

    # Panels 1 and 2: bars for time and peak memory (skipped methods are hatched)
    for ax, key, title, fmt in [(axes[0], "time", "Execution time (s)", "{:.1f}"),
                                (axes[1], "peak", "Peak memory (GB)", "{:.2f}")]:
        bars = ax.bar([r["name"] for r in results], [r[key] for r in results], color=colors)
        for bar, r in zip(bars, results):
            label = fmt.format(r[key]) + ("" if r["status"] == "OK" else "\n" + r["status"])
            if r["status"] != "OK":
                bar.set_hatch("//")
                bar.set_alpha(0.5)
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label,
                    ha="center", va="bottom", fontweight="bold")
        ax.set_title(title, fontweight="bold")
        ax.margins(y=0.25)                           # leave room above the bars for the labels

    # Panel 3: system RAM over time, with the guard line
    for r, color in zip(results, colors):
        seconds, pct = zip(*r["ram"])
        axes[2].plot(seconds, pct, color=color, linewidth=2, label=r["name"])
    axes[2].axhline(RAM_LIMIT, color="orange", linestyle="--", label=f"{RAM_LIMIT:.0f}% guard")
    axes[2].set_title("System RAM (%) over time", fontweight="bold")
    axes[2].set_xlabel("seconds")
    axes[2].legend()

    fig.suptitle(f"Big Data on one PC: Pandas vs Chunking vs Dask  ({CSV})", fontsize=18, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig("benchmark_comparison.png", dpi=150, facecolor=fig.get_facecolor())
    print("Chart saved: benchmark_comparison.png")