#!/usr/bin/env python3
"""Plot Iris dataset (sepal length vs sepal width) using matplotlib.

Creates `iris_scatter.png` and shows the scatter plot.
"""

from sklearn.datasets import load_iris
import matplotlib.pyplot as plt


def main():
    iris = load_iris()
    X = iris.data
    y = iris.target
    feature_names = iris.feature_names

    # 列インデックス: 0 = sepal length (cm), 1 = sepal width (cm)
    x_idx, y_idx = 0, 1

    colors = ["tab:orange", "tab:green", "tab:blue"]
    labels = iris.target_names

    plt.figure(figsize=(8, 6))
    for label in range(len(labels)):
        mask = (y == label)
        plt.scatter(
            X[mask, x_idx],
            X[mask, y_idx],
            c=[colors[label]],
            label=labels[label],
            edgecolors="k",
            s=60,
        )

    plt.xlabel(feature_names[x_idx])
    plt.ylabel(feature_names[y_idx])
    plt.title(f"Iris dataset: {feature_names[x_idx]} vs {feature_names[y_idx]}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    out_path = "iris_scatter.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved figure to {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
