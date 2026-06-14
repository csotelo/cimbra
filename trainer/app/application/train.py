"""CRISP-DM Fases 4-5: Modelado y Evaluación.

Red neuronal MLP con activación sigmoid en salida → probabilidad 0.0-1.0.
Arquitectura validada en la tesis:
  Input(5) → Dense(64,relu) → Dense(32,relu) → Dense(16,relu) → Dense(1,sigmoid)
"""
import logging
import time

import numpy as np
import tensorflow as tf
from tensorflow import keras

logger = logging.getLogger("trainer.train")

EPOCHS = 50
BATCH_SIZE = 64
LEARNING_RATE = 0.001
EARLY_STOPPING_PATIENCE = 8


def build_model(input_dim: int = 5) -> keras.Model:
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
        metrics=["accuracy", keras.metrics.Precision(name="precision"), keras.metrics.Recall(name="recall")],
    )
    return model


def train_model(
    X_train, X_val, X_test,
    y_train, y_val, y_test,
    model_path: str,
) -> dict:
    """Entrena el modelo y retorna métricas sobre test set."""
    tf.random.set_seed(42)
    np.random.seed(42)

    model = build_model(input_dim=X_train.shape[1])
    model.summary(print_fn=logger.info)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
        ),
    ]

    logger.info(f"Iniciando entrenamiento — {EPOCHS} épocas máx, batch={BATCH_SIZE}")
    t0 = time.time()

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=0,
    )

    elapsed = int(time.time() - t0)
    epochs_run = len(history.history["loss"])
    logger.info(f"Entrenamiento completado en {elapsed}s — {epochs_run} épocas efectivas")

    results = model.evaluate(X_test, y_test, verbose=0)
    metrics = dict(zip(model.metrics_names, results))
    logger.info(f"Test metrics: {metrics}")

    model.save(model_path)
    logger.info(f"Modelo guardado en {model_path}")

    return {
        "accuracy": float(metrics.get("accuracy", 0)),
        "precision": float(metrics.get("precision", 0)),
        "recall": float(metrics.get("recall", 0)),
        "loss": float(metrics.get("loss", 0)),
        "epochs_run": epochs_run,
        "training_seconds": elapsed,
    }
