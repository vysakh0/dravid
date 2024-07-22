import unittest
from drd.utils.step_executor import apply_changes  # Update this import as needed


class TestApplyChangesSpecific(unittest.TestCase):
    def test_add_email_and_move_paragraph(self):
        original_content = """<body>
    <h1>Welcome to Our Company</h1>
    <p>We are a leading provider of services.</p>
</body>
<p>More information.</p>
"""
        changes = """
+ 4:<p>Email: info@ourcompany.com</p>
- 5:
+ 5:<p>Contact us for more information.</p>
"""
        expected_content = """<body>
    <h1>Welcome to Our Company</h1>
    <p>We are a leading provider of services.</p>
<p>Email: info@ourcompany.com</p>
<p>Contact us for more information.</p>
</body>
"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)

    def test_replace_with_preserved_indentation(self):
        original_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a + b;
    console.log(c);
}"""
        changes = """
r 4:    var c = a * b;
"""
        expected_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a * b;
    console.log(c);
}"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)

    def test_multiple_additions_with_indentation(self):
        original_content = """function example() {
    var a = 1;
    var b = 2;
}"""
        changes = """
+ 4:    if a == 1:
+ 5:        console.log(c);
"""
        expected_content = """function example() {
    var a = 1;
    var b = 2;
    if a == 1:
        console.log(c);
}"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)

    def test_multiple_deletions(self):
        original_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a + b;
    console.log(c);
}"""
        changes = """
- 4:
- 5:
"""
        expected_content = """function example() {
    var a = 1;
    var b = 2;
}"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)

    def test_complex_changes(self):
        original_content = """<html>
    <head>
        <title>Old Title</title>
    </head>
    <body>
        <h1>Header</h1>
        <p>Old paragraph.</p>
        <footer>Old footer</footer>
    </body>
    </html>"""
        changes = """
    r 3:        <title>New Title</title>
    r 6:        <h1>New Header</h1>
    r 7:        <p>New paragraph.</p>
    + 8:        <p>Additional paragraph.</p>
    - 8:
    """
        expected_content = """<html>
    <head>
        <title>New Title</title>
    </head>
    <body>
        <h1>New Header</h1>
        <p>New paragraph.</p>
        <p>Additional paragraph.</p>
    </body>
    </html>"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)

    def test_python_code_add_replace(self):
        original_content = """def my_function():
    a = 10
    b = 20
    result = a + b
    print(result)
"""
        changes = """
r 4:    result = a * b
+ 5:    return result
"""
        expected_content = """def my_function():
    a = 10
    b = 20
    result = a * b
    return result
    print(result)
"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result, expected_content)
