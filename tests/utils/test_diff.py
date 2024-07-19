import unittest
from drd.utils.diff import generate_colored_diff, preview_file_changes
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class TestDiffUtils(unittest.TestCase):

    def test_generate_colored_diff(self):
        original_content = "Line 1\nLine 2\nLine 3\n"
        new_content = "Line 1\nModified Line 2\nLine 3\nNew Line 4\n"

        expected_diff = (
            f"{Fore.RED}--- {Style.RESET_ALL}\n"
            f"{Fore.GREEN}+++ {Style.RESET_ALL}\n"
            f"@@ -1,3 +1,4 @@\n"
            f" Line 1\n"
            f"{Fore.RED}-Line 2{Style.RESET_ALL}\n"
            f"{Fore.GREEN}+Modified Line 2{Style.RESET_ALL}\n"
            f" Line 3\n"
            f"{Fore.GREEN}+New Line 4{Style.RESET_ALL}"
        )

        result = generate_colored_diff(original_content, new_content)
        self.assertEqual(result, expected_diff)

    def test_preview_file_changes_create(self):
        result = preview_file_changes(
            'CREATE', 'new_file.txt', new_content='New file content')
        expected_output = (
            f"{Fore.CYAN}{Style.BRIGHT}File: new_file.txt{Style.RESET_ALL}\n"
            f"{Fore.GREEN}{Style.BRIGHT}Operation: CREATE{Style.RESET_ALL}\n"
            f"{Fore.GREEN}New content:{Style.RESET_ALL}\n"
            f"{Fore.GREEN}New file content{Style.RESET_ALL}"
        )
        self.assertEqual(result, expected_output)

    def test_preview_file_changes_update(self):
        original_content = "Line 1\nLine 2\nLine 3\n"
        new_content = "Line 1\nModified Line 2\nLine 3\nNew Line 4\n"
        result = preview_file_changes(
            'UPDATE', 'existing_file.txt', new_content=new_content, original_content=original_content)
        self.assertIn(
            f"{Fore.YELLOW}{Style.BRIGHT}Operation: UPDATE{Style.RESET_ALL}", result)
        self.assertIn(f"{Fore.RED}-Line 2{Style.RESET_ALL}", result)
        self.assertIn(f"{Fore.GREEN}+Modified Line 2{Style.RESET_ALL}", result)
        self.assertIn(f"{Fore.GREEN}+New Line 4{Style.RESET_ALL}", result)

    def test_preview_file_changes_delete(self):
        result = preview_file_changes('DELETE', 'file_to_delete.txt')
        expected_output = (
            f"{Fore.CYAN}{Style.BRIGHT}File: file_to_delete.txt{Style.RESET_ALL}\n"
            f"{Fore.RED}{Style.BRIGHT}Operation: DELETE{Style.RESET_ALL}\n"
            f"{Fore.RED}The file 'file_to_delete.txt' will be deleted.{Style.RESET_ALL}"
        )
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
