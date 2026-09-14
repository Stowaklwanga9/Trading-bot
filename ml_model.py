"""
Model layer: a modest gradient-boosted classifier predicting next-period
direction. Deliberately not a deep net -- on this little data, a simpler
model generalizes better and is far easier to debug and trust.
"""
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from feature_engineering import FEATURE_COLUMNS
import config


def train(df):
    """
    df must already have FEATURE_COLUMNS and a 'label' column.
    Uses a chronological split (not random shuffle) -- shuffling time series
    data leaks future information into training and inflates accuracy.
    """
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["label"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["label"]

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("Out-of-sample accuracy:", accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))
    print(
        "NOTE: accuracy alone is not profitability. A model that's 55% "
        "accurate with good risk/reward can be profitable; 70% accurate "
        "with poor risk management can still lose money."
    )

    joblib.dump(model, config.MODEL_PATH)
    return model


def load():
    return joblib.load(config.MODEL_PATH)


def predict_signal(model, feature_row):
    """
    Returns (direction, confidence).
    direction: 1 = expect up-move, 0 = expect down/flat.
    confidence: model's probability estimate for the predicted class.
    """
    X = feature_row[FEATURE_COLUMNS].values.reshape(1, -1)
    proba = model.predict_proba(X)[0]
    direction = int(proba[1] > proba[0])
    confidence = max(proba)
    return direction, confidence
