import os
import pickle
import random

class Recipe:
    # Main Recipe class
    # Constructor contains the recipe fields
    # Contains from_file method which returns recipe from text file
    def __init__(self, title, ingredients, cooking_time, method, servings, meal, dietary_tags, filename=None):
        self.title = title.strip()
        self.ingredients = [i.strip() for i in ingredients if i and i.strip()]
        self.cooking_time = cooking_time.strip()
        self.method = [s.strip() for s in method if s and s.strip()]
        self.servings = servings.strip()
        self.meal = meal.strip()
        self.dietary_tags = [t.strip() for t in dietary_tags if t and t.strip()]
        self.filename = filename
    # Changed from first edition - added error handling, changed condition for line read from if it matches the field to just reading lines in order
    @classmethod
    def from_file(cls, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f]
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return None
        #Strip the lines and assign to fields based on order from the text file
        title = lines[0].strip()
        ingredients = [i.strip() for i in lines[1].split(',') if i.strip()]
        cooking_time = lines[2].strip()
        method = [s.strip() for s in lines[3].split('.') if s.strip()]
        servings = lines[4].strip() if len(lines) > 4 else ""
        meal = lines[5].strip() if len(lines) > 5 else ""
        dietary_tags = [t.strip() for t in lines[6].split(',') if t.strip()] if len(lines) > 6 else []

        return cls(title, ingredients, cooking_time, method, servings, meal, dietary_tags, filename=os.path.basename(path))
    # String version of Recipe for printing and saving to text file
    def __str__(self):
        return (
            f"Title: {self.title}\n"
            f"Ingredients: {', '.join(self.ingredients)}\n"
            f"Cooking time: {self.cooking_time}\n"
            f"Method: {'. '.join(self.method)}\n"
            f"Servings: {self.servings}\n"
            f"Meal: {self.meal}\n"
            f"Dietary tags: {', '.join(self.dietary_tags)}\n"
        )
