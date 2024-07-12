# Dravid (DRD) - AI-Powered CLI Coding Framework

Dravid (DRD) is an advanced, AI-powered CLI coding framework designed to streamline and enhance the development process. It leverages artificial intelligence to assist developers in various tasks, from project setup to code generation and file management.

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

## Usage

After installation, you can use the `drd` command directly from your terminal. Here are some common usage examples:

### Basic Query

Execute a Dravid command:

```
drd "create a nextjs project"
```

The above command loads project context or project guidelines (you can create your own project_guidelines.txt) if they exist, along with any relevant file content in its context.

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

### Development Server with Monitoring

Run the development server with automatic error fixing:

```
drd --monitor-init
```

### Metadata Management

Initialize metadata for an existing project:

```
drd --meta-init
```

Update metadata after modifying files:

```
drd --meta-add "modified the about page"
```

### File-specific Queries

Ask for suggestions on specific files:

```
drd --ask "can you suggest how to refactor this file" --file "src/main.py"
```

For more detailed usage instructions and options, use the help command:

```
drd --help
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

## Testing

After adding some functionalities, if you want to test how it works, I suggest creating a directory
called `myapp` or `testapp` or `test-app` in the root of this project. These folder names are already in .gitignore.

```
cd myapp
poetry run drd "create a simple elixir project"
```

To run the test suite:

```
poetry run test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to the creators of the Claude AI model, which powers many of Dravid's capabilities

## Contact

For questions, suggestions, or issues, please open an issue on the GitHub repository or contact the maintainers directly.

Happy coding with Dravid!
