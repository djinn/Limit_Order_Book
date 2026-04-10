"""
Poisson LOB — single-window viewer.

Runs all simulations, then opens one window with buttons to switch between views.

Run:
    python app.py
"""

import random
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from lob import simulate
from config import LAMBDAS, DT, N_STEPS, P_FILL, GAMMA, K_FILL, LOB_INIT, GAMMA_CONFIGS, FILL_MODE
from plotting import plot_single_run, plot_gamma_comparison, plot_fill_comparison

SEED = random.randint(0, 2**31 - 1)
FILL_COMPARE_GAMMAS = [(g, l) for g, l in GAMMA_CONFIGS if g in (0.0, 0.05, 0.10, 0.25)]

SIM_KWARGS = dict(lambdas=LAMBDAS, dt=DT, n_steps=N_STEPS, p_fill=P_FILL, seed=SEED, **LOB_INIT)

# ------------------------------------------------------------------
# Run all simulations up front
# ------------------------------------------------------------------

print(f"Seed: {SEED}")

print("Running single simulation...")
single_result = simulate(**SIM_KWARGS, gamma=GAMMA, fill_mode=FILL_MODE, k=K_FILL)

print("Running gamma sweep...")
gamma_results = []
for g, label in GAMMA_CONFIGS:
    r = simulate(**SIM_KWARGS, gamma=g, fill_mode="logistic", k=K_FILL)
    gamma_results.append((g, label, r))
    print(f"  gamma={g}")

print("Running fill model comparison...")
constant_results, logistic_results = [], []
for g, label in FILL_COMPARE_GAMMAS:
    constant_results.append(simulate(**SIM_KWARGS, gamma=g, fill_mode="constant"))
    logistic_results.append(simulate(**SIM_KWARGS, gamma=g, fill_mode="logistic", k=K_FILL))
    print(f"  gamma={g}")

# ------------------------------------------------------------------
# Build figures (don't show yet)
# ------------------------------------------------------------------

fig_single = plot_single_run(single_result, p_fill=P_FILL, gamma=GAMMA, fill_mode=FILL_MODE, k=K_FILL)
fig_gamma  = plot_gamma_comparison(gamma_results, seed=SEED, p_fill=P_FILL)
fig_fill   = plot_fill_comparison(
    FILL_COMPARE_GAMMAS, constant_results, logistic_results,
    seed=SEED, p_fill=P_FILL, k=K_FILL,
)

plt.close("all")  # prevent any accidental auto-display

FIGURES = [
    ("Single Run",         fig_single),
    ("Gamma Sweep",        fig_gamma),
    ("Fill Comparison",    fig_fill),
]

# ------------------------------------------------------------------
# Tkinter app
# ------------------------------------------------------------------

class ViewerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Poisson LOB Viewer")
        self.current = 0

        # Button bar
        btn_frame = tk.Frame(root, bg="#1e1e1e", pady=6)
        btn_frame.pack(side=tk.TOP, fill=tk.X)

        self.buttons = []
        for i, (name, _) in enumerate(FIGURES):
            btn = tk.Button(
                btn_frame, text=name,
                command=lambda i=i: self.show(i),
                font=("Helvetica", 11),
                relief=tk.FLAT,
                padx=18, pady=6,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=6)
            self.buttons.append(btn)

        # Canvas area
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = None
        self.show(0)

    def show(self, index: int):
        self.current = index

        # Highlight active button
        for i, btn in enumerate(self.buttons):
            btn.config(
                bg="#4CAF50" if i == index else "#333333",
                fg="white",
            )

        # Swap canvas
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        _, fig = FIGURES[index]
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


print("\nOpening viewer...")
root = tk.Tk()
root.configure(bg="#1e1e1e")
root.state("zoomed")  # start maximized
app = ViewerApp(root)
root.mainloop()
