"""Visualization utilities for detection/attack-classification results."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix as sk_confusion_matrix
from sklearn.metrics import roc_curve as sk_roc_curve


def plot_entropy_profiles(X: np.ndarray, y: np.ndarray, class_names: list[str] | None = None):
    """Plot mean per-layer entropy for each class — the qualitative evidence for whether
    the detection methodology is actually separating classes."""
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = class_names if class_names is not None else sorted(set(y))
    for label in labels:
        mask = np.asarray(y) == label
        if mask.sum() == 0:
            continue
        mean_profile = np.asarray(X)[mask].mean(axis=0)
        ax.plot(mean_profile, marker="o", label=str(label))
    ax.set_xlabel("Transformer layer")
    ax.set_ylabel("Mean attention entropy")
    ax.set_title("Attention Entropy by Class")
    ax.legend()
    return fig


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, labels: list[str] | None = None):
    labels = labels if labels is not None else sorted(set(y_true) | set(y_pred))
    cm = sk_confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(4 + len(labels), 4 + len(labels) * 0.5))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, cm[i, j], ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black",
            )
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    fig.colorbar(im)
    return fig


def plot_roc_curve(y_true: np.ndarray, y_scores: np.ndarray, positive_label):
    """Binary-detection ROC curve. y_true should contain positive_label for the
    'adversarial' class and something else for 'clean'."""
    y_binary = (np.asarray(y_true) == positive_label).astype(int)
    fpr, tpr, _ = sk_roc_curve(y_binary, y_scores)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    return fig
