from sklearn import linear_model
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score, f1_score, accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pandas as pd
import joblib  # Import joblib to save the model
import numpy as np
from typing_extensions import Annotated
import mlflow
from mlflow.models import infer_signature


mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("MLflow First experiment")

def importer():
    df = pd.read_csv("../source2/heart.csv")
    features = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach',
                'exang', 'oldpeak', 'slope', 'ca', 'thal']
    X = df[features]
    y = df['target']
    return train_test_split(X, y, test_size=0.4, random_state=42)

def main():
    X_train, X_test, y_train, y_test = importer()
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    f1 = f1_score(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"F1 score: {f1:.2f}")
    print(f"Accuracy: {accuracy:.2f}")

    with mlflow.start_run():
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.set_tag("name", "machine learning Experiment")
        signature = infer_signature(X_train, model.predict(X_train))
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="DecisionTreeClassifier",
            signature=signature,
            input_example=X_train,
            registered_model_name="DecisionTreeClassifier_v1",
        )

if __name__ == "__main__":
    main()