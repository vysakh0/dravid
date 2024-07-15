import pytest
from drd.utils.pretty_print_stream import stream_and_print_commands


def test_basic_explanation(capsys):
    chunks = [
        "<response>",
        "<explanation>This is a basic explanation.</explanation>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: This is a basic explanation." in captured.out


def test_spaced_tags(capsys):
    chunks = [
        "< response >",
        "  < explanation >",
        "This is an explanation with spaced tags.",
        "  < /explanation >",
        "</ response >"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: This is an explanation with spaced tags." in captured.out


def test_newline_in_tags(capsys):
    chunks = [
        "<response\n>",
        "<explanation\n>",
        "This is an explanation with newlines in tags.",
        "</explanation\n>",
        "</response\n>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: This is an explanation with newlines in tags." in captured.out


def test_mixed_spacing_and_newlines(capsys):
    chunks = [
        "< response \n >",
        "  <\nexplanation \n >",
        "This is an explanation with mixed spacing and newlines.",
        "  < /explanation\n >",
        "</ response >"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: This is an explanation with mixed spacing and newlines." in captured.out


def test_multiple_chunks(capsys):
    chunks = [
        "< response >",
        "  < expl",
        "anation >",
        "This is an explanation ",
        "split across multiple chunks.",
        "  < /explanation >",
        "</ response >"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: This is an explanation split across multiple chunks." in captured.out


def test_multiple_explanations(capsys):
    chunks = [
        "<response>",
        "<explanation>First explanation.</explanation>",
        "<other_tag>Some other content.</other_tag>",
        "<explanation>Second explanation.</explanation>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: First explanation." in captured.out
    assert "Explanation: Second explanation." in captured.out


def test_explanation_and_shell_command(capsys):
    chunks = [
        "<response >",
        "  <explanation ",
        ">A brief explanation of the steps, if necessary</explanation>",
        "  <steps",
        ">",
        "    <step>",
        "      <type>shell</type>",
        "      <command>npm run dev</command>",
        "    </step>",
        "</steps>",
        "</response >"
    ]
    print("Debug: Starting test_explanation_and_shell_command")
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    print(f"Debug: Captured output: {captured.out}")
    assert "Explanation: A brief explanation of the steps, if necessary" in captured.out
    assert "Shell Command: npm run dev" in captured.out
    print("Debug: test_explanation_and_shell_command completed")


def test_file_operation_and_cdata(capsys):
    chunks = [
        "<response >",
        "<explanation ",
        "> This is an explanation of file operation.</explanation>",
        "<steps>",
        "<step>",
        "      <type>file</type>",
        "      <operation>UPDATE</operation>",
        "      <filename>path/to/existing/file.ext</filename>",
        "      <content>",
        "        <![CDATA[",
        "          <html> <body>This is the content of the file</body> </html>",
        "        ]]>",
        "      </content>",
        "    </step>",
        "</steps>",
        "</response>"
    ]
    print("Debug: Starting test_file_operation_and_cdata")
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    print(f"Debug: Captured output: {captured.out}")
    assert "Explanation: This is an explanation of file operation." in captured.out
    assert "File Operation: UPDATE path/to/existing/file.ext" in captured.out
    assert "<html> <body>This is the content of the file</body> </html>" in captured.out
    print("Debug: test_file_operation_and_cdata completed")


def test_multiple_shell_commands(capsys):
    chunks = [
        "<response>",
        "<explanation>Multiple commands example</explanation>",
        "<steps>",
        "<step><type>shell</type><command>npm install</command></step>",
        "<step><type>shell</type><command>npm run build</command></step>",
        "<step><type>shell</type><command>npm run start</command></step>",
        "</steps>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: Multiple commands example" in captured.out
    assert "Shell Command: npm install" in captured.out
    assert "Shell Command: npm run build" in captured.out
    assert "Shell Command: npm run start" in captured.out


def test_mixed_content(capsys):
    chunks = [
        "<response>",
        "<explanation>Mixed content example</explanation>",
        "<steps>",
        "<step><type>file</type><operation>CREATE</operation><filename>example.txt</filename></step>",
        "<step><type>shell</type><command>echo 'Hello' > example.txt</command></step>",
        "</steps>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: Mixed content example" in captured.out
    assert "Shell Command: echo 'Hello' > example.txt" in captured.out


def test_multiple_file_operations(capsys):
    chunks = [
        "<response>",
        "<explanation>Multiple file operations</explanation>",
        "<steps>",
        "<step><type>file</type><operation>CREATE</operation><filename>file1.txt</filename><content><![CDATA[Content 1]]></content></step>",
        "<step><type>file</type><operation>UPDATE</operation><filename>file2.txt</filename><content><![CDATA[Content 2]]></content></step>",
        "</steps>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: Multiple file operations" in captured.out
    assert "File Operation: CREATE file1.txt" in captured.out
    assert "File Operation: UPDATE file2.txt" in captured.out
    assert "Content 1" in captured.out
    assert "Content 2" in captured.out


def test_mixed_operations(capsys):
    chunks = [
        "<response>",
        "<explanation>Mixed operations</explanation>",
        "<steps>",
        "<step><type>file</type><operation>CREATE</operation><filename>file.txt</filename><content><![CDATA[File content]]></content></step>",
        "<step><type>shell</type><command>echo 'Hello'</command></step>",
        "</steps>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: Mixed operations" in captured.out
    assert "File Operation: CREATE file.txt" in captured.out
    assert "File content" in captured.out
    assert "Shell Command: echo 'Hello'" in captured.out


def test_cdata_with_xml_content(capsys):
    chunks = [
        "<response>",
        "<explanation>CDATA with XML-like content</explanation>",
        "<steps>",
        "<step><type>file</type><operation>CREATE</operation><filename>config.xml</filename>",
        "<content><![CDATA[",
        "<config>",
        "  <setting>value</setting>",
        "  <nested>",
        "    <element>text</element>",
        "  </nested>",
        "</config>",
        "]]></content></step>",
        "</steps>",
        "</response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Explanation: CDATA with XML-like content" in captured.out
    assert "File Operation: CREATE config.xml" in captured.out
    assert "<config>" in captured.out
    assert "<setting>value</setting>" in captured.out
    assert "<nested>" in captured.out
    assert "<element>text</element>" in captured.out
    assert "</config>" in captured.out


def test_large_cdata_content(capsys):
    chunks = [
        "<response><steps><step><type>file</type><operation>CREATE</operation><filename>large_file.txt</filename><content><![CDATA[",
        "This is the start of a large file content.\n",
        "This is the middle of the file content.\n" * 100,  # Simulate a large file
        "This is the end of the file content.",
        "]]></content></step></steps></response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "File Operation: CREATE large_file.txt" in captured.out
    assert "File Content:" in captured.out
    assert "This is the start of a large file content." in captured.out
    assert "This is the middle of the file content." in captured.out
    assert "This is the end of the file content." in captured.out


def test_split_step(capsys):
    chunks = [
        "<response><steps><st",
        "ep><type>shell</type><comm",
        "and>echo 'Hello'</command></step></steps></response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "Shell Command: echo 'Hello'" in captured.out


def test_split_cdata(capsys):
    chunks = [
        "<response><steps><step><type>file</type><operation>CREATE</operation><filename>test.txt</filename><content><![CDATA[This is ",
        "a test file ",
        "with multiple lines]]></content></step></steps></response>"
    ]
    stream_and_print_commands(chunks)
    captured = capsys.readouterr()
    assert "File Operation: CREATE test.txt" in captured.out
    assert "This is a test file with multiple lines" in captured.out
