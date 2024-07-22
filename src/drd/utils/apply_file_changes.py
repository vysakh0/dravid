import re


def apply_changes(original_content, changes_str):
    original_lines = original_content.split('\n')
    changes = changes_str.strip().split('\n')
    deletions = set()
    replacements = {}
    additions = []

    for change in changes:
        change = change.strip()  # Strip unnecessary spaces
        match = re.match(r'([r\-+])\s*(\d+):(.*)', change)
        if match:
            action = match.group(1)
            line_num = int(match.group(2))
            content = match.group(3)  # Do not strip leading spaces here
            if action == 'r':
                replacements[line_num] = content
            elif action == '-':
                deletions.add(line_num)
            elif action == '+':
                additions.append((line_num, content))

    # Apply changes
    result_lines = []
    for i, line in enumerate(original_lines, start=1):
        if i in deletions:
            continue
        if i in replacements:
            result_lines.append(replacements[i])
        else:
            result_lines.append(line)

    # Apply additions
    for line_num, content in sorted(additions):
        result_lines.insert(line_num - 1, content)

    return '\n'.join(result_lines)