class RecipeBook:
    # The collection of recipe objects
    # Init is private, loads from pickle or text files - encapsulation
    # Has exist_ok to create folder if not already created
    def __init__(self, folder='recipe-book-collection', pickle_file='recipeBook.pkl'):
        self.folder = os.path.join(os.path.dirname(__file__), folder)
        self.pickle_path = os.path.join(self.folder, pickle_file)
        os.makedirs(self.folder, exist_ok=True)
        self.recipes = self._load_recipes()
    # Private method to load recipes from pickle or text files
    def _load_recipes(self):
        if os.path.exists(self.pickle_path):
            try:
                with open(self.pickle_path, 'rb') as f:
                    print("Loading recipes from pickle file...")
                    return pickle.load(f)
            except Exception as e:
                print(f"Error: could not load pickle ({e}), loading from .txt files instead.")
        #If pickle load fails for whatever reason, load from text files
        recipes = []
        print("Loading recipes from text files...")
        for fname in os.listdir(self.folder):
            path = os.path.join(self.folder, fname)
            if os.path.isfile(path) and fname.endswith(".txt"):
                try:
                    recipes.append(Recipe.from_file(path))
                except Exception as e:
                    print(f"Error loading {fname}: {e}")
        return recipes
    # Private method to save recipes to pickle
    def _save_to_pickle(self):
        #Added error handling here
        try:
            with open(self.pickle_path, 'wb') as f:
                pickle.dump(self.recipes, f)
            print("Recipes saved to pickle.")
        except Exception as e:
            print(f"Error: failed to save pickle: {e}")

    def add_recipe(self, recipe):
        #Updated to include error handling and check for existing files
        filename = recipe.title.replace(' ', '_').lower() + '.txt'
        file_path = os.path.join(self.folder, filename)

        if os.path.exists(file_path):
            print(f"Error: recipe file '{filename}' already exists.")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(recipe))
            recipe.filename = os.path.basename(file_path)
            self.recipes.append(recipe)
            self._save_to_pickle()
        except Exception as e:
            print(f"Error saving recipe: {e}")

    # Update to the search function
        # Changed the name of the method to be more descriptive
        # Searches by specified field and query, returns list of matching recipes
        # Added error handling, allows capital letters/all lowercase
        # Added a better response for list fields (ingredients, method, dietary_tags)
    def search_by_field(self, field, query):
        matches = []
        q = query.lower()
        for r in self.recipes:
            if field == 'title':
                if q in r.title.lower():
                    matches.append(r)
            elif field == 'ingredient':
                if any(q in ing.lower() for ing in r.ingredients):
                    matches.append(r)
            elif field == 'cooking_time':
                if q in r.cooking_time.lower():
                    matches.append(r)
            elif field == 'method':
                if any(q in step.lower() for step in r.method):
                    matches.append(r)
            elif field == 'servings':
                if q in r.servings.lower():
                    matches.append(r)
            elif field == 'meal':
                if q in r.meal.lower():
                    matches.append(r)
            elif field == 'dietary_tags':
                if any(q in tag.lower() for tag in r.dietary_tags):
                    matches.append(r)
        return matches

    def get_random_recipe(self):
        return random.choice(self.recipes) if self.recipes else None
    # New delete recipe method
        # Deletes recipe by title, removes file from disk and updates pickle
        # Has good error handling and confirmation messages
    def delete_recipe(self, title):
        matches = self.search_by_field('title', title)

        if not matches:
            print(f"Error: recipe '{title}' not found.")
            return

        recipe = matches[0]

        if recipe.filename:
            filename = recipe.filename
        else:
            filename = recipe.title.replace(' ', '_').lower() + '.txt'
        file_path = os.path.join(self.folder, filename)
    #Using try-except for error handling during file deletion to prevent crashes
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {filename}")
            else:
                print(f"Warning: file '{filename}' not found.")

            self.recipes.remove(recipe)
            self._save_to_pickle()
            print(f"Recipe '{recipe.title}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting recipe: {e}")
    
    
    def edit_recipe(self, title):
        # Find recipe
        matches = self.search_by_field('title', title)
        if not matches:
            print(f"Error: recipe '{title}' not found.")
            return
        recipe = matches[0]

        print(f"\nEditing '{recipe.title}'...")
        print("Press Enter to keep the current value.\n")

        # Gather new fields (blank input means keep old)
        new_title = input(f"New title [{recipe.title}]: ").strip() or recipe.title

        new_ingredients = input(
            f"New ingredients (comma-separated) [{', '.join(recipe.ingredients)}]: "
        ).strip()

        if new_ingredients:
            new_ingredients = [i.strip() for i in new_ingredients.split(',')]

        else:
            new_ingredients = recipe.ingredients

        new_cooking_time = input(
            f"New cooking time [{recipe.cooking_time}]: "
        ).strip() or recipe.cooking_time

        new_method = input(
            f"New method ('.' separated) [{'. '.join(recipe.method)}]: "
        ).strip()

        if new_method:
            new_method = [s.strip() for s in new_method.split('.') if s.strip()]

        else:
            new_method = recipe.method

        new_servings = input(
            f"New servings [{recipe.servings}]: "
        ).strip() or recipe.servings

        new_meal = input(
            f"New meal [{recipe.meal}]: "
        ).strip() or recipe.meal
        new_dietary = input(
            f"New dietary tags (comma-separated) [{', '.join(recipe.dietary_tags)}]: "
        ).strip()
        if new_dietary:
            new_dietary = [t.strip() for t in new_dietary.split(',')]
        else:
            new_dietary = recipe.dietary_tags

        # Handle filename changes
        old_filename = recipe.filename or recipe.title.replace(' ', '_').lower() + ".txt"
        old_path = os.path.join(self.folder, old_filename)

        new_filename = new_title.replace(' ', '_').lower() + ".txt"
        new_path = os.path.join(self.folder, new_filename)

        # If title changed, rename the file
        if new_filename != old_filename:
            if os.path.exists(new_path):
                print("Error: A recipe with that title already exists.")
                return
            os.rename(old_path, new_path)

        # Update recipe object
        recipe.title = new_title
        recipe.ingredients = new_ingredients
        recipe.cooking_time = new_cooking_time
        recipe.method = new_method
        recipe.servings = new_servings
        recipe.meal = new_meal
        recipe.dietary_tags = new_dietary
        recipe.filename = new_filename

        # Save updated recipe to the text file
        try:
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(str(recipe))
        except Exception as e:
            print(f"Error writing recipe file: {e}")
            return

        self._save_to_pickle()

        print(f"Recipe '{new_title}' updated successfully.")
        print(recipe)
   
