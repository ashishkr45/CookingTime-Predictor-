import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import datetime
import random
import re
from model import (
    ingredient_mapping, train_cooking_model, predict_cooking_time,
    ingredient_tips, method_tips, cooking_instructions, chat_responses
)

class CookingTimePredictor(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Model data
        self.ingredient_mapping = ingredient_mapping
        self.prep_methods = ["Simmer", "Boil", "Fry"]
        self.model_pipeline = None
        self.X_columns = None
        self.selected_ingredients = {}
        
        # Set up the UI
        self.title("Chef's Assistant - Cooking Time Predictor")
        self.geometry("900x700")
        self.configure(bg="#F5F5DC")  # Beige background
        
        self.setup_ui()
        
        # Start model training in background
        self.status_var.set("Training model... Please wait.")
        self.update_idletasks()
        
        self.train_thread = threading.Thread(target=self.train_model)
        self.train_thread.daemon = True
        self.train_thread.start()
    
    def setup_ui(self):
        # Create main frames
        self.top_frame = tk.Frame(self, bg="#F5F5DC", pady=10)
        self.main_frame = tk.Frame(self, bg="#F5F5DC")
        self.bottom_frame = tk.Frame(self, bg="#F5F5DC", pady=10)
        
        self.top_frame.pack(fill="x")
        self.main_frame.pack(fill="both", expand=True)
        self.bottom_frame.pack(fill="x")
        
        # Top frame - Title and Status
        self.title_label = tk.Label(
            self.top_frame, 
            text="Chef's Assistant", 
            font=("Garamond", 24, "bold"), 
            bg="#F5F5DC", 
            fg="#8B4513"  # Brown color
        )
        self.title_label.pack(pady=(0, 5))
        
        self.subtitle_label = tk.Label(
            self.top_frame, 
            text="Predict cooking times based on ingredients and method", 
            font=("Garamond", 14, "italic"), 
            bg="#F5F5DC", 
            fg="#8B4513"
        )
        self.subtitle_label.pack(pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            self.top_frame, 
            textvariable=self.status_var,
            bg="#F5F5DC", 
            fg="#006400"  # Dark green
        )
        self.status_label.pack()
        
        # Main frame - Split into left (ingredients) and right (chat) panes
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Left panel - Ingredients and methods selector
        self.left_panel = tk.LabelFrame(
            self.main_frame, 
            text="Recipe Builder", 
            bg="#F5F5DC", 
            fg="#8B4513",
            font=("Garamond", 12, "bold"),
            padx=10, 
            pady=10
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create a canvas with scrollbar for ingredients
        self.canvas_frame = tk.Frame(self.left_panel, bg="#F5F5DC")
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#F5F5DC", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.ingredients_frame = tk.Frame(self.canvas, bg="#F5F5DC")
        self.ingredients_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.ingredients_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Add ingredients checkboxes with quantity spinboxes
        self.ingredient_vars = {}
        self.quantity_vars = {}
        self.ingredient_frames = {}
        
        row = 0
        col = 0
        ingredients_per_col = 7
        
        for ingredient in sorted(self.ingredient_mapping.keys()):
            frame = tk.Frame(self.ingredients_frame, bg="#F5F5DC")
            frame.grid(row=row, column=col, sticky="w", pady=3)
            self.ingredient_frames[ingredient] = frame
            
            self.ingredient_vars[ingredient] = tk.BooleanVar()
            check = tk.Checkbutton(
                frame, 
                text=ingredient,
                variable=self.ingredient_vars[ingredient],
                bg="#F5F5DC",
                command=self.update_ingredient_selection
            )
            check.pack(side="left")
            
            self.quantity_vars[ingredient] = tk.IntVar(value=1)
            spinbox = tk.Spinbox(
                frame, 
                from_=1, 
                to=10, 
                width=2,
                textvariable=self.quantity_vars[ingredient],
                state="disabled"
            )
            spinbox.pack(side="left", padx=5)
            
            # Enable/disable spinbox based on checkbox
            self.ingredient_vars[ingredient].trace_add(
                "write", 
                lambda *args, ing=ingredient: self.toggle_spinbox(ing)
            )
            
            row += 1
            if row >= ingredients_per_col:
                row = 0
                col += 1
        
        # Preparation method section
        self.prep_frame = tk.LabelFrame(
            self.left_panel, 
            text="Preparation Method", 
            bg="#F5F5DC", 
            fg="#8B4513",
            font=("Garamond", 12),
            padx=10, 
            pady=5
        )
        self.prep_frame.pack(fill="x", pady=10)
        
        self.prep_var = tk.StringVar(value=self.prep_methods[0])
        
        for i, method in enumerate(self.prep_methods):
            radio = tk.Radiobutton(
                self.prep_frame,
                text=method,
                variable=self.prep_var,
                value=method,
                bg="#F5F5DC"
            )
            radio.pack(side="left", padx=10)
        
        # Predict button
        self.predict_button = tk.Button(
            self.left_panel,
            text="Predict Cooking Time",
            command=self.predict,
            bg="#8B4513",
            fg="white",
            font=("Garamond", 12, "bold"),
            padx=10,
            pady=5,
            relief=tk.RAISED,
            state="disabled"  # Initially disabled until model is trained
        )
        self.predict_button.pack(pady=10)
        
        # Right panel - Chat history
        self.right_panel = tk.LabelFrame(
            self.main_frame, 
            text="Chef's Conversation", 
            bg="#F5F5DC", 
            fg="#8B4513", 
            font=("Garamond", 12, "bold"),
            padx=10, 
            pady=10
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.chat_history = scrolledtext.ScrolledText(
            self.right_panel,
            bg="#FFFAF0",  # Floral white
            fg="#000000",
            font=("Garamond", 11),
            wrap=tk.WORD,
            width=40,
            height=20
        )
        self.chat_history.pack(fill="both", expand=True)
        self.chat_history.config(state="disabled")
        
        # Bottom frame - User input
        self.input_label = tk.Label(
            self.bottom_frame, 
            text="Ask Chef:", 
            bg="#F5F5DC", 
            fg="#8B4513",
            font=("Garamond", 12, "bold")
        )
        self.input_label.pack(side="left", padx=10)
        
        self.user_input = tk.Entry(
            self.bottom_frame,
            bg="white",
            fg="#000000",
            font=("Garamond", 11),
            width=50
        )
        self.user_input.pack(side="left", padx=5, fill="x", expand=True)
        self.user_input.bind("<Return>", self.send_message)
        
        self.send_button = tk.Button(
            self.bottom_frame,
            text="Send",
            command=self.send_message,
            bg="#8B4513",
            fg="white",
            font=("Garamond", 11)
        )
        self.send_button.pack(side="left", padx=5)
        
        # Initialize the chat with welcome message
        self.append_to_chat("Chef's Assistant", "Welcome to Chef's Assistant! I can help predict cooking times based on ingredients and cooking methods. Please select ingredients and I'll give you an estimate.", "system")
    
    def train_model(self):
        """Train the model in a background thread"""
        try:
            self.model_pipeline, self.X_columns, best_params = train_cooking_model()
            
            # Update UI from main thread
            self.after(0, self.on_model_trained, best_params)
            
        except Exception as e:
            # Update UI from main thread
            self.after(0, self.on_model_error, str(e))
    
    def on_model_trained(self, best_params):
        """Called after model training completes"""
        self.status_var.set("Model trained successfully!")
        self.predict_button.config(state="normal")
        self.append_to_chat("Chef's Assistant", 
                           f"I'm ready to help! My model has been trained with the best parameters: {best_params}", 
                           "system")
    
    def on_model_error(self, error_msg):
        """Called if model training fails"""
        self.status_var.set(f"Error training model")
        messagebox.showerror("Model Training Error", f"Failed to train model: {error_msg}")
    
    def toggle_spinbox(self, ingredient):
        """Enable/disable spinbox based on checkbox state"""
        spinbox = self.ingredient_frames[ingredient].winfo_children()[1]
        if self.ingredient_vars[ingredient].get():
            spinbox.config(state="normal")
        else:
            spinbox.config(state="disabled")
    
    def update_ingredient_selection(self):
        """Update selected ingredients dictionary based on UI state"""
        self.selected_ingredients = {}
        for ingredient, var in self.ingredient_vars.items():
            if var.get():
                self.selected_ingredients[ingredient] = self.quantity_vars[ingredient].get()
    
    def predict(self):
        """Predict cooking time based on selected ingredients and method"""
        self.update_ingredient_selection()
        
        if not self.selected_ingredients:
            messagebox.showinfo("No Ingredients", "Please select at least one ingredient.")
            return
        
        try:
            prep_method = self.prep_var.get()
            cooking_time = predict_cooking_time(
                self.model_pipeline, 
                self.X_columns, 
                self.selected_ingredients, 
                prep_method
            )
            
            # Create a nicely formatted message about the recipe
            ingredient_list = ", ".join([f"{qty} {ing}" for ing, qty in self.selected_ingredients.items()])
            message = f"For a recipe with {ingredient_list} using {prep_method.lower()} method, I estimate a cooking time of {cooking_time} minutes."
            
            self.append_to_chat("Chef's Assistant", message, "prediction")
            
            # Add a cooking tip based on ingredients and method
            self.add_cooking_tip()
            
        except Exception as e:
            messagebox.showerror("Prediction Error", f"Error predicting cooking time: {str(e)}")
    
    def append_to_chat(self, sender, message, msg_type="user"):
        """Add a message to the chat history"""
        self.chat_history.config(state="normal")
        
        # Insert timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Format based on message type
        if msg_type == "user":
            self.chat_history.insert(tk.END, f"[{timestamp}] You: ", "user_sender")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user_message")
        elif msg_type == "system":
            self.chat_history.insert(tk.END, f"[{timestamp}] {sender}: ", "system_sender")
            self.chat_history.insert(tk.END, f"{message}\n\n", "system_message")
        elif msg_type == "prediction":
            self.chat_history.insert(tk.END, f"[{timestamp}] {sender}: ", "prediction_sender")
            self.chat_history.insert(tk.END, f"{message}\n\n", "prediction_message")
        
        # Apply tags for styling
        self.chat_history.tag_config("user_sender", foreground="#006400", font=("Garamond", 11, "bold"))
        self.chat_history.tag_config("user_message", foreground="black", font=("Garamond", 11))
        self.chat_history.tag_config("system_sender", foreground="#8B4513", font=("Garamond", 11, "bold"))
        self.chat_history.tag_config("system_message", foreground="black", font=("Garamond", 11))
        self.chat_history.tag_config("prediction_sender", foreground="#8B0000", font=("Garamond", 11, "bold"))
        self.chat_history.tag_config("prediction_message", foreground="#8B0000", font=("Garamond", 11))
        
        self.chat_history.config(state="disabled")
        self.chat_history.see(tk.END)
    
    def send_message(self, event=None):
        """Handle user sending a message"""
        message = self.user_input.get().strip()
        if not message:
            return
        
        self.append_to_chat("You", message, "user")
        self.user_input.delete(0, tk.END)
        
        # Process user message and generate response
        self.process_user_message(message)
    
    def process_user_message(self, message):
        """Process user message and generate appropriate response"""
        message_lower = message.lower()
        
        # Check for greetings
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            self.append_to_chat("Chef's Assistant", random.choice(chat_responses["greeting"]), "system")
            return
            
        # Check for farewells
        elif any(word in message_lower for word in ["bye", "goodbye", "exit", "quit"]):
            self.append_to_chat("Chef's Assistant", random.choice(chat_responses["farewell"]), "system")
            return
            
        # Check for help requests
        elif any(word in message_lower for word in ["help", "instructions", "how to use"]):
            self.append_to_chat("Chef's Assistant", chat_responses["help"][0], "system")
            return
            
        # Check for questions about the system
        elif any(phrase in message_lower for phrase in ["how are you", "what can you do", "who are you", "what are you"]):
            self.append_to_chat("Chef's Assistant", chat_responses["about"][0], "system")
            return
            
        # Check for prediction requests
        elif any(phrase in message_lower for phrase in ["predict", "cooking time", "how long", "estimate time"]):
            if self.selected_ingredients:
                self.predict()
            else:
                self.append_to_chat("Chef's Assistant", "Please select some ingredients first, then I can predict the cooking time.", "system")
            return
            
        # Check for tip requests
        elif any(word in message_lower for word in ["tip", "advice", "suggestion", "hint"]):
            self.add_cooking_tip()
            return
        
        # Check for specific cooking instructions
        for food, instructions in cooking_instructions.items():
            food_lower = food.lower()
            if f"cook {food_lower}" in message_lower or f"how to cook {food_lower}" in message_lower or f"cooking {food_lower}" in message_lower:
                self.append_to_chat("Chef's Assistant", instructions, "system")
                return
        
        # Check for specific ingredient tips
        for ingredient, tip in ingredient_tips.items():
            if ingredient.lower() in message_lower and ("tip" in message_lower or "advice" in message_lower):
                self.append_to_chat("Chef's Assistant", f"Tip for {ingredient}: {tip}", "system")
                return
        
        # Default fallback response
        self.append_to_chat("Chef's Assistant", random.choice(chat_responses["fallback"]), "system")
    
    def add_cooking_tip(self):
        """Add a relevant cooking tip based on selected ingredients and method"""
        # Select a tip based on ingredients or method
        tip = ""
        selected_ingredients = list(self.selected_ingredients.keys())
        
        if selected_ingredients:
            # Choose a tip for a random selected ingredient that has a tip
            eligible_ingredients = [ing for ing in selected_ingredients if ing in ingredient_tips]
            if eligible_ingredients:
                chosen_ingredient = random.choice(eligible_ingredients)
                tip = ingredient_tips[chosen_ingredient]
            else:
                # Fall back to method tip
                tip = method_tips.get(self.prep_var.get(), "Remember to taste as you go for the best results!")
        else:
            # No ingredients selected, use method tip
            tip = method_tips.get(self.prep_var.get(), "Remember to taste as you go for the best results!")
        
        self.append_to_chat("Chef's Assistant", f"Chef's Tip: {tip}", "system")

if __name__ == "__main__":
    app = CookingTimePredictor()
    app.mainloop()