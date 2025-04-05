import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import model
import os

# Fonts and styles
FONT_HEADING = ("Montserrat", 22, "bold")
FONT_REGULAR = ("Open Sans", 16)
FONT_LABEL = ("Open Sans", 14)
FONT_HELPER = ("Open Sans", 12)
FONT_MONOSPACE = ("Courier", 16, "bold")  # For cooking time
COLOR_BG = "#FAF3E0"
COLOR_PRIMARY = "#D35400"
COLOR_SECONDARY = "#1E8449"
COLOR_TEXT = "#333333"
COLOR_ERROR = "#D32F2F"
COLOR_LIGHT_BG = "#FEF9E7"

# Categories with cooking time impact factors
ingredients = {
    "Proteins": ["Chicken", "Fish", "Eggs", "Tofu", "Pork", "Lamb"],
    "Vegetables": ["Carrots", "Potatoes", "Tomatoes", "Onions", "Peas", "Celery", "Mushrooms", "Bell Peppers"],
    "Liquids": ["Water", "Broth", "Milk", "Coconut Milk", "Cream", "Wine", "Stock"]
}

# Store selected ingredients with quantities
selected_ingredients = {}

# Dictionary to store icon images (prevents garbage collection)
icon_cache = {}

def add_ingredient(ingredient, quantity_var, category, display_frame):
    """Add an ingredient to the stew with specified quantity"""
    try:
        quantity = int(quantity_var.get())
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        selected_ingredients[ingredient] = {
            "quantity": quantity,
            "category": category
        }
        update_selection_display(display_frame)
        
        # Provide immediate feedback
        status_label.config(text=f"Added {quantity}x {ingredient}", fg=COLOR_SECONDARY)
        
        # Calculate time estimate if ingredients are present
        if selected_ingredients:
            predict_cooking_time(preview=True)
            
    except ValueError as e:
        status_label.config(text=f"Error: {str(e)}", fg=COLOR_ERROR)

