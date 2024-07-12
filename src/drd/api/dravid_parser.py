import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import re
import click


def extract_and_parse_xml(response: str) -> ET.Element:
    # Try to extract the outermost XML content
    xml_start = response.find('<response>')
    xml_end = response.rfind('</response>')
    if xml_start != -1 and xml_end != -1:
        # +11 to include '</response>'
        xml_content = response[xml_start:xml_end + 11]
    else:
        raise ValueError("No valid XML response found")

    # Remove any content after the closing </response> tag
    xml_content = re.sub(r'</response>.*$', '</response>',
                         xml_content, flags=re.DOTALL)

    # Escape any nested CDATA sections
    xml_content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', lambda m: '<![CDATA[' + m.group(
        1).replace(']]>', ']]]]><![CDATA[>') + ']]>', xml_content, flags=re.DOTALL)

    # Parse the XML
    try:
        root = ET.fromstring(xml_content)
        return root
    except ET.ParseError as e:
        print("---errroro", response)
        print(f"Error parsing XML: {e}")
        print("Original response:")
        print(response)

        # Attempt to identify the problematic part
        line_num, col_num = e.position
        lines = xml_content.split('\n')
        if line_num <= len(lines):
            problematic_line = lines[line_num - 1]
            print(f"Problematic line ({line_num}):")
            print(problematic_line)
            print(' ' * (col_num - 1) + '^')

            # Try to fix common issues
            fixed_line = re.sub(
                r'&(?!amp;|lt;|gt;|apos;|quot;)', '&amp;', problematic_line)
            if fixed_line != problematic_line:
                print("Attempting to fix the line:")
                print(fixed_line)
                lines[line_num - 1] = fixed_line
                fixed_xml = '\n'.join(lines)
                try:
                    return ET.fromstring(fixed_xml)
                except ET.ParseError:
                    print("Fix attempt failed.")

        raise


def parse_dravid_response(response: str) -> List[Dict[str, Any]]:
    try:
        root = extract_and_parse_xml(response)
        commands = []
        explanation = root.find('explanation')
        if explanation is not None and explanation.text:
            commands.append({
                'type': 'explanation',
                'content': explanation.text.strip()
            })
        for step in root.findall('.//step'):
            command = {}
            for child in step:
                if child.tag == 'content':
                    command[child.tag] = child.text.strip(
                    ) if child.text else ''
                else:
                    command[child.tag] = child.text
            commands.append(command)
        return commands
    except Exception as e:
        print(f"Error parsing dravid response: {e}")
        print("Original response:")
        print(response)
        return []


def pretty_print_commands(commands: List[Dict[str, Any]]):
    for i, cmd in enumerate(commands, 1):
        click.echo(click.style(f"\nCommand {i}:", fg="cyan", bold=True))

        if cmd['type'] == 'file':
            if cmd['filename'] == 'metadata':
                continue
            filename = cmd.get('filename', 'Unknown file')
            operation = cmd.get('operation', 'Unknown operation')
            content = cmd.get('content', '')

            click.echo(click.style(
                f"File Operation: {operation} {filename}", fg="yellow"))

            if content:
                click.echo(click.style("Content:", fg="yellow"))
                try:
                    from pygments import highlight
                    from pygments.lexers import get_lexer_by_name, guess_lexer
                    from pygments.formatters import TerminalFormatter

                    try:
                        lexer = get_lexer_by_name(filename.split('.')[-1])
                    except:
                        lexer = guess_lexer(content)

                    formatted_content = f"# {filename}\n{content}"
                    highlighted_content = highlight(
                        formatted_content, lexer, TerminalFormatter())
                    click.echo(highlighted_content)
                except Exception as e:
                    # Fallback to non-highlighted output
                    click.echo(f"# {filename}")
                    click.echo(content)
                    click.echo(click.style(
                        f"Note: Syntax highlighting unavailable. Displaying raw content.", fg="yellow"))

        elif cmd['type'] == 'shell':
            command = cmd.get('command', '')
            click.echo(click.style("Shell Command:", fg="blue"))
            try:
                from pygments import highlight
                from pygments.lexers import get_lexer_by_name
                from pygments.formatters import TerminalFormatter

                lexer = get_lexer_by_name('bash')
                highlighted_command = highlight(
                    command, lexer, TerminalFormatter())
                click.echo(highlighted_command)
            except:
                # Fallback to non-highlighted output
                click.echo(click.style(command, fg="blue"))

        elif cmd['type'] == 'explanation':
            click.echo(click.style("Explanation:", fg="green"))
            click.echo(cmd['content'])

        else:
            for key, value in cmd.items():
                click.echo(f"  {key.capitalize()}: {value}")

    click.echo()