class RecipeApp:
    def __init__(self):
        self.book = RecipeBook()

    def run(self):
        keep_running = True
        while keep_running:
            #Updated how the menu looks
            print("\n=== Recipe Book ===")
            print("1. Search recipes")
            print("2. Create recipe")
            print("3. Delete recipe")
            print("4. Edit recipe")
            print("5. Display all recipes")
            print("6. Random recipe")
            choice = input("Enter choice (1-6): ").strip()
                    
            try:
                choice = int(choice)
            except ValueError:
                print("Invalid input, please try again")
                continue

            if choice == 1:
                self.search_menu()
            elif choice == 2:
                self.create_recipe()
            elif choice == 3:
                self.delete_recipe()
            elif choice == 4:
                self.edit_recipe()
            elif choice == 5:
                self.display_all_recipes()
            elif choice == 6:
                self.random_recipe()
            else:
                print("Invalid choice. Try again.")

            again = input("Would you like to do something else? (Y/N): ").strip().upper()
            while again not in ("Y", "N"):
                again = input("Invalid input. Please enter Y or N: ").strip().upper()
            keep_running = again == "Y"
        print("Thanks for using the Recipe Book!")
        print("Goodbye!")

    def create_recipe(self):
        # Added in functionality to not allow invalid/empty inputs
        print("\n--- Create Recipe ---")
        title = input("Recipe title: ").strip()
        if not title:
            print("Error: title cannot be empty.")
            return
       
        ingredients_input = input("Ingredients (comma-separated): ").strip()
        if not ingredients_input:
            print("Error: at least one ingredient required.")
            return
        ingredients = [i.strip() for i in ingredients_input.split(',') if i.strip()]

        cooking_time = input("Cooking time: ").strip()
        if not cooking_time:
            print("Error: cooking time required.")
            return
        # Getting method input string and splitting into list by full stops
        method_input = input("Method (separate steps with a full stop '.'): ").strip()
        if not method_input:
            print("Error: method required.")
            return
        method = [s.strip() for s in method_input.split('.') if s.strip()]
    # The rest of the fields are optional, so there's no need to validate them as not empty
        servings = input("Servings (e.g. '2' or '2-3'): ").strip()
       
        meal = input("Meal (e.g. 'breakfast', 'dinner'): ").strip()
        # Takes the dietary tags input string and splits into list by commas
        dietary_input = input("Dietary tags (comma-separated): ").strip()
        dietary_tags = [t.strip() for t in dietary_input.split(',') if t.strip()] if dietary_input else []

    # Create Recipe object and add to RecipeBook
        recipe = Recipe(title, ingredients, cooking_time, method, servings, meal, dietary_tags)
        self.book.add_recipe(recipe)

        print(f"Your recipe for'{title}' has been saved!.")
        print(recipe)

    def search_menu(self):
        print("\n--- Search Recipes ---")
        #fields is a list of tuples containing field keys and their display names
        fields = [
            ('title', 'Title'),
            ('ingredient', 'Ingredient'),
            ('cooking_time', 'Cooking time'),
            ('method', 'Method'),
            ('servings', 'Servings'),
            ('meal', 'Meal'),
            ('dietary_tags', 'Dietary tags')
        ]
        # Changed how the search menu looks, removed random recipe option from here, and made it its own method
        # The menu for the search fields
        for i in range(len(fields)):
            print(f"{i + 1}. {fields[i][1]}")
        choice = input(f"Choose field to search (1-{len(fields)}): ").strip()
        try:
            search_choice = int(choice) - 1
            if search_choice < 0 or search_choice >= len(fields):
                print("Invalid choice.")
                return
        except ValueError:
            print("Invalid choice.")
            return
    # Get search query from user
        field_key = fields[search_choice][0]
        query = input(f"Enter search text for {fields[search_choice][1]}: ").strip()
        if not query:
            print("Search text can't be empty.")
            return
    # Perform search
    # Changed so now all results found are in a list and printed out
        results = self.book.search_by_field(field_key, query)
        if results:
            for recipe in results:
                print(f"\n{recipe}")
        else:
            print("No matching recipes found. Try again.")

    def display_all_recipes(self):
        print("\n--- All Recipes ---")
        if not self.book.recipes:
            print("No recipes available.")
            return
        for recipe in self.book.recipes:
            print(f"\n{recipe}")
# This is the instance of delete recipe method in RecipeApp, it calls the delete_recipe method in RecipeBook
    def delete_recipe(self):
        print("\n--- Delete Recipe ---")
        title = input("Enter recipe title to delete: ").strip()
        confirm = input(f"Are you sure you want to delete '{title}'? (yes/no): ").strip().lower()

        if confirm == 'yes':
            self.book.delete_recipe(title)
# I made random recipe its own method, added error handling for no recipes
    def random_recipe(self):
        print("\n--- Random Recipe ---")
        recipe = self.book.get_random_recipe()
        if recipe:
            print(f"\n{recipe}")
        else:
            print("No recipes available.")
    
    def edit_recipe(self):
            print("\n--- Edit Recipe ---")
            title = input("Enter the title of the recipe to edit: ").strip()
            self.book.edit_recipe(title)

# Main run point
if __name__ == "__main__":
    app = RecipeApp()
    app.run()