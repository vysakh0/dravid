import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import re
import click
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import TerminalFormatter


def extract_outermost_xml(response: str) -> str:
    xml_start = response.find('<response>')
    xml_end = response.rfind('</response>')
    if xml_start != -1 and xml_end != -1:
        return response[xml_start:xml_end + 11]
    raise ValueError("No valid XML response found")


def escape_nested_cdata(xml_content: str) -> str:
    return re.sub(
        r'<!\[CDATA\[(.*?)\]\]>',
        lambda m: '<![CDATA[' + m.group(1).replace(']]>',
                                                   ']]]]><![CDATA[>') + ']]>',
        xml_content,
        flags=re.DOTALL
    )


def escape_special_characters(xml_content: str) -> str:
    return xml_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def extract_and_parse_xml(response: str) -> ET.Element:
    try:
        xml_content = extract_outermost_xml(response)
        xml_content = escape_nested_cdata(xml_content)

        # Escape special characters in content, but not in tags
        xml_content = re.sub(
            r'(>)([^<]+)(<)',
            lambda m: m.group(
                1) + escape_special_characters(m.group(2)) + m.group(3),
            xml_content
        )

        return ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        print("Original response:")
        print(response)
        print("Processed XML content:")
        print(xml_content)
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
            if cmd.get('filename') == 'metadata':
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
