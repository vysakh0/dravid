import unittest
from drd.utils.step_executor import apply_changes  # Update this import as needed


class TestApplyChangesSpecific(unittest.TestCase):
    def test_add_email_and_move_paragraph(self):
        original_content = """<body>
    <h1>Welcome to Our Company</h1>
    <p>We are a leading provider of services.</p>
</body>
<p>Contact us for more information.</p>
"""
        changes = """
+ 4: <p>Email: info@ourcompany.com</p>
- 5:
+ 5: <p>Contact us for more information.</p>
"""
        expected_content = """<body>
    <h1>Welcome to Our Company</h1>
    <p>We are a leading provider of services.</p>
<p>Email: info@ourcompany.com</p>
<p>Contact us for more information.</p>
</body>"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result.replace(' ', '').replace('\n', ''),
                         expected_content.replace(' ', '').replace('\n', ''))

    # def test_html_structure_changes(self):
    #     original_content = """<!DOCTYPE html>
    # <html lang="en">
    # <head>
    #     <meta charset="UTF-8">
    #     <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #     <title>Document</title>
    # </head>
    # <body>
    #     <h1>Welcome to Our Company</h1>
    #     <h3>hello</h3>
    #     <h2>About Us</h2>
    #     <p>Address: 123 Main Street, Anytown, ST 12345</p>
    # </body>
    # <p>Phone: (555) 123-4567</p>
    # </html>"""
    #     changes = """
    # r 6: <title>About Us - TestApp</title>
    # r 11: <h2>About Us</h2>
    # r 12: <p>Address: 123 Main Street, Anytown, ST 12345</p>
    # r 13: <p>Phone: (555) 123-4567</p>
    # + 14: <p>Email: srvysah@sdf.com</p>
    # - 14:
    # - 15:
    # """
    #     expected_content = """<!DOCTYPE html>
    # <html lang="en">
    # <head>
    #     <meta charset="UTF-8">
    #     <meta name="viewport" content="width=device-width, initial-scale=1.0">
    # <title>About Us - TestApp</title>
    # </head>
    # <body>
    #     <h1>Welcome to Our Company</h1>
    #     <h3>hello</h3>
    # <h2>About Us</h2>
    # <p>Address: 123 Main Street, Anytown, ST 12345</p>
    # <p>Phone: (555) 123-4567</p>
    # <p>Email: srvysah@sdf.com</p>
    # </body>
    # </html>"""
    #     result = apply_changes(original_content, changes)
    #     print(result, "--")
    #     self.assertEqual(result.replace(' ', '').replace('\n', ''),
    #                      expected_content.replace(' ', '').replace('\n', ''))

    def test_replace_with_preserved_indentation(self):
        original_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a + b;
    console.log(c);
}"""
        changes = """
r 4: var c = a * b;
"""
        expected_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a * b;
    console.log(c);
}"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result.replace(' ', '').replace('\n', ''),
                         expected_content.replace(' ', '').replace('\n', ''))

    def test_multiple_additions_with_indentation(self):
        original_content = """function example() {
    var a = 1;
    var b = 2;
}"""
        changes = """
+ 4: var c = a + b;
+ 5: console.log(c);
"""
        expected_content = """function example() {
    var a = 1;
    var b = 2;
    var c = a + b;
    console.log(c);
}"""
        result = apply_changes(original_content, changes)
        self.assertEqual(result.replace(' ', '').replace('\n', ''),
                         expected_content.replace(' ', '').replace('\n', ''))

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
    r 3: <title>New Title</title>
    r 6: <h1>New Header</h1>
    r 7: <p>New paragraph.</p>
    + 8: <p>Additional paragraph.</p>
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
        self.assertEqual(result.replace(' ', '').replace('\n', ''),
                         expected_content.replace(' ', '').replace('\n', ''))


if __name__ == '__main__':
    unittest.main()
