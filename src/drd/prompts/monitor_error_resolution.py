# File: prompts/error_resolution_prompt.py

def get_error_resolution_prompt(error_type, error_message, error_trace, line, project_context, file_context=None):
    return f"""
    # Error Context
    An error occurred while running the server:
    Error type: {error_type}
    Error message: {error_message}
    Error trace:
    {error_trace}
    Relevant output line:
    {line}
    Project context:
    {project_context}

    File context: {file_context}
    # Instructions for dravid: Error Resolution Assistant
    Analyze the error above and provide steps to fix it.
    This is being run in a monitoring thread, so don't suggest server starting commands like npm run dev.
    Make sure you dont try for drastic changes, just the needed and precise fix. 
    Your response should be in strictly XML format with no other extra messages. Use the following format:
    <response>
    <explanation>A brief explanation of the steps, if necessary</explanation>
    <steps>
        <step>
        <type>shell</type>
        <command>command to execute</command>
        </step>
        <step>
        <type>file</type>
        <operation>CREATE</operation>
        <filename>path/to/file.ext</filename>
        <content>
            <![CDATA[
            file content here
            ]]>
        </content>
        </step>
       <step>
        <type>file</type>
        <operation>UPDATE</operation>
        <filename>path/to/existing/file.ext</filename>
        <content>
          <![CDATA[
          Specify changes using the following format:
          + line_number: content to add
          - line_number: (to remove the line)
          r line_number: content to replace the line with
          
          Example:
          + 3: import new_module
          - 10:
          r 15: def updated_function():
          ]]>
        </content>
      </step>
        <type>file</type>
        <operation>DELETE</operation>
        <filename>path/to/file/to/delete.ext</filename>
        </step>
    </steps>
    </response>
    """
