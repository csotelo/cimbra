"""CRISP-DM Fase 3: Preparación del dataset.

- Limpieza de nulos y outliers
- Generación de labels (heurística física SENAMHI-aligned)
- Normalización Min-Max con sklearn
- Partición 70/15/15 (train/val/test)
"""
import logging
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger("trainer.prepare")

FEATURES = ["temperature", "humidity", "pressure", "cape", "k_index"]

# Thresholds SENAMHI-aligned para label binario
# CAPE >= 500 J/kg AND K-Index >= 20 → tormenta probable (label=1)
CAPE_THRESHOLD = 500.0
K_INDEX_THRESHOLD = 20.0

OUTLIER_BOUNDS = {
    "temperature": (-20, 50),
    "humidity": (0, 100),
    "pressure": (500, 1100),
    "cape": (0, 10000),
    "k_index": (-20, 60),
}


def _label(row) -> int:
    cape = row["cape"]
    ki = row["k_index"]
    if pd.isna(cape) or pd.isna(ki):
        return 0
    return 1 if (cape >= CAPE_THRESHOLD and ki >= K_INDEX_THRESHOLD) else 0


def prepare_dataset(records: list[dict], scaler_path: str) -> tuple:
    """Retorna (X_train, X_val, X_test, y_train, y_val, y_test, n_train, n_val, n_test)."""
    df = pd.DataFrame(records)[FEATURES + ["id"]]

    # Limpieza de outliers
    for col, (lo, hi) in OUTLIER_BOUNDS.items():
        df = df[df[col].between(lo, hi, inclusive="both") | df[col].isna()]

    df = df.dropna(subset=FEATURES).reset_index(drop=True)

    if len(df) < 100:
        raise ValueError(f"Dataset insuficiente tras limpieza: {len(df)} registros")

    df["label"] = df.apply(_label, axis=1)
    pos = df["label"].sum()
    logger.info(f"Dataset: {len(df)} registros — {pos} positivos ({pos/len(df):.1%}) / {len(df)-pos} negativos")

    X = df[FEATURES].values.astype(np.float32)
    y = df["label"].values.astype(np.float32)

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, scaler_path)
    logger.info(f"Scaler guardado en {scaler_path}")

    n = len(X_scaled)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    X_train, y_train = X_scaled[:n_train], y[:n_train]
    X_val,   y_val   = X_scaled[n_train:n_train + n_val], y[n_train:n_train + n_val]
    X_test,  y_test  = X_scaled[n_train + n_val:], y[n_train + n_val:]

    logger.info(f"Split — train: {len(X_train)}, val: {len(X_val)}, test: {len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test, len(X_train), len(X_val), len(X_test)


SEQ_LEN = 6  # ventana temporal para LSTM (horas)


def walk_forward_splits(X: np.ndarray, y: np.ndarray, n_splits: int = 4) -> list:
    """
    Temporal expanding-window cross-validation.
    Asume X, y ya ordenados cronológicamente.
    Retorna lista de ((X_tr, y_tr), (X_te, y_te)).
    """
    n = len(X)
    base = int(n * 0.55)
    step = max(int(n * 0.10), 50)
    splits = []
    for i in range(n_splits):
        train_end = base + i * step
        test_end = min(train_end + step, n)
        if train_end >= n or test_end <= train_end:
            break
        splits.append(
            ((X[:train_end], y[:train_end]), (X[train_end:test_end], y[train_end:test_end]))
        )
    return splits


def create_sequences(X: np.ndarray, y: np.ndarray, seq_len: int = SEQ_LEN) -> tuple:
    """
    Crea ventanas temporales para LSTM.
    X: (n, features) → output Xs: (n-seq_len, seq_len, features)
    y: label del paso seq_len-ésimo de cada ventana.
    """
    Xs, ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i:i + seq_len])
        ys.append(y[i + seq_len])
    return np.array(Xs, dtype=np.float32), np.array(ys, dtype=np.float32)
