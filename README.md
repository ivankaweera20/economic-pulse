# Economic Pulse

**Python-based exploration of U.S. macroeconomic indicators using the Federal Reserve Economic Data (FRED) API.**

> **Status:** Work in progress. This repository currently contains a standalone analysis script with Matplotlib visualizations, not a deployed Streamlit dashboard or a formal research paper.

## Overview

Economic Pulse retrieves public U.S. economic time series from FRED and uses pandas to calculate, compare, and visualize selected indicators. The goal is to practice reproducible data retrieval and explore how inflation, labor-market conditions, interest rates, and real GDP evolve over time.

## What the current script does

- Downloads monthly CPI (`CPIAUCSL`), unemployment (`UNRATE`), and effective federal funds rate (`FEDFUNDS`) observations.
- Downloads quarterly real GDP (`GDPC1`) observations.
- Calculates year-over-year CPI inflation (12-month percentage change) and real GDP growth (four-quarter percentage change).
- Computes summary statistics such as the count, mean, minimum, median, maximum, latest observation, and date.
- Creates Matplotlib charts of inflation versus unemployment and the level of real GDP.
- Retrieves quarterly average unemployment data using FRED's aggregation options.
- Compares two historical vintages of real GDP observations to explore data revisions.
- Performs basic validity checks for ascending dates, duplicate monthly dates, positive CPI, and plausible unemployment percentages.

These are descriptive analyses and data checks; the script does not establish causal relationships between economic variables.

## Requirements

- Python 3.10 or newer
- A free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
- Python packages listed in `requirements.txt`

## Run locally

1. Download or clone this repository.
2. In a terminal in the project folder, install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Set your FRED API key as an environment variable. **Do not paste a real key into the source code or commit it to GitHub.**

   **Windows PowerShell:**
   ```powershell
   $env:FRED_API_KEY = "your_key_here"
   python fred_tutorial.py
   ```

   **macOS / Linux:**
   ```bash
   export FRED_API_KEY="your_key_here"
   python fred_tutorial.py
   ```

4. The program downloads live FRED data, prints summary tables, displays two Matplotlib figures, and reports its validation checks.

**Note:** An internet connection and a valid FRED API key are required to execute the data-download steps. The script is not yet a Streamlit application.

## Data sources and units

| FRED series | Indicator | Typical frequency |
| --- | --- | --- |
| `CPIAUCSL` | Consumer Price Index for All Urban Consumers: All Items | Monthly |
| `UNRATE` | Civilian Unemployment Rate | Monthly |
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly |
| `GDPC1` | Real Gross Domestic Product | Quarterly |

Data are retrieved from [FRED at the Federal Reserve Bank of St. Louis](https://fred.stlouisfed.org/). Definitions, reporting units, and availability are determined by the source series; economic data can be revised over time.

## Next steps

- Add an interactive Streamlit interface with selectable date ranges and indicators.
- Add clearer automated tests and error handling for missing observations.
- Write documented research questions and analyses of the resulting figures, including the limitations of descriptive comparisons.

## Project background

An undergraduate personal project combining programming and interest in economics, financial markets, and applied data analysis.
