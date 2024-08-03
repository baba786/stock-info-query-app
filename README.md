# Stock Info Query App

## Description

The Stock Info Query App is a Python-based application that allows users to query stock information using natural language. It leverages the AngelOne API for real-time stock data and uses LangChain for natural language processing.

## Features

- Natural language processing for stock queries
- Real-time stock data fetching from AngelOne API
- Historical data retrieval and analysis
- User-friendly command-line interface

## Installation

1. Clone the repository:git clone https://github.com/baba786/stock-info-query-app.git
cd stock-info-query-app

2. Create a virtual environment:python -m venv venv
source venv/bin/activate

3. Install the required packages: pip install -r requirements_dev.txt

4. 4. Set up your environment variables:
- Copy `.env.example` to `.env`
- Fill in your AngelOne API credentials and OpenAI API key in the `.env` file

5. Set up your AngelOne API key:
- Copy `key.txt.example` to `key.txt`
- Fill in your AngelOne API credentials in the `key.txt` file

## Usage

Run the main application script:python app.py

Follow the prompts to enter your stock queries in natural language.

## Configuration

- `key.txt`: Contains AngelOne API credentials
- `.env`: Contains environment variables including OpenAI API key

Make sure to keep these files secure and never commit them to version control.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
