import re


def apply_changes(original_content, changes_str):
    original_lines = original_content.split('\n')
    changes = changes_str.strip().split('\n')

    deletions = []
    replacements = []
    additions = []

    for change in changes:
        change = change.strip()  # Strip unnecessary spaces
        match = re.match(r'([r\-+])\s*(\d+):(.*)', change)
        if match:
            action = match.group(1)
            line_num = int(match.group(2))
            content = match.group(3).lstrip()  # Preserve leading spaces

            if action == 'r':
                replacements.append((line_num, content))
            elif action == '-':
                deletions.append(line_num)
            elif action == '+':
                additions.append((line_num, content))

    # Apply deletions in reverse order to avoid index shift issues
    deletions.sort(reverse=True)
    for line_num in deletions:
        if 0 <= line_num - 1 < len(original_lines):
            del original_lines[line_num - 1]

    # Apply replacements with preserved indentation
    for line_num, content in replacements:
        if 0 <= line_num - 1 < len(original_lines):
            current_line = original_lines[line_num - 1]
            indent = re.match(r'(\s*)', current_line).group(1)
            original_lines[line_num - 1] = indent + content

    # Apply additions with preserved indentation
    additions.sort()
    for line_num, content in additions:
        if 0 <= line_num - 1 <= len(original_lines):
            current_line = original_lines[line_num -
                                          1] if line_num - 1 < len(original_lines) else ''
            indent = re.match(r'(\s*)', current_line).group(1)
            original_lines.insert(line_num - 1, indent + content)

    return '\n'.join(original_lines)
