### Financial Research Report Generator

## This project extracts structured financial information from company research reports / investor presentations using an LLM and generates analyst-style PDF reports.

## Tech Stack
# Backend
- Python
- FastAPI
- Google Gemini
- ReportLab
- Matplotlib
# Frontend
- Next.js
- Tailwind

## Features
- Extracts company information from PDF documents
- Extracts financial metrics, highlights, outlook, strengths and risks
- Generates a multi-page equity research style PDF report
- Supports both annual and quarterly financial data
  

## Template Fields

The extraction schema and report fields are defined in the prompt used for Gemini.

## Key fields include:

- Company Information
- Rating
- Highlights
- Outlook
- Financials
- Quarterly Financials
- Shareholding
- Strengths
- Risks

The PDF layout and rendering logic are defined in:

- pdf_generator.py

## How to run:
# Backend
- Create a virtual environment and install dependencies:
- pip install -r requirements.txt
- Create a .env file:
- GOOGLE_API_KEY=your_api_key

# Frontend
- npm install
-  
## Start the application:
# Backend
python -m uvicorn app.main:app --reload
The API will be available at:
http://localhost:8000

# Frontend
- npm run dev
  
## Sample generated reports are included:
- ICICI Bank 
- JSW Energy
