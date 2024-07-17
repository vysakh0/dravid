# Dravid (DRD) - AI-Powered CLI Coding Framework

![PyPI](https://img.shields.io/pypi/v/dravid.svg)
![Build Status](https://github.com/vysakh0/dravid/actions/workflows/main.yml/badge.svg)
![Coverage Status](https://codecov.io/gh/vysakh0/dravid/branch/main/graph/badge.svg)
![License](https://img.shields.io/github/license/vysakh0/dravid.svg)

Dravid (DRD) is an advanced, AI-powered CLI coding framework (in alpha) designed to follow user instructions until the job is done, even if it means fixing errors, including installation issues. It can generate code and fix errors autonomously until the intended result is achieved.

### Security and Sandbox (important note)

- Always try in a new directory for a fresh project.
- For existing projects, create a separate git branch or a sandbox environment. Monitor the generated commands. Git add or commit when you get results.
- Your file content will be sent to the CLAUDE API LLM for response. Do not include sensitive files in the project.
- Don't use hardcoded API_KEYS. Use .env and ensure it's part of .gitignore so the tool can skip reading it.
- Please use version 0.8.0 or higher. You can check the version with drd --version.
- If possible try in a docker instance.

### Quick preview:

1.  As shown in the video, when initializing a project where system dependencies don't exist, Dravid will attempt to fix them one by one, even if those fixes result in their own errors

https://github.com/user-attachments/assets/07784a9e-8de6-4161-9e83-8cad1fa04ae6

2. If you have a dev server with import or reference errors, requiring dependency installation or fixes, Dravid will monitor your dev or test server and autofix. This is particularly useful for existing projects where you want to fix tests or refactor the entire project.

https://github.com/user-attachments/assets/14350e4d-6cec-4922-997f-f34e9f716189

You can also initialize Dravid in your existing project. See the Usage section for more details.

## Features

- AI-powered CLI for efficient coding and project management
- Image query handling capabilities
- Robust file operations and metadata management
- Integration with external APIs (Dravid API)
- Built-in development server with file monitoring
- Comprehensive error handling and reporting
- Extensible architecture for easy feature additions

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package installer)
- CLAUDE_API_KEY (environment variable should be set)

To install Dravid, run the following command:

```
pip install dravid
```

To upgrade for latest fixes

```
pip install --upgrade dravid
```

### NOTE:

Always create a fresh directory before trying to create a new project.

## Usage

After installation, you can use the `drd` command directly from your terminal. Here are some common usage examples:

NOTE: for better results, go step by step and communicate clearly. You can also define project_guidelines.txt
which will be referenced in the main query, you can use this to instruct on how the code should be generated etc.

Also, any png or jpg files that will be generated and needs to be replaced will have placeholder prefix, so you
know that it has to be replaced.

### Basic Query

Execute a Dravid command:

```
drd "create a nextjs project"
```

The above command loads project context or project guidelines if they exist, along with any relevant file content in its context.

#### With larger text (heredoc)

When you have larger string or if you want to copy paste a error stack with double quotes etc, please use this.

```
drd <<EOF
Fix this error:
....
EOF
```

### Ask Questions or Generate Content

Ask questions or generate content:

```
drd --ask "how is the weather"
```

Generate a file directly:

```
drd --ask "create a MIT LICENSE file, just the file, don't respond with anything else" >> LICENSE
```

--ask is much faster than the execute command because it doesn't load project context or project guidelines (you can create your own project_guidelines.txt)

### Image-based Queries

Use image references in your queries:

```
drd "make the home image similar to the image" --image "~/Downloads/reference.png"
```

### Self healing fix

You can run the development server with automatic error fixing.

This command will start your dev server (as in the drd.json) and then continually fix any errors
and then restart, you can sitback and sip coffee :)

```
drd --hf
```

or

```
drd --hot-fix
```

#### Test server monitoring and continous fix

You can also pass custom cmd options to `--hf` then it will pick that command over the dev server command.
This useful especially if you have test runners.

If you have 100 test cases, and 10 of the file, you can set this command to identify errors and automatically fix

```
drd --hf --cmd "npm run test:watch"
```

or

```
drd --hf --command "poetry run test:watch"
```

It would work with any languages or frameworks, make sure that the command is a continually running one not the usual
test script which exits out after tests passes or fails.

### Metadata Management

To use Dravid cli in an existing project you would have to initialize metadata (drd.json)

This script will ignore files in your .gitgnore and recursively read and give description for each of the file

```
drd --meta-init
```

or

```
drd --i
```

Note: make sure to include as many things in .gitignore that are not relevant. This would make multiple LLM calls.

When you have added some files or removed files on your own for some reason and you want Dravid to know about it,
you have to run this:

```
drd --meta-add "modified the about page"
```

or

```
drd --a "added users api"
```

This would update the drd.json

### File-specific Queries

Ask for suggestions on specific files:

```
drd --ask "can you suggest how to refactor this file" --file "src/main.py"
```

For more detailed usage instructions and options, use the help command:

```
drd --help
```

## Use Cases

### Next.js Project Development

1. Create a simple Next.js app:

   ```
   drd "create a simple nextjs app"
   ```

2. Include shadcn components:

   ```
   drd "include shadcn components like button, input, select etc"
   ```

3. Modify home page based on a reference image:

   ```
   drd "make the home page similar to the image" --image ~/Downloads/reference.png
   ```

4. Create additional pages with consistent layout:

   ```
   drd "whatever links like Company, About, Services etc that you see in Nav link you can convert them into links and page on its own and with some sample content. All these new pages should have the same layout as the home page"
   ```

5. Auto-fix errors and start development server:
   ```
   drd --hf
   ```

### Working with Existing Projects

Initialize Dravid in an existing project:

```
drd --i
```

This creates a drd.json based on the existing folder structure, allowing you to start using Dravid in that project.

### Exploring New Languages (e.g., Elixir)

1. Create a simple Elixir project (even if Elixir is not installed):

   ```
   drd "create a simple elixir project"
   ```

   Dravid will auto-fix any errors, including installing necessary dependencies.

2. Handle specific errors:
   ```
   drd <<EOF
   Your error trace in "file"
   EOF
   ```

### Ruby on Rails Project Development

1. Create a new Rails project:

   ```
   drd "create a new Ruby on Rails project with PostgreSQL database"
   ```

2. Generate a scaffold for a resource:

   ```
   drd "generate a scaffold for a Blog model with title and content fields"
   ```

3. Set up authentication:

   ```
   drd "add Devise gem for user authentication"
   ```

4. Create a custom controller and views:

   ```
   drd "create a controller for static pages with home, about, and contact actions, including corresponding views"
   ```

5. Implement a feature based on an image:

   ```
   drd "implement a comment section for blog posts similar to the image" --image ~/Downloads/comment_section.png
   ```

6. Run migrations and start the server:

   ```
   drd "run database migrations and start the Rails server"
   ```

7. Auto-fix any errors:
   ```
   drd --hf
   ```

### Python Project Development

1. Set up a new Python project with virtual environment:

   ```
   drd "create a new Python project with poetry for dependency management"
   ```

2. Create a simple Flask web application:

   ```
   drd "create a basic Flask web application with a home route and a simple API endpoint"
   ```

3. Add database integration:

   ```
   drd "add SQLAlchemy ORM to the Flask app and create a User model"
   ```

4. Implement user authentication:

   ```
   drd "implement JWT-based authentication for the Flask API"
   ```

5. Create a data processing script:

   ```
   drd "create a Python script that processes CSV files using pandas and generates a summary report"
   ```

6. Add unit tests:

   ```
   drd "add pytest-based unit tests for the existing functions in the project"
   ```

7. Generate project documentation:

   ```
   drd "generate Sphinx documentation for the project, including docstrings for all functions and classes"
   ```

8. Auto-fix any errors or missing dependencies:
   ```
   drd --hf
   ```

## Project Structure

- `src/drd/`: Main source code directory
  - `cli/`: Command-line interface modules
  - `api/`: API interaction and parsing modules
  - `utils/`: Utility functions and helpers
  - `prompts/`: AI prompt templates
  - `metadata/`: Project metadata management
- `tests/`: Test suite for the project

## Contributing

We welcome contributions to Dravid! Please see our [Contributing Guide](CONTRIBUTING.md) for more details on how to get started.

## Development

To install Dravid, you need Python 3.7+ and Poetry. Follow these steps:

1. Clone the repository:

   ```
   git clone https://github.com/vysakh0/dravid.git
   cd dravid
   ```

2. Install dependencies using Poetry:

   ```
   poetry install
   ```

3. Set up environment variables:
   Create a `.env` file in the project root and add your API keys:

   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

4. You can use Dravid to add features or functionalities to the project. As this project uses drd.json
   and has used Dravid to build Dravid.

```
poetry run drd "refactor api_utils"
```

or

```
poetry run drd "add tests for utils/utils"
```

```
poetry run drd --ask "who are you"
```

### Video examples

https://github.com/user-attachments/assets/2bcd2969-2746-4115-a879-18b8333a3053

https://github.com/user-attachments/assets/15112577-0d45-44be-b564-74bee548ac66

https://github.com/user-attachments/assets/25b82c1f-e357-405b-9b85-2488a2d2b771

## Testing

After adding some functionalities, if you want to test how it works, I suggest creating a directory
called `myapp` or `testapp` or `test-app` in the root of this project. These folder names are already in .gitignore.

```
cd myapp
poetry run drd "create a simple elixir project"
```

To run the test suite:

```
poetry run pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to the creators of the Claude AI model, which powers many of Dravid's capabilities

## Contact

For questions, suggestions, or issues, please open an issue on the GitHub repository or contact the maintainers directly.

Happy coding with Dravid!