def update_selection_display(frame):
    """Update the visual display of selected ingredients"""
    for widget in frame.winfo_children():
        widget.destroy()

    if not selected_ingredients:
        label = tk.Label(frame, text="Your stew pot is empty. Add ingredients to get started.", 
                        font=FONT_HELPER, fg=COLOR_TEXT, bg=COLOR_LIGHT_BG, padx=10, pady=5)
        label.pack(fill="x")
        return

    # Group ingredients by category
    categories = {}
    for ingredient, data in selected_ingredients.items():
        category = data["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((ingredient, data["quantity"]))

    # Display by category
    for category, items in categories.items():
        category_frame = tk.Frame(frame, bg=COLOR_LIGHT_BG, padx=5, pady=5)
        category_frame.pack(fill="x", pady=2)
        
        category_label = tk.Label(category_frame, text=f"{category}:", 
                                font=FONT_LABEL, fg=COLOR_PRIMARY, bg=COLOR_LIGHT_BG)
        category_label.pack(side="left", padx=5)
        
        for ingredient, quantity in items:
            item_frame = tk.Frame(category_frame, bg=COLOR_LIGHT_BG)
            item_frame.pack(side="left")
            
            item_label = tk.Label(item_frame, text=f"{quantity}x {ingredient}", 
                                font=FONT_REGULAR, fg=COLOR_TEXT, bg=COLOR_LIGHT_BG)
            item_label.pack(side="left", padx=5)
            
            # Add remove button for each ingredient
            remove_btn = tk.Button(item_frame, text="✕", font=("Arial", 10), fg="white", bg=COLOR_ERROR,
                                  command=lambda i=ingredient: remove_ingredient(i, frame), width=2)
            remove_btn.pack(side="left")

def remove_ingredient(ingredient, display_frame):
    """Remove an ingredient from the selection"""
    if ingredient in selected_ingredients:
        del selected_ingredients[ingredient]
        update_selection_display(display_frame)
        status_label.config(text=f"Removed {ingredient}", fg=COLOR_SECONDARY)
        
        # Update time estimate
        if selected_ingredients:
            predict_cooking_time(preview=True)
        else:
            result_label.config(text="")

def clear_selection(display_frame):
    """Clear all selected ingredients"""
    if not selected_ingredients:
        status_label.config(text="No ingredients to clear", fg=COLOR_TEXT)
        return
        
    selected_ingredients.clear()
    update_selection_display(display_frame)
    status_label.config(text="All ingredients cleared", fg=COLOR_TEXT)
    result_label.config(text="")

def predict_cooking_time(preview=False):
    """Calculate and display estimated cooking time"""
    if not selected_ingredients:
        result_label.config(text="Error: No ingredients selected!", font=FONT_REGULAR, fg=COLOR_ERROR)
        return
    
    try:
        # Convert to format expected by model
        model_input = {ingredient: data["quantity"] for ingredient, data in selected_ingredients.items()}
        estimated_time = model.predict_cooking_time(model_input)
        
        if preview:
            result_label.config(text=f"Estimated Time: {estimated_time} min", font=FONT_MONOSPACE, fg=COLOR_TEXT)
        else:
            result_label.config(text=f"Estimated Cooking Time: {estimated_time} min", font=FONT_MONOSPACE, fg=COLOR_PRIMARY)
            
            # Show cooking tips based on ingredients
            show_cooking_tips()
    except Exception as e:
        result_label.config(text=f"Error calculating time: {str(e)}", font=FONT_REGULAR, fg=COLOR_ERROR)

def show_cooking_tips():
    """Display cooking tips based on selected ingredients"""
    tips = []
    
    # Get categories present
    categories = {data["category"] for data in selected_ingredients.values()}
    
    if "Proteins" in categories and "Vegetables" in categories:
        tips.append("For best results, sear protein first before adding vegetables")
        
    if "Liquids" in categories and "Vegetables" in categories:
        tips.append("Add hard vegetables (potatoes, carrots) before soft ones")
    
    if tips:
        tip_text = "Cooking Tips:\n• " + "\n• ".join(tips)
        tip_label.config(text=tip_text)
    else:
        tip_label.config(text="")

def create_tab_view(parent):
    """Create tabbed view for ingredient categories"""
    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", padx=10, pady=5)
    
    # Configure the notebook style
    style = ttk.Style()
    style.configure("TNotebook", background=COLOR_BG)
    style.configure("TNotebook.Tab", background=COLOR_BG, padding=[10, 5])
    style.map("TNotebook.Tab", background=[("selected", COLOR_PRIMARY)], 
              foreground=[("selected", "white")])
    
    # Create tabs for each category
    tabs = {}
    
    for category in ingredients.keys():
        tab = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(tab, text=f" {category} ")
        tabs[category] = tab
        
    return tabs

def create_ingredient_buttons(tab, category, display_frame):
    """Create buttons for each ingredient in the category"""
    frame = tk.Frame(tab, bg=COLOR_BG)
    frame.pack(pady=10, fill="both", expand=True)
    
    # Create a scrollable frame if needed
    canvas = tk.Canvas(frame, bg=COLOR_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=COLOR_BG)
    
    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Create a grid layout
    row, col = 0, 0
    max_cols = 3
    
    for item in ingredients[category]:
        item_frame = tk.Frame(scroll_frame, bg=COLOR_BG, padx=10, pady=10, 
                             highlightbackground=COLOR_PRIMARY, highlightthickness=1)
        item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Try to load icon (placeholder for now)
        try:
            # This would be replaced with actual icons in a real implementation
            # icon_path = f"icons/{item.lower()}.png"
            # if os.path.exists(icon_path):
            #     img = Image.open(icon_path).resize((40, 40))
            #     icon = ImageTk.PhotoImage(img)
            #     icon_cache[item] = icon
            #     icon_label = tk.Label(item_frame, image=icon, bg=COLOR_BG)
            #     icon_label.pack(pady=5)
            pass
        except Exception:
            pass
            
        item_label = tk.Label(item_frame, text=item, font=FONT_LABEL, fg=COLOR_TEXT, bg=COLOR_BG)
        item_label.pack(pady=5)

        quantity_frame = tk.Frame(item_frame, bg=COLOR_BG)
        quantity_frame.pack(pady=5)
        
        quantity_label = tk.Label(quantity_frame, text="Qty:", font=FONT_HELPER, fg=COLOR_TEXT, bg=COLOR_BG)
        quantity_label.pack(side="left")
        
        quantity_var = tk.StringVar(value="1")
        quantity_menu = ttk.Combobox(quantity_frame, textvariable=quantity_var, 
                                    values=["1", "2", "3", "4", "5"], width=3, font=FONT_HELPER)
        quantity_menu.pack(side="left", padx=5)

        add_button = tk.Button(item_frame, text="Add to Stew", 
                              command=lambda i=item, q=quantity_var, c=category: 
                              add_ingredient(i, q, c, display_frame), 
                              font=FONT_HELPER, fg="white", bg=COLOR_PRIMARY,
                              activebackground=COLOR_SECONDARY, padx=10)
        add_button.pack(pady=5)
        
        # Update grid position
        col += 1
        if col >= max_cols:
            col = 0
            row += 1
    
    # Pack the canvas with scrollbar if there are many ingredients
    if len(ingredients[category]) > max_cols * 2:
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    else:
        canvas.pack(fill="both", expand=True)

def create_main_window():
    """Create the main application window"""
    root = tk.Tk()
    root.title("Stew Cooking Time Predictor")
    root.configure(bg=COLOR_BG)
    root.geometry("900x700")
    root.minsize(800, 600)

    # Add app icon (in real implementation)
    # if os.path.exists("icon.png"):
    #     icon = tk.PhotoImage(file="icon.png")
    #     root.iconphoto(True, icon)

    # Heading with subtitle
    header_frame = tk.Frame(root, bg=COLOR_BG)
    header_frame.pack(fill="x", pady=10)
    
    heading_label = tk.Label(header_frame, text="Stew Cooking Time Predictor", 
                            font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG)
    heading_label.pack()
    
    subtitle_label = tk.Label(header_frame, text="Select ingredients to calculate cooking time", 
                             font=FONT_HELPER, fg=COLOR_TEXT, bg=COLOR_BG)
    subtitle_label.pack()

    # Main content frame
    content_frame = tk.Frame(root, bg=COLOR_BG)
    content_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Create left panel for ingredients selection (tabbed)
    left_panel = tk.Frame(content_frame, bg=COLOR_BG)
    left_panel.pack(side="left", fill="both", expand=True)
    
    # Create tabbed view
    tabs = create_tab_view(left_panel)
    
    # Create right panel for selected ingredients and results
    right_panel = tk.Frame(content_frame, bg=COLOR_BG, width=300)
    right_panel.pack(side="right", fill="both", padx=10)
    right_panel.pack_propagate(False)
    
    # Selection display frame with border and title
    selection_title = tk.Label(right_panel, text="Your Stew Ingredients", 
                              font=FONT_LABEL, fg=COLOR_PRIMARY, bg=COLOR_BG)
    selection_title.pack(anchor="w", pady=(0, 5))
    
    display_frame = tk.Frame(right_panel, bg=COLOR_LIGHT_BG, bd=1, relief="solid", padx=5, pady=5)
    display_frame.pack(fill="x", pady=5)
    update_selection_display(display_frame)
    
    # Buttons
    button_frame = tk.Frame(right_panel, bg=COLOR_BG)
    button_frame.pack(fill="x", pady=10)

    predict_button = tk.Button(button_frame, text="Calculate Cooking Time", 
                              command=lambda: predict_cooking_time(preview=False), 
                              font=FONT_REGULAR, fg="white", bg=COLOR_PRIMARY,
                              activebackground=COLOR_SECONDARY, padx=10, pady=5)
    predict_button.pack(side="left", padx=5)

    clear_button = tk.Button(button_frame, text="Clear All", 
                            command=lambda: clear_selection(display_frame), 
                            font=FONT_REGULAR, fg="white", bg=COLOR_TEXT,
                            activebackground=COLOR_ERROR, padx=10, pady=5)
    clear_button.pack(side="left", padx=5)

    # Results frame
    results_frame = tk.Frame(right_panel, bg=COLOR_LIGHT_BG, bd=1, relief="solid", padx=10, pady=10)
    results_frame.pack(fill="x", pady=10)
    
    # Result label
    global result_label
    result_label = tk.Label(results_frame, text="", font=FONT_MONOSPACE, 
                           fg=COLOR_PRIMARY, bg=COLOR_LIGHT_BG, padx=5, pady=5)
    result_label.pack(fill="x")
    
    # Tips label
    global tip_label
    tip_label = tk.Label(results_frame, text="", font=FONT_HELPER, 
                        fg=COLOR_TEXT, bg=COLOR_LIGHT_BG, justify="left", padx=5, pady=5)
    tip_label.pack(fill="x")
    
    # Status bar
    global status_label
    status_bar = tk.Frame(root, bg=COLOR_PRIMARY, height=25)
    status_bar.pack(side="bottom", fill="x")
    
    status_label = tk.Label(status_bar, text="Ready to cook", font=FONT_HELPER, 
                           fg="white", bg=COLOR_PRIMARY, padx=10)
    status_label.pack(side="left")
    
    # Create ingredient buttons in tabs
    for category, tab in tabs.items():
        create_ingredient_buttons(tab, category, display_frame)

    # Bind keyboard shortcuts
    root.bind("<Control-p>", lambda e: predict_cooking_time(preview=False))
    root.bind("<Control-c>", lambda e: clear_selection(display_frame))
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    create_main_window()