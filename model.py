import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

# Ingredient Mapping (Weights in grams or unit count)
ingredient_mapping = {
    "Carrots": 100, "Potatoes": 150, "Onions": 80, "Chicken": 200, "Eggs": 50,
    "Fish": 180, "Water": 500, "Broth": 500, "Milk": 250, "Coconut Milk": 250,
    "Cream": 100, "Tofu": 200, "Peas": 100, "Tomatoes": 100, "Garlic": 10,
    "Rice": 150, "Beans": 100  # Added variety
}

def train_cooking_model():
    """Train the cooking time prediction model and return it with training data columns"""
    # Expanded Training Data with Preparation Method (0: Simmer, 1: Boil, 2: Fry)
    data = pd.DataFrame({
        "Carrots": [100, 0, 50, 0, 0, 100, 0, 0, 80, 0, 0, 50, 0],
        "Potatoes": [150, 200, 0, 0, 100, 0, 0, 200, 100, 0, 0, 0, 150],
        "Onions": [0, 80, 0, 0, 50, 0, 100, 0, 0, 0, 0, 80, 0],
        "Chicken": [200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 250, 0],
        "Eggs": [0, 0, 0, 2, 0, 3, 0, 1, 4, 0, 0, 0, 0],
        "Fish": [0, 0, 180, 0, 0, 0, 0, 0, 0, 0, 200, 0, 0],
        "Tofu": [0, 0, 0, 0, 0, 0, 200, 0, 0, 0, 0, 0, 0],
        "Peas": [0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 50, 0],
        "Tomatoes": [0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 100],
        "Garlic": [0, 10, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0],
        "Rice": [0, 0, 0, 0, 0, 0, 0, 150, 0, 0, 0, 0, 0],
        "Beans": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0],
        "Water": [500, 700, 400, 300, 100, 200, 0, 250, 0, 0, 0, 300, 0],
        "Broth": [0, 0, 0, 0, 200, 0, 0, 0, 0, 300, 0, 0, 500],
        "Milk": [0, 0, 0, 0, 0, 0, 0, 0, 250, 0, 0, 0, 0],
        "Coconut Milk": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0],
        "Cream": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 50, 0, 0],
        "Prep_Method": [0, 1, 0, 2, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        "Cooking Time": [40, 20, 15, 10, 12, 20, 8, 7, 25, 35, 30, 18, 45]
    })

    # Feature Engineering
    data["Total_Weight"] = data.drop(columns=["Cooking Time", "Prep_Method"]).sum(axis=1)
    data["Ingredient_Count"] = data.drop(columns=["Cooking Time", "Prep_Method"]).gt(0).sum(axis=1)

    # Train Model
    X = data.drop(columns=["Cooking Time"])
    y = data["Cooking Time"]

    # Hyperparameter tuning
    param_grid = {
        "model__n_estimators": [100, 200, 300],
        "model__max_depth": [5, 10, 15],
        "model__min_samples_split": [2, 5]
    }
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(random_state=42))
    ])
    grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring="neg_mean_squared_error")
    grid_search.fit(X, y)

    return grid_search.best_estimator_, X.columns, grid_search.best_params_

def predict_cooking_time(model_pipeline, X_columns, selected_ingredients, prep_method="Simmer"):
    """Prediction function using the trained model"""
    try:
        prep_map = {"Simmer": 0, "Boil": 1, "Fry": 2}
        full_ingredients = {ing: (ingredient_mapping.get(ing, 0) * selected_ingredients.get(ing, 0)) 
                          for ing in ingredient_mapping}
        
        # Create a dataframe with all columns from the training data
        X_input = pd.DataFrame([full_ingredients], columns=X_columns.drop(["Prep_Method", "Total_Weight", "Ingredient_Count"]))
        
        # Add preparation method
        X_input["Prep_Method"] = prep_map.get(prep_method, 0)
        
        # Add engineered features
        X_input["Total_Weight"] = X_input.drop(columns=["Prep_Method"]).sum(axis=1)
        X_input["Ingredient_Count"] = X_input.drop(columns=["Prep_Method"]).gt(0).sum(axis=1)
        
        # Ensure columns are in the same order as during training
        X_input = X_input[X_columns]
        
        predicted_time = model_pipeline.predict(X_input)[0]
        return round(predicted_time)
    except Exception as e:
        raise Exception(f"Prediction error: {str(e)}")

