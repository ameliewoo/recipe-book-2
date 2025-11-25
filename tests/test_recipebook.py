import os
import unittest
import tempfile

from main import Recipe, RecipeBook

class TestRecipeBook(unittest.TestCase):
    def test_add_search_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # use absolute path (RecipeBook will accept absolute folder)
            book = RecipeBook(folder=tmpdir, pickle_file='recipes_test.pkl')

            # start empty
            self.assertEqual(book.recipes, [])

            r = Recipe(
                title='Test Pancake',
                ingredients=['flour', 'egg', 'milk'],
                cooking_time='10 minutes',
                method=['mix', 'cook'],
                servings='2',
                meal='breakfast',
                dietary_tags=['vegetarian']
            )

            # add recipe
            book.add_recipe(r)
            # file exists
            filename = r.filename
            self.assertTrue(filename)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, filename)))

            # search by title
            found = book.search('title', 'Test Pancake', return_first=True)
            self.assertIsNotNone(found)
            self.assertEqual(found.title, 'Test Pancake')

            # delete
            deleted = book.delete_recipe('Test Pancake')
            self.assertTrue(deleted)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, filename)))

            # confirm removed from index
            self.assertFalse(book.search('title', 'Test Pancake'))

if __name__ == '__main__':
    unittest.main()
