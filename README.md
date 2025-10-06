1. Project Overview

This project demonstrates an AI-powered narrative report generation system. It takes structured university data (students, grades, financial records) and produces Indonesian-language reports via Google Gemini (GenAI). The goal is to showcase integration of AI APIs into a data analytics pipeline, with validation to mitigate hallucinations.

Objectives

Automate report writing from raw data

Maintain factual consistency and reduce hallucinations

Produce human-readable output (Markdown)

Structure code in modular, understandable components

Serve as a technical artifact for demonstration in your thesis

2. Features

Excel Data Input: Load student, grade, and finance data from .xlsx files

AI Narrative Generation: Use Gemini to create narrative reports in Indonesian

Validation Layer: Heuristic checks for inconsistencies or invented claims

Markdown Output: Reports are exported as Markdown files, with metadata

Offline Fallback: If the AI fails, a fallback report template is generated

Modular Design: Clear separation between data, AI, validation, export

3. Project Structure
university-ai-report-generator/
│
├── main.py                   # Entry point / CLI orchestration
├── config.py                 # API key / environment loading & configurations
├── data_processor.py         # Read Excel, compute summaries
├── report_generator.py       # AI prompt construction & Gemini integration
├── validator.py              # Checking the generated text against data
├── exporter.py               # Markdown composition & file writing
│
├── requirements.txt          # Python dependencies
├── .env.example               # Template for environment variables
├── README.md                  # Project documentation
│
├── data/                      # Input data files (Excel)
│   ├── students.xlsx
│   ├── grades.xlsx
│   └── finance.xlsx
│
└── reports/                   # Generated output (Markdown)
    ├── report_YYYYMMDD_HHMMSS.md

4. Setup & Installation
4.1 Prerequisites

Python 3.10 or newer

Internet access (for calling Gemini API)

A valid Gemini (Generative Language) API key

4.2 Create and Activate Virtual Environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

4.3 Install Dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

4.4 Configure API Key

Copy .env.example → .env

Edit .env and set:

GEMINI_API_KEY=YOUR_API_KEY_HERE
# Optionally:
GEMINI_API_URL= (leave blank to use default model endpoint)

5. Usage
5.1 Generate Dummy Data (for demo)
python main.py --generate-data


This creates sample Excel files in the data/ folder.

5.2 Run the Full Pipeline
python main.py --run


By default, it will call the AI (if API key is set) and export a report in reports/.

To run in offline mode (no API call), use:

python main.py --run --no-api

6. Module Explanations (for Thesis Defense)
main.py

Parses command-line flags (--generate-data, --run, --no-api)

Coordinates the pipeline: data generation, ETL → AI → validation → export

Loads environment variables (via dotenv)

config.py

Reads environment variables

Provides functions like get_api_key() or get_setting()

Central point of configuration to avoid scattering secrets

data_processor.py

Reads .xlsx files using pandas and openpyxl

Computes statistical summaries: counts, averages, distributions

Produces structured summaries for prompt insertion

report_generator.py

Constructs prompts (in Indonesian) embedding facts from data

Calls Gemini (via the GenAI SDK) with retry logic

Parses response to extract the generated text

Provides fallback if the API fails

validator.py

Parses numbers and keywords from the narrative

Compares extracted numbers to the data summary

Flags obvious disparities, missing data, or too-short output

exporter.py

Assembles narrative + facts + validation messages into Markdown format

Saves file to reports/ with timestamped filename

Ensures directory creation and error handling

7. Sample Data Format & Example
Students / Grades Excel
StudentID	Name	Department	Grade
2101001	Budi	TI	3.45
2101002	Siti	Manajemen	3.72
Finance Excel
Year	TuitionIncome	OperationalExpense
2024	1,200,000,000	950,000,000

These tables feed into summary dicts used to generate narrative.

8. Academic & Technical Context

Research Goals: Demonstrate how AI can assist academic reporting, and how to mitigate hallucinations

Challenges Addressed:

Connecting structured data and free-form narrative

Preventing AI from inventing facts

Handling API failures gracefully

Limitations:

Validation is heuristic, not perfect

The system is not fully autonomous

Does not learn or adapt over time

9. Roadmap & Future Work

Add a web interface (Flask / FastAPI)

Store data in a real database (PostgreSQL, MySQL)

Introduce user authentication / role-based access

Extend validation using embeddings, entailment models

Export to PDF, offer email delivery

Batch processing & scheduler

10. Troubleshooting & FAQ
Problem	Solution
ModuleNotFoundError	Ensure you installed dependencies in the correct venv
“API key not set”	Confirm .env exists and contains GEMINI_API_KEY
FileNotFoundError	Create data/ folder or correct paths
API call fails	Check internet connectivity, key validity, quota
11. Dependencies
pandas
openpyxl
numpy
google-genai
python-dotenv
requests


Line up with your requirements.txt.

12. License & Acknowledgement

This project is intended for academic / educational use within your thesis.
Feel free to include a license (e.g. MIT) if you plan to publish it publicly.