# Cooking tips database
ingredient_tips = {
    "Carrots": "For more flavor, try roasting carrots with a drizzle of honey.",
    "Potatoes": "Soaking potatoes in cold water removes excess starch for crispier results.",
    "Onions": "To reduce tears when cutting onions, refrigerate them for 30 minutes before chopping.",
    "Chicken": "Always let chicken rest for 5-10 minutes after cooking to retain juices.",
    "Eggs": "Room temperature eggs whip up better than cold ones.",
    "Fish": "Fish is done when it flakes easily with a fork.",
    "Tofu": "Press tofu between paper towels with a heavy object to remove excess water before cooking.",
    "Rice": "The perfect rice ratio is 1 part rice to 2 parts water.",
    "Garlic": "Crush garlic and let it sit for 10 minutes before cooking to enhance health benefits.",
    "Tomatoes": "Store tomatoes at room temperature, not in the refrigerator, for best flavor.",
    "Beans": "Soak dried beans overnight to reduce cooking time and make them more digestible.",
    "Water": "Using filtered water can improve the taste of your dishes, especially in soups.",
    "Broth": "Make your own broth by saving vegetable scraps and simmering them in water.",
    "Milk": "To prevent milk from curdling in soups, add it at the end of cooking.",
    "Coconut Milk": "Shake coconut milk well before using as it tends to separate.",
    "Cream": "To prevent cream from curdling when added to hot dishes, temper it first with a little of the hot liquid.",
    "Peas": "Frozen peas often have better flavor than fresh ones as they're frozen at peak ripeness."
}

method_tips = {
    "Simmer": "Keep the lid on when simmering to maintain consistent temperature.",
    "Boil": "Adding salt to boiling water increases the boiling point for better cooking.",
    "Fry": "Don't overcrowd the pan when frying - cook in batches if needed."
}

# Cooking instructions dictionary
cooking_instructions = {
    "Chicken": "To cook chicken: Season with salt and pepper. For boneless chicken breasts, cook in a skillet over medium heat for 6-7 minutes per side until internal temperature reaches 165°F (74°C).",
    "Fish": "For salmon or fish fillets: Season and cook skin-side down first in a hot pan with oil for 3-4 minutes. Flip and cook for another 2-3 minutes until it flakes easily.",
    "Potatoes": "For roasted potatoes: Cut into cubes, toss with oil, salt, and herbs. Roast at 425°F (220°C) for 25-30 minutes, turning halfway through.",
    "Rice": "For perfect rice: Rinse first, then use 1 part rice to 2 parts water. Bring to boil, reduce to simmer, cover and cook for 18 minutes. Let stand covered for 5 minutes before fluffing.",
    "Pasta": "Cook pasta in salted boiling water according to package directions. Test for al dente by biting into it - it should have a slight resistance.",
    "Eggs": "For scrambled eggs: Beat eggs with a fork, cook in a non-stick pan over medium-low heat, stirring gently until just set but still slightly moist.",
    "Vegetables": "For sautéed vegetables: Cut into uniform pieces, cook in a hot pan with oil, stirring occasionally until tender-crisp."
}

# Generic response templates for the chatbot
chat_responses = {
    "greeting": [
        "Hello! I'm your cooking assistant. How can I help in the kitchen today?",
        "Hi there! Ready to cook something delicious?",
        "Greetings! What would you like to cook today?"
    ],
    "farewell": [
        "Goodbye! Enjoy your cooking!",
        "Happy cooking! Come back if you need more help.",
        "Bye for now! Hope your dish turns out great!"
    ],
    "help": [
        "Here's how to use Chef's Assistant:\n1. Select ingredients from the left panel\n2. Choose quantities for each ingredient\n3. Select a cooking method (Simmer, Boil, or Fry)\n4. Click 'Predict Cooking Time'\n5. You can also ask me for cooking tips!"
    ],
    "about": [
        "I'm a cooking assistant that helps predict cooking times based on ingredients and methods. Select ingredients, choose a cooking method, and I'll estimate how long your dish will take to cook!"
    ],
    "fallback": [
        "I'm not sure I understand. I can help predict cooking times or give cooking advice. Try selecting some ingredients or asking for a specific cooking tip.",
        "Sorry, I didn't catch that. Would you like me to predict cooking time for a recipe or provide cooking tips?",
        "I specialize in cooking times and tips. Could you rephrase your question about cooking?"
    ]
}