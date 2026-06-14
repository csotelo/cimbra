"""CRISP-DM Fases 4-5: Modelado y Evaluación.

Entrena dos arquitecturas de red neuronal:
  - MLP: Input(5) → Dense(64,relu)+D(0.2) → Dense(32,relu)+D(0.2) → Dense(16,relu) → Dense(1,sigmoid)
  - LSTM: Input(seq_len,5) → LSTM(64) → D(0.2) → Dense(32,relu) → D(0.2) → Dense(1,sigmoid)

La arquitectura final es la que mejor ROC-AUC obtiene en el test set.
"""
import logging
import time

import numpy as np
import tensorflow as tf
from sklearn.metrics import f1_score, roc_auc_score
from tensorflow import keras

logger = logging.getLogger("trainer.train")

EPOCHS = 50
BATCH_SIZE = 64
LEARNING_RATE = 0.001
EARLY_STOPPING_PATIENCE = 8


def build_mlp(input_dim: int = 5) -> keras.Model:
    model = keras.Sequential([
        keras.layers.Input(shape=(input_dim,)),
        keras.layers.Dense(64, activation="relu"),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="binary_crossentropy",
        metrics=["accuracy",
                 keras.metrics.Precision(name="precision"),
                 keras.metrics.Recall(name="recall")],
    )
    return model


def build_lstm(seq_len: int, n_features: int = 5) -> keras.Model:
    model = keras.Sequential([
        keras.layers.Input(shape=(seq_len, n_features)),
        keras.layers.LSTM(64, return_sequences=False),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="binary_crossentropy",
        metrics=["accuracy",
                 keras.metrics.Precision(name="precision"),
                 keras.metrics.Recall(name="recall")],
    )
    return model


def _extended_metrics(model, X_test, y_test) -> dict:
    """Añade ROC AUC y F1 a las métricas estándar de Keras."""
    results = model.evaluate(X_test, y_test, verbose=0)
    m = dict(zip(model.metrics_names, results))
    y_prob = model.predict(X_test, verbose=0).flatten()
    has_both = len(np.unique(y_test)) > 1
    m["roc_auc"] = float(roc_auc_score(y_test, y_prob)) if has_both else 0.0
    m["f1"] = float(f1_score(y_test, (y_prob >= 0.5).astype(int), zero_division=0))
    return m


def _fit(model, X_tr, y_tr, X_val, y_val) -> tuple:
    """Entrena con EarlyStopping. Retorna (history, elapsed_s, epochs_run)."""
    cb = [keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=EARLY_STOPPING_PATIENCE, restore_best_weights=True,
    )]
    t0 = time.time()
    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=cb,
        verbose=0,
    )
    return history, int(time.time() - t0), len(history.history["loss"])


def train_model(X_train, X_val, X_test, y_train, y_val, y_test, model_path: str) -> dict:
    """Entrena MLP y retorna métricas sobre test set."""
    tf.random.set_seed(42)
    np.random.seed(42)

    model = build_mlp(input_dim=X_train.shape[1])
    model.summary(print_fn=logger.info)

    logger.info(f"[MLP] Iniciando — {EPOCHS} épocas máx, batch={BATCH_SIZE}")
    history, elapsed, epochs_run = _fit(model, X_train, y_train, X_val, y_val)
    logger.info(f"[MLP] Completado en {elapsed}s — {epochs_run} épocas efectivas")

    m = _extended_metrics(model, X_test, y_test)
    logger.info(f"[MLP] Test → acc={m['accuracy']:.4f}  f1={m['f1']:.4f}  auc={m['roc_auc']:.4f}")

    model.save(model_path)
    logger.info(f"[MLP] Guardado en {model_path}")

    return {
        "accuracy": float(m.get("accuracy", 0)),
        "precision": float(m.get("precision", 0)),
        "recall": float(m.get("recall", 0)),
        "f1": float(m.get("f1", 0)),
        "roc_auc": float(m.get("roc_auc", 0)),
        "loss": float(m.get("loss", 0)),
        "epochs_run": epochs_run,
        "training_seconds": elapsed,
    }


def train_lstm(X_train_seq, X_val_seq, X_test_seq,
               y_train_s, y_val_s, y_test_s, model_path: str) -> dict:
    """Entrena LSTM sobre secuencias temporales y retorna métricas sobre test set."""
    tf.random.set_seed(42)
    np.random.seed(42)

    seq_len = X_train_seq.shape[1]
    n_features = X_train_seq.shape[2]
    model = build_lstm(seq_len=seq_len, n_features=n_features)
    model.summary(print_fn=logger.info)

    logger.info(f"[LSTM] Iniciando — seq_len={seq_len}, features={n_features}, "
                f"{EPOCHS} épocas máx, batch={BATCH_SIZE}")
    history, elapsed, epochs_run = _fit(model, X_train_seq, y_train_s, X_val_seq, y_val_s)
    logger.info(f"[LSTM] Completado en {elapsed}s — {epochs_run} épocas efectivas")

    m = _extended_metrics(model, X_test_seq, y_test_s)
    logger.info(f"[LSTM] Test → acc={m['accuracy']:.4f}  f1={m['f1']:.4f}  auc={m['roc_auc']:.4f}")

    model.save(model_path)
    logger.info(f"[LSTM] Guardado en {model_path}")

    return {
        "accuracy": float(m.get("accuracy", 0)),
        "precision": float(m.get("precision", 0)),
        "recall": float(m.get("recall", 0)),
        "f1": float(m.get("f1", 0)),
        "roc_auc": float(m.get("roc_auc", 0)),
        "loss": float(m.get("loss", 0)),
        "epochs_run": epochs_run,
        "training_seconds": elapsed,
    }
