# 🎓 University AI Report Generator

## 📋 Project Overview

This system automatically generates narrative reports in Indonesian from university data (students, grades, finance) using Google Gemini AI. Built as a demonstration of AI API integration with data processing capabilities.

### Key Features
- ✅ Read Excel files (students, grades, finance data)
- ✅ Generate Indonesian narrative reports using Gemini API
- ✅ Validate AI outputs for hallucinations
- ✅ Export as Markdown files with metadata
- ✅ Modular, beginner-friendly code structure
- ✅ Comprehensive documentation for thesis

---

## 🏗️ Project Structure

```
university-report-generator/
│
├── main.py                  # Main application (run this!)
├── config.py                # Configuration & API key management
├── data_processor.py        # Excel reading & data analysis
├── report_generator.py      # Gemini AI integration
├── output_manager.py        # Markdown file export
│
├── requirements.txt         # Python dependencies
├── .env.example            # API key template (copy to .env)
├── README.md               # This file
│
├── data/                   # Place your Excel files here
│   ├── sample_students.xlsx
│   └── sample_finance.xlsx
│
└── reports/                # Generated reports (auto-created)
    ├── student_reports/
    ├── finance_reports/
    └── metadata/
```

---

## 🚀 Installation Guide

### Step 1: Install Python
1. Download Python 3.10 or newer from [python.org](https://www.python.org/downloads/)
2. **Important**: During installation, check "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Set Up Project
1. Create a project folder:
   ```bash
   mkdir university-report-generator
   cd university-report-generator
   ```

2. Create all the Python files (copy code from artifacts)

3. Create virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

4. Activate virtual environment:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `pandas` - Excel file reading
- `openpyxl` - Excel format support
- `numpy` - Data calculations
- `google-generativeai` - Gemini AI API
- `python-dotenv` - Environment variable loading

### Step 4: Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy your API key

### Step 5: Configure API Key
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # macOS/Linux
   ```

2. Open `.env` and add your API key:
   ```
   GEMINI_API_KEY=AIzaSyC1234567890abcdefGHIJKLMNOPQRSTUVWX
   ```

---

## 📊 Preparing Sample Data

### Student Data Example (sample_students.xlsx)

Create an Excel file with columns like:
| NIM | Nama | Nilai | IPK | Semester |
|-----|------|-------|-----|----------|
| 2101001 | Budi Santoso | 85 | 3.5 | 5 |
| 2101002 | Siti Aminah | 92 | 3.8 | 5 |
| 2101003 | Ahmad Fauzi | 78 | 3.2 | 5 |

### Finance Data Example (sample_finance.xlsx)

| Kategori | Pemasukan | Pengeluaran | Bulan |
|----------|-----------|-------------|-------|
| SPP | 150000000 | 0 | Januari |
| Operasional | 0 | 50000000 | Januari |
| Penelitian | 30000000 | 20000000 | Januari |

Save these files in the `data/` folder.

---

## ▶️ Running the Application

### Basic Usage
```bash
python main.py
```

You'll see a menu:
```
Select an option:
1. Generate Student Performance Report
2. Generate Financial Analysis Report
3. Run Demo (process all sample files)
4. Exit
```

### Demo Mode (Recommended for First Run)
1. Choose option `3` (Run Demo)
2. System will process all files in `data/` folder
3. Reports saved to `reports/` folder

### Processing Specific Files
1. Choose option `1` or `2`
2. Enter full path to your Excel file
3. Wait for processing
4. Check `reports/` for output

---

## 🔍 Understanding the Code

### Module Breakdown

#### 1. **main.py** - Application Orchestrator
- Coordinates all components
- Handles user interface (CLI menu)
- Manages the workflow: Read → Analyze → Generate → Save

**Key Functions**:
- `generate_student_report()` - Process student data
- `generate_finance_report()` - Process financial data
- `run_demo()` - Demo mode for presentations

#### 2. **config.py** - Configuration Manager
- Loads API key securely
- Manages application settings
- Reads from `.env` file

**Key Functions**:
- `get_api_key()` - Retrieves Gemini API key
- `get_setting()` - Gets configuration values

#### 3. **data_processor.py** - Data Handler
- Reads Excel files with pandas
- Calculates statistics (mean, median, std dev)
- Detects data type (student/finance)
- Creates summaries for AI

**Key Functions**:
- `read_excel()` - Load Excel into DataFrame
- `analyze_data()` - Calculate all statistics
- `get_data_summary_for_ai()` - Create text summary

#### 4. **report_generator.py** - AI Integration
- Connects to Gemini API
- Sends prompts to generate reports
- Validates for hallucinations
- Handles errors and retries

**Key Functions**:
- `generate_report()` - Call Gemini to create report
- `validate_report()` - Check for fake data
- `_create_prompt()` - Build AI prompt

#### 5. **output_manager.py** - File Management
- Saves reports as Markdown
- Adds metadata headers
- Organizes files by type
- Creates directory structure

**Key Functions**:
- `save_report()` - Write Markdown file
- `list_reports()` - Show all generated reports

---

## 🎯 For Your Thesis Presentation

### Explaining to Your Advisor

**System Flow**:
1. **Input**: User provides Excel file
2. **Processing**: System reads data and calculates statistics
3. **AI Generation**: Gemini creates narrative report in Indonesian
4. **Validation**: Check for hallucinations/fake data
5. **Output**: Save as Markdown with metadata

**Key Technical Concepts**:
- **API Integration**: How your code calls external services (Gemini)
- **Data Processing**: Statistical analysis with pandas
- **Prompt Engineering**: Crafting good AI instructions
- **Validation**: Preventing AI hallucinations
- **Modular Design**: Each file has one clear purpose

### Demo Script
1. Show the project structure
2. Explain each module briefly
3. Run demo mode: `python main.py` → option 3
4. Show input Excel files
5. Show generated Markdown reports
6. Explain validation process

---

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "API key not found"
- Check `.env` file exists
- Verify API key is correct
- No spaces around `=` in `.env`

### "FileNotFoundError"
- Create `data/` folder
- Place Excel files inside
- Check file path is correct

### "Excel file error"
- Verify file is `.xlsx` or `.xls`
- Check file isn't corrupted
- Ensure file isn't open in Excel

### "API call failed"
- Check internet connection
- Verify API key is valid
- Check Gemini API quota

---

## 📈 Future Enhancements

Ideas for extending this project:
- [ ] Add web interface (Flask/FastAPI)
- [ ] Database integration (PostgreSQL/MySQL)
- [ ] User authentication
- [ ] Multiple report templates
- [ ] PDF export option
- [ ] Email delivery
- [ ] Batch processing
- [ ] Dashboard with charts

---

## 📚 Dependencies Explained

| Package | Purpose | Thesis Relevance |
|---------|---------|------------------|
| pandas | Data manipulation | Core data processing |
| openpyxl | Excel file support | Input data handling |
| numpy | Numerical operations | Statistical calculations |
| google-generativeai | Gemini AI API | AI integration demo |
| python-dotenv | Environment variables | Security best practice |

---

## 🎓 Academic Notes

### Research Questions Addressed:
1. How can AI assist in automated report generation?
2. What techniques prevent AI hallucinations?
3. How to integrate external AI APIs effectively?

### Methodology:
- **Quantitative**: Statistical analysis of data
- **Qualitative**: Narrative report generation
- **Validation**: Hallucination detection algorithms

### Technologies Used:
- **Language**: Python 3.10+
- **AI Model**: Google Gemini Pro
- **Data Processing**: pandas, numpy
- **File Format**: Markdown (human-readable)

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review code comments
3. Test each module independently
4. Check Gemini API documentation

---

## 📄 License

This project is for educational/thesis purposes.  
Created by [Your Name] - [Year]

---


**Good luck with your thesis! 🎉**
