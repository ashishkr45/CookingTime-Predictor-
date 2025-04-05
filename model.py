import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Ingredient Mapping (Weights in grams or unit count)
ingredient_mapping = {
    "Carrots": 100,
    "Potatoes": 150,
    "Onions": 80,
    "Chicken": 200,
    "Eggs": 50,  # Approx weight per egg
    "Fish": 180,
    "Water": 500,
    "Broth": 500,
    "Milk": 250,
    "Coconut Milk": 250,
    "Cream": 100,
    "Tofu": 200,
    "Peas": 100,
    "Tomatoes": 100
}

# Training Data (Expanded)
data = pd.DataFrame({
    "Carrots": [100, 0, 50, 0, 0, 100, 0, 0, 80, 0, 0],
    "Potatoes": [150, 200, 0, 0, 100, 0, 0, 200, 100, 0, 0],
    "Onions": [0, 80, 0, 0, 50, 0, 100, 0, 0, 0, 0],
    "Chicken": [200, 0, 0, 0, 0, 0, 0, 0, 0, 250, 0],
    "Eggs": [0, 0, 0, 2, 0, 3, 0, 1, 4, 0, 0],
    "Fish": [0, 0, 180, 0, 0, 0, 0, 0, 0, 0, 200],
    "Tofu": [0, 0, 0, 0, 0, 0, 200, 0, 0, 0, 0],
    "Peas": [0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0],
    "Tomatoes": [0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0],
    "Water": [500, 700, 400, 300, 100, 200, 0, 250, 0, 0, 0],
    "Broth": [0, 0, 0, 0, 200, 0, 0, 0, 0, 300, 0],
    "Milk": [0, 0, 0, 0, 0, 0, 0, 0, 250, 0, 0],
    "Coconut Milk": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100],
    "Cream": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 50],
    "Cooking Time": [40, 20, 15, 10, 12, 20, 8, 7, 25, 35, 30]
})

# Train Model
X = data.drop(columns=["Cooking Time"])
y = data["Cooking Time"]

model_pipeline = Pipeline([
    ("scaler", StandardScaler()),  # Normalize data for better learning
    ("model", RandomForestRegressor(n_estimators=200, random_state=42, max_depth=10))
])

model_pipeline.fit(X, y)

# Prediction Function
def predict_cooking_time(selected_ingredients):
    try:
        full_ingredients = {ing: (ingredient_mapping.get(ing, 0) * selected_ingredients.get(ing, 0)) for ing in X.columns}
        X_input = pd.DataFrame([full_ingredients], columns=X.columns)
        predicted_time = model_pipeline.predict(X_input)[0]
        return round(predicted_time)
    except Exception as e:
        return f"Error: {str(e)}"
