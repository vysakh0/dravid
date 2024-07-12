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

## Usage

To start using Dravid, activate the Poetry environment and run the main script:

```
poetry shell
python src/drd/main.py
```

### Basic Commands

- `dravid query "Your query here"`: Execute a Dravid command
- `dravid monitor`: Start the development server with file monitoring
- `dravid init`: Initialize project metadata

For more detailed usage instructions, refer to the in-app help:

```
python src/drd/main.py --help
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

## Testing

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
