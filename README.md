# Dravid (DRD) - AI-Powered CLI Coding Framework

![PyPI](https://img.shields.io/pypi/v/dravid.svg)
![Build Status](https://github.com/vysakh0/dravid/actions/workflows/main.yml/badge.svg)
![Coverage Status](https://codecov.io/gh/vysakh0/dravid/branch/main/graph/badge.svg)
![License](https://img.shields.io/github/license/vysakh0/dravid.svg)

Dravid (DRD) is an advanced, AI-powered CLI coding framework (in alpha) designed to follow user instructions until the job is done, even if it means fixing errors, including installation issues. It can also listen to a live dev server or a test server (in watch mode) or any processes with interactive pair programming. It can generate code and fix errors autonomously until the intended result is achieved.


## Installation

### Prerequisites

- Python 3.7+
- pip (Python package installer)
- API key for your chosen AI provider (environment variable should be set). Please see the LLM providers section. Supports AI providers: Claude (default), OpenAI, Azure OpenAI, Llama 3, Mixtral (through Anyscale, Groq, or NVIDIA), and local LLM models through Ollama.


To install Dravid, run the following command:

```
pip install dravid
```

To upgrade for latest fixes:

```
pip install --upgrade dravid
```


## Usage

After installation, you can use the `drd` command directly from your terminal. Here are some common usage examples:

NOTE: for better results, go step by step and communicate clearly. You can also define project_guidelines.txt
which will be referenced in the main query, you can use this to instruct on how the code should be generated etc.

Also, any png or jpg files that will be generated and needs to be replaced will have placeholder prefix, so you
know that it has to be replaced.

## Turbo dev mode

You can run the development server with automatic error fixing.

This command will start your dev server or test server and then continually fix any errors
and then restart, you can sitback and sip coffee :)
You can give instructions into this mode, it will generate code, fix any errors, restart.
You can also provide image for reference, or any number of files for references.

```
drd "rails server"
```

```
drd "npm run test:watch"
```

## The bootstrap mode

- When you want to create a fresh project

```
drd --do "create a nextjs project"
```

- When you to quickly fix or change something in a project without starting a dev or test server.

```
drd --do "make the walls permeable in the snake_game file"
```

#### With larger text (multi line string)

When you have larger string or if you want to copy paste a error stack with double quotes etc, please use this.

```
drd --do """
Fix this error:
....
"""
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
drd --do "make the home image similar to the image" --image "~/Downloads/reference.png"
```


### Security and Sandbox (important note)

- Always try in a new directory for a fresh project.
- For existing projects, create a separate git branch or a sandbox environment. Monitor the generated commands. Git add or commit when you get results.
- Your file content will be sent to the your chosen LLM for response. Do not include sensitive files in the project.
- Don't use hardcoded API_KEYS. Use .env and ensure it's part of .gitignore so the tool can skip reading it.
- 
## AI Models and Providers

Dravid supports multiple AI providers and models to suit your needs. Here's an overview of the available options:

### Default: Claude (Anthropic)

By default, Dravid uses Claude 3.5 Sonnet from Anthropic. Claude is known for its strong performance across a wide range of tasks, including coding, analysis, and creative writing.

To use Claude, set the following environment variable:

```
CLAUDE_API_KEY=your_claude_api_key_here
```

### OpenAI

Dravid also supports OpenAI's models. When using OpenAI, the default model is gpt-4o.

To use OpenAI, set the following environment variables:

```
DRAVID_LLM=openai
OPENAI_API_KEY=your_openai_api_key_here
```

You can control the specific OpenAI model used by changing the `OPENAI_MODEL` environment variable.
For example:

```
OPENAI_MODEL=gpt-4 # for standard GPT-4
OPENAI_MODEL=gpt-3.5-turbo # for GPT-3.5 Turbo
```

## Other Providers

Depending on your chosen AI provider, you'll need to set different environment variables:

### Azure OpenAI

```
DRAVID_LLM=azure
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_API_VERSION=your_api_version_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
```

### Custom Provider compatible with OpenAI spec(e.g., Anyscale, Togeether, Groq, NVIDIA, or your own)

```
DRAVID_LLM=custom
DRAVID_LLM_API_KEY=your_custom_api_key_here
DRAVID_LLM_ENDPOINT=your_custom_endpoint_here
DRAVID_LLM_MODEL=your_preferred_model_here
```

### Ollama (for local LLM models)

```
DRAVID_LLM=ollama
DRAVID_LLM_MODEL=your_preferred_local_model_here
```

## Project Structure

- `src/drd/`: Main source code directory
  - `cli/`: Command-line interface modules
  - `api/`: API interaction
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

   For eg: if you use CLAUDE, if you use other services, you can add those env.

   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

4. You can use Dravid to add features or functionalities to the project. As this project uses drd.json
   and has used Dravid to build Dravid.

```
poetry run drd --do "refactor api_utils"
```

or

```
poetry run drd --do "add tests for utils/utils"
```

```
poetry run drd --ask "who are you"
```

## Testing

After adding some functionalities, if you want to test how it works, I suggest creating a directory
called `myapp` or `testapp` or `test-app` in the root of this project. These folder names are already in .gitignore.

```
cd myapp
poetry run drd --do "create a simple elixir project"
```

To run the test suite:

```
poetry run pytest
```

## Errors or Exception

### Installation

- Make sure you are installing with python 3.8 and above, please check your python version
  and pip version if you have both python2 and python3 in your system.
- If you get "SyntaxError: multiple exception types must be parenthesized" after installation
  and when you do `drd --version` it means the pygments library (dependency of openai) needs upgrade

```
pip install --upgrade pygments
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Contact

For questions, suggestions, or issues, please open an issue on the GitHub repository or contact the maintainers directly.

Happy coding with Dravid!
