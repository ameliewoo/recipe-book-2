import os
import random
import pickle

# Recipe class to hold individual recipe details
# It is a private class that is only used within this file - encapsulation
class Recipe:
    # Purpose: hold recipe fields and normalize inputs
    # Inputs: title(str), ingredients(list[str]), cooking_time(str), method(list[str]), servings(str), meal(str), dietary_tags(list[str]), filename(str|None)
    # Outputs: Recipe instance with trimmed strings and normalized lists
    # Side-effects: strips whitespace from inputs; stores source filename if provided
    # Errors: TypeError if inputs are not iterable where expected
    def __init__(self, title, ingredients, cooking_time, method, servings, meal, dietary_tags, filename=None):
        self.title = title.strip()
        self.ingredients = [i.strip() for i in ingredients if i and i.strip()]
        self.cooking_time = cooking_time.strip()
        self.method = [s.strip() for s in method if s and s.strip()]
        self.servings = servings.strip()
        self.meal = meal.strip()
        self.dietary_tags = [t.strip() for t in dietary_tags if t and t.strip()]
        self.filename = filename
# loads recipe from a text file
# takes inputs of cls and path
    @classmethod
    # Purpose: parse a structured .txt recipe file into a Recipe
    # Inputs: path (str) to a .txt file (first line title, subsequent 'Key: value' lines)
    # Outputs: Recipe instance (returns empty-titled Recipe on read error)
    # Side-effects: prints a warning on file read/parse issues
    # Errors: does not raise on parse errors; returns fallback Recipe instead
    def from_file(cls, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = [l.rstrip('\n') for l in f]
        except Exception as e:
            logger.warning("Failed to read recipe file '%s': %s", path, e)
            return cls("", [], "", [], "", "", [], filename=os.path.basename(path))

        title = lines[0].strip() if lines else ""
        ingredients, cooking_time, method, servings, meal, dietary_tags = [], "", [], "", "", []

        for line in lines[1:]:
            if not line:
                continue
            try:
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                key, val = parts[0].strip().lower(), parts[1].strip()
                if key == 'ingredients':
                    ingredients = [i.strip() for i in val.split(',') if i.strip()]
                elif key == 'cooking time':
                    cooking_time = val
                elif key == 'method':
                    method = [s.strip() for s in val.split('.') if s.strip()]
                elif key in ('serving size', 'servings'):
                    servings = val
                elif key == 'meal':
                    meal = val
                elif key in ('dietary tags', 'diet'):
                    dietary_tags = [t.strip() for t in val.split(',') if t.strip()]
            except Exception:
                continue

        return cls(title, ingredients, cooking_time, method, servings, meal, dietary_tags, filename=os.path.basename(path))
# Matches -  checks if recipe matches search criteria
#self - the instance of the Recipe class
#criteria - the field to search by (title, ingredients, etc.)
#query - the search term or terms
    # Purpose: test whether this recipe matches a search query
    # Inputs: criteria(str) - 'title'|'ingredients'|'servings'|'meal'|'diet'; query (str|list)
    # Outputs: bool
    # Notes: string matching is case-insensitive; ingredients expects a list
    def matches(self, criteria, query):
        if isinstance(query, str):
            query = query.strip().lower()

        recipe_fields = {
            'title': lambda: self.title.lower() == query,
            'ingredients': lambda: isinstance(query, list) and set(i.lower() for i in query).issubset(set(i.lower() for i in self.ingredients)),
            'servings': lambda: self.servings.lower() == query,
            'meal': lambda: self.meal.lower() == query,
            'diet': lambda: query in (t.lower() for t in self.dietary_tags)
        }
        return recipe_fields.get(criteria, lambda: query in self.title.lower())()

    # Purpose: return a plain-text representation suitable for saving to .txt
    # Inputs: none
    # Outputs: str representation with title and 'Key: value' lines
    def __str__(self):
        return (
            f"{self.title}\n"
            f"Ingredients: {', '.join(self.ingredients)}\n"
            f"Cooking time: {self.cooking_time}\n"
            f"Method: {'. '.join(self.method)}\n"
            f"Serving size: {self.servings}\n"
            f"Meal: {self.meal}\n"
            f"Dietary tags: {', '.join(self.dietary_tags)}\n"
        )


class RecipeBook:
    # Purpose: manage a collection of Recipe objects and persistence
    # Keywords: load, save, add, search, delete
    def __init__(self, folder='recipe-book-collection', pickle_file='recipes.pkl'):
        self.folder = os.path.join(os.path.dirname(__file__), folder)
        self.pickle_path = os.path.join(self.folder, pickle_file)
        os.makedirs(self.folder, exist_ok=True)
        self.recipes = self._load_recipes()
# loads recipes from pickle file or text files if pcikles files are unavailable
    # Purpose: load recipes from pickle for speed or from .txt files as fallback
    # Inputs: none (uses configured folder and pickle path)
    # Outputs: list[Recipe]
    # Side-effects: reads filesystem, prints warnings on errors
    def _load_recipes(self):
        if os.path.exists(self.pickle_path):
            try:
                with open(self.pickle_path, 'rb') as f:
                    logger.info("Loading recipes from pickle file...")
                    try:
                        return pickle.load(f)
                    except Exception as e:
                        logger.warning("Pickle file is corrupt or unreadable, falling back to .txt files: %s", e)
            except Exception as e:
                logger.warning("Failed to open pickle file, loading from .txt instead: %s", e)

        recipes = []
        for fname in os.listdir(self.folder):
            path = os.path.join(self.folder, fname)
            if os.path.isfile(path) and fname.endswith(".txt"):
                try:
                    recipes.append(Recipe.from_file(path))
                except Exception as e:
                    print(f"Error loading {fname}: {e}")
        return recipes
# saves recipes to a pickle file
    # Purpose: persist in-memory recipes list to a pickle file for faster startup
    # Inputs: none
    # Outputs: None
    # Side-effects: writes to filesystem; prints error on failure
    def _save_to_pickle(self):
        # atomic write to avoid corrupting existing pickle
        try:
            dirpath = os.path.dirname(self.pickle_path) or self.folder
            fd, tmp_path = tempfile.mkstemp(dir=dirpath)
            try:
                with os.fdopen(fd, 'wb') as f:
                    pickle.dump(self.recipes, f)
                os.replace(tmp_path, self.pickle_path)
                logger.info("Recipes saved to pickle file.")
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error("Failed to save recipes to pickle file: %s", e)
# adds a new recipe to the collection
    # Purpose: create a .txt file for a new recipe and add it to the index
    # Inputs: recipe (Recipe)
    # Outputs: None
    # Side-effects: writes a file and updates pickle; may raise FileExistsError or ValueError
    def add_recipe(self, recipe):
        safe_title = (recipe.title or "untitled").strip()
        if not safe_title:
            raise ValueError("Recipe must have a title")

        # sanitize filename
        filename = _sanitize_filename(safe_title)
        file_path = os.path.join(self.folder, f"{filename}.txt")

        if os.path.exists(file_path):
            raise FileExistsError(f"Recipe file '{file_path}' already exists.")

        # write atomically
        try:
            fd, tmp_path = tempfile.mkstemp(dir=self.folder)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(str(recipe))
                os.replace(tmp_path, file_path)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error("Failed to write recipe file '%s': %s", file_path, e)
            raise

        # attach filename to recipe and update pickle
        recipe.filename = os.path.basename(file_path)
        self.recipes.append(recipe)
        self._save_to_pickle()
# searches for recipes based on criteria and query
    # Purpose: find recipes matching a criteria
    # Inputs: criteria (str), query (str|list), return_first (bool)
    # Outputs: list[Recipe] or Recipe (if return_first=True)
    def search(self, criteria, query, return_first=False):
        if criteria == 'ingredients' and isinstance(query, str):
            query = [i.strip() for i in query.split(',') if i.strip()]
        elif isinstance(query, str):
            query = query.strip()

        matches = [r for r in self.recipes if r.matches(criteria, query)]
        return matches[0] if return_first and matches else matches

    # Purpose: convenience: return a random recipe for suggestion
    # Inputs: none
    # Outputs: Recipe or None
    def get_random_recipe(self):
        return random.choice(self.recipes) if self.recipes else None
# deletes a recipe from the collection by title
    # Purpose: remove a recipe by title from the index and delete its file
    # Inputs: title (str)
    # Outputs: bool - True if deletion occurred, False if not found
    # Side-effects: removes .txt file and updates pickle; prints warnings on IO errors
    def delete_recipe(self, title):
        title = title.strip().lower()
        recipe_to_delete = None
        for recipe in self.recipes:
            if recipe.title.lower() == title:
                recipe_to_delete = recipe
                break
        
        if recipe_to_delete:
            try:
                self.recipes.remove(recipe_to_delete)
            except ValueError:
                pass

            # delete the text file
            if recipe_to_delete.filename:
                file_path = os.path.join(self.folder, recipe_to_delete.filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Warning: failed to remove recipe file '{file_path}': {e}")

            # update pickle
            try:
                self._save_to_pickle()
            except Exception as e:
                print(f"Warning: failed to update pickle after deletion: {e}")
            return True
        return False
# Main application class to run the recipe book program
class RecipeApp:
    # Purpose: command-line interface for RecipeBook operations
    # Keywords: menu, user input, create, search, delete
    def __init__(self):
        self.book = RecipeBook()

    # Purpose: main interactive loop - show menu and dispatch actions
    # Inputs: user keystrokes via stdin
    # Outputs: printed prompts and action results
    def run(self):
        keep_running = True
        while keep_running:
            print('*' * 30)
            print("Welcome to the Recipe Book")
            print('*' * 30)

            choice = input("Are you:\n\tSearching for a recipe? - enter 1\n\tCreating a new recipe? - enter 2\n\tDeleting a recipe? - enter 3\n")
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
                self.delete_recipe_menu()
            else:
                print("Invalid option, please try again")

            again = input("Would you like to do something else? (Y/N): ").strip().upper()
            while again not in ("Y", "N"):
                again = input("Invalid input. Please enter Y or N: ").strip().upper()
            keep_running = again == "Y"

        print("Goodbye!")
# creates a new recipe by taking user input
    def create_recipe(self):
        print("================================")
        # gather inputs with basic validation
        title = input("Enter the title of the recipe: ").strip()
        if not title:
            print("Title cannot be empty. Aborting.")
            return

        ingredients_raw = input("Enter the ingredients (comma-separated): ").strip()
        ingredients = [i.strip() for i in ingredients_raw.split(',') if i.strip()]
        if not ingredients:
            print("At least one ingredient is required. Aborting.")
            return

        cooking_time = input("Enter the cooking time (e.g., '10 minutes'): ").strip()
        method_raw = input("Enter the method (steps separated by full stops): ").strip()
        method = [s.strip() for s in method_raw.split('.') if s.strip()]
        servings = input("Enter the serving size: ").strip()
        meal = input("Enter the meal type: ").strip()
        dietary_tags_raw = input("Enter the dietary tags (comma-separated): ").strip()
        dietary_tags = [t.strip() for t in dietary_tags_raw.split(',') if t.strip()]

        recipe = Recipe(title, ingredients, cooking_time, method, servings, meal, dietary_tags)

        # compute safe filename to check for existing file
        safe_title = (title or "untitled").strip()
        filename = "".join(c for c in safe_title if c.isalnum() or c in (" ","-","_")).rstrip()
        filename = filename.replace(' ', '_') or 'untitled'
        file_path = os.path.join(self.book.folder, f"{filename}.txt")

        if os.path.exists(file_path):
            overwrite = input(f"A recipe file named '{filename}.txt' already exists. Overwrite? (Y/N): ").strip().upper()
            while overwrite not in ("Y", "N"):
                overwrite = input("Please enter Y or N: ").strip().upper()
            if overwrite == 'N':
                print("Creation cancelled. No changes made.")
                return
            # attempt overwrite
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(recipe))
                # replace existing recipe in memory if title matches
                existing = self.book.search('title', title, return_first=True)
                if existing:
                    try:
                        self.book.recipes.remove(existing)
                    except ValueError:
                        pass
                recipe.filename = f"{filename}.txt"
                self.book.recipes.append(recipe)
                self.book._save_to_pickle()
                print(f"Recipe for '{title}' saved (overwritten).")
            except Exception as e:
                print(f"Failed to overwrite recipe file: {e}")
                return
        else:
            try:
                self.book.add_recipe(recipe)
                print(f"Recipe for '{title}' saved!")
            except FileExistsError as e:
                print(e)
            except Exception as e:
                print(f"Failed to save recipe: {e}")
#  search menu to find recipes based on different criteria
    def search_menu(self):
        print("=========================================")
        try:
            choice = int(input("Search options:\n"
                "\tSearch by Title - enter 1\n"
                "\tSearch by Ingredients - enter 2\n"
                "\tSearch by Serving Size - enter 3\n"
                "\tSearch by Meal - enter 4\n"
                "\tSearch by dietary tags - enter 5\n"
                "\tRandom recipe! - enter 0\n"
                "===========================================\n"
                "Please enter your choice:   "))
        except ValueError:
            print("Invalid input")
            return

        fields = {
            1: 'title',
            2: 'ingredients',
            3: 'servings',
            4: 'meal',
            5: 'diet'
        }
        # if user chooses random recipe, find a random recipe if present
        if choice == 0:
            recipe = self.book.get_random_recipe()
            print("Random Recipe:\n", recipe if recipe else "No recipes available.")
        elif choice in fields:
            query = input(f"Enter your search query for {fields[choice]}: ").strip()
            results = self.book.search(fields[choice], query)
            if results:
                for r in results:
                    print("Recipe found:\n", r)
            else:
                print("No matching recipes found.")
        else:
            print("Invalid option")
# delete menu to remove recipes
    def delete_recipe_menu(self):
        print("================================")
        title = input("Enter the title of the recipe you want to delete: ").strip()
        if not title:
            print("No title entered. Aborting.")
            return

        existing = self.book.search('title', title, return_first=True)
        if not existing:
            print(f"Recipe '{title}' not found.")
            return

        confirm = input(f"Are you sure you want to delete '{title}'? This cannot be undone. (Y/N): ").strip().upper()
        while confirm not in ("Y", "N"):
            confirm = input("Please enter Y or N: ").strip().upper()
        if confirm == 'N':
            print("Deletion cancelled.")
            return

        try:
            if self.book.delete_recipe(title):
                print(f"Recipe '{title}' has been deleted successfully!")
            else:
                print(f"Recipe '{title}' not found or could not be deleted.")
        except Exception as e:
            print(f"An error occurred deleting the recipe: {e}")


if __name__ == "__main__":
    app = RecipeApp()
    app.run()