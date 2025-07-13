# Mutual Fund Plan Generator

## Overview

The **Mutual Fund Plan Generator** is a web application that helps users understand and project the potential growth of a mutual fund portfolio. It leverages historical stock market data to identify a diversified set of stocks with a balance of high Return on Investment (ROI) and low volatility (risk). The application then calculates a weighted average ROI for this selected portfolio and allows users to visualize the future value of their monthly investments (Systematic Investment Plan - SIP) over various time horizons.

This project demonstrates a practical application of data analysis, financial modeling, and web development to create an insightful tool for long-term investment planning.

## Features

* **Automated Stock Analysis:** Processes historical stock data to calculate key metrics like daily returns, volatility, and total ROI for multiple companies.

* **Intelligent Stock Selection:** Identifies a portfolio of stocks that exhibit both high ROI and low volatility based on predefined thresholds (median values).

* **Risk-Adjusted Allocation:** Calculates investment ratios for selected stocks using an inverse volatility weighting, allocating more to less volatile assets.

* **Portfolio Weighted ROI:** Computes the overall expected return for the generated mutual fund portfolio.

* **Interactive Future Value Projection (SIP Calculator):** Allows users to input a monthly investment amount (minimum ₹1000) and instantly visualize the compounded growth over 1, 3, 5, 10, 15, 20, 25, and 30 years.

* **Dynamic Content Display:** The mutual fund plan summary (ROI, volatility, selected companies) and investment projections are only displayed *after* the user provides valid input and clicks the "Calculate Future Value" button.

* **Improved User Feedback:** Input validation errors are displayed directly on the page in red text, providing a smoother user experience than traditional alerts.

* **Interactive Visualizations:** Uses Plotly.js to display stock price trends and future value projections in an intuitive and interactive manner.

* **Responsive Design:** Optimized for viewing on various devices (desktop, tablet, mobile).

## How the Mutual Fund Plan is Calculated

The core of this application lies in its data analysis pipeline, implemented in the Flask backend (`app.py`). Here's a step-by-step breakdown of how the mutual fund plan is generated:

1. **Data Loading and Preprocessing:**

   * The application loads historical closing prices for Nifty 50 companies from `nifty50_closing_prices.csv`.

   * The 'Date' column is converted to datetime objects.

   * All stock price columns are explicitly converted to numeric types, coercing any non-numeric entries into `NaN` (Not a Number).

   * Missing values (`NaN`s) are handled robustly by first applying `ffill()` (forward-fill) to propagate the last valid observation forward, followed by `bfill()` (backward-fill) to fill any leading `NaN`s.

   * Any columns that remain entirely `NaN` after these filling operations (e.g., if a stock had no valid data) are dropped from the dataset.

2. **Daily Returns Calculation:**

   * For each stock, the daily percentage change in closing prices is calculated. This is a fundamental step for assessing short-term performance and volatility.

3. **Volatility (Risk) Calculation:**

   * Volatility is measured as the standard deviation of the daily percentage returns for each stock. A higher standard deviation indicates greater price fluctuations and thus higher risk.

4. **Total Return on Investment (ROI) Calculation:**

   * The overall ROI for each stock is calculated from its first recorded closing price to its last. This provides a long-term performance metric.

5. **Stock Selection Criteria (High ROI, Low Volatility):**

   * To create a balanced mutual fund, stocks are selected based on two criteria:

     * Their total ROI must be greater than the median ROI of all companies.

     * Their daily return volatility must be less than the median volatility of all companies.

   * This strategy aims to identify companies that have historically offered good returns with relatively lower risk compared to the broader market.

6. **Investment Ratios (Inverse Volatility Weighting):**

   * For the selected stocks, investment ratios (or weights) are assigned based on their inverse volatility. This means:

     * Stocks with lower volatility (less risky) receive a higher allocation in the portfolio.

     * Stocks with higher volatility (more risky) receive a lower allocation.

   * The ratios are normalized so their sum equals 1 (or 100%).

7. **Portfolio Weighted Average ROI:**

   * The overall expected annual ROI for the entire mutual fund portfolio is calculated by taking a weighted average of the individual ROIs of the selected stocks, using the investment ratios as weights. This is the key growth rate used for future value projections.

8. **Future Value (SIP) Calculation:**

   * The application uses the calculated portfolio's weighted average ROI to project the future value of a Systematic Investment Plan (SIP).

   * The formula used is for the Future Value of an Annuity Due, which assumes monthly payments are made at the beginning of each period, compounding over time.

## Project Structure

```
MutualFundApp/
├── app.py                  # Flask backend: data analysis, API endpoints
├── nifty50_closing_prices.csv # Your historical stock data
├── templates/
│   └── index.html          # Frontend HTML for the web interface
└── static/
    ├── styles.css          # Frontend CSS for styling
    └── script.js           # Frontend JavaScript for interactivity and Plotly charts

```

## Live Demo

Experience the Mutual Fund Plan Generator live:

* **Vercel Deployment:** [Your Vercel Live Link Here]
* **Render Deployment:** [Your Render Live Link Here]

## Setup and Installation (Local)

To run this project on your local machine, follow these steps:

1. **Clone the Repository:**

   ```bash
   git clone <your-repository-url>
   cd MutualFundApp
   ```

2. **Place the Data File:**
   Ensure the `nifty50_closing_prices.csv` file is placed directly in the `MutualFundApp` directory (alongside `app.py`).

3. **Create a Virtual Environment (Recommended):**

   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

4. **Install Dependencies:**

   ```bash
   pip install Flask pandas numpy plotly flask-cors
   ```

5. **Run the Flask Application:**

   ```bash
   python app.py
   ```

   You should see output indicating that the Flask development server is running.

6. **Access the Application:**
   Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Deployment

### Deploying to Vercel

Vercel is a cloud platform for static sites and serverless functions. Flask applications can be deployed as serverless functions.

1. **Ensure `nifty50_closing_prices.csv` is in the root directory.**

2. **Add a `requirements.txt` file:**
   Create a file named `requirements.txt` in your `MutualFundApp` directory with the following content:

   ```
   Flask
   pandas
   numpy
   plotly
   flask-cors
   ```

3. **Configure `vercel.json` (Optional, but recommended for Flask):**
   Create a `vercel.json` file in your `MutualFundApp` directory:

   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```

4. **Deploy:**

   * Install Vercel CLI: `npm i -g vercel`

   * Login: `vercel login`

   * Navigate to your project directory and run: `vercel`

   * Follow the prompts. Vercel will detect the Flask application and deploy it.

### Deploying to Render

Render is a unified cloud to build and run all your apps and websites.

1. **Ensure `nifty50_closing_prices.csv` is in the root directory.**

2. **Add a `requirements.txt` file** (same as for Vercel).

3. **Add a `Procfile`:**
   Create a file named `Procfile` (no extension) in your `MutualFundApp` directory with the following content. This tells Render how to start your web server:

   ```
   web: gunicorn app:app
   ```

   *You'll need to add `gunicorn` to your `requirements.txt`:*

   ```
   Flask
   pandas
   numpy
   plotly
   flask-cors
   gunicorn
   ```

4. **Set up on Render:**

   * Go to the Render Dashboard and click "New Web Service".

   * Connect your GitHub repository.

   * Configure the service:

     * **Build Command:** `pip install -r requirements.txt`

     * **Start Command:** `gunicorn app:app`

     * **Python Version:** Select a compatible Python version (e.g., `Python 3.9.x` or `3.10.x`).

     * **Root Directory:** Ensure it points to `MutualFundApp` if your repo has other folders.

   * Click "Create Web Service". Render will automatically build and deploy your application.

## Usage

Once the application is running (locally or deployed):

1. You will initially see the header and the SIP calculator section. The mutual fund portfolio details and investment projections will be hidden.

2. In the "Projected Investment Growth (SIP)" section, enter your desired monthly investment amount in the input field. **Please note: The amount must be ₹1000 or greater.** If you enter less than ₹1000, an error message will appear below the button.

3. Click the "Calculate Future Value" button.

4. If your input is valid, the "Analyzed Mutual Fund Portfolio" section will appear, displaying the selected companies, their individual ROIs, and their calculated investment ratios, along with the overall portfolio's weighted average ROI.

5. Simultaneously, an interactive chart will appear in the "Proje
cted Investment Growth (SIP)" section, showing the expected future value of your investments over various periods (1, 3, 5, 10, 15, 20, 25, and 30 years). You can hover over the chart points to see exact values.

## Technologies Used

* **Backend:**

  * Python

  * Flask: Web framework

  * Pandas: Data manipulation and analysis

  * NumPy: Numerical operations

  * Flask-CORS: Handling Cross-Origin Resource Sharing

* **Frontend:**

  * HTML5: Structure

  * CSS3: Styling (Responsive Design)

  * JavaScript: Interactivity

  * Plotly.js: Interactive data visualization library

## Disclaimer

This Mutual Fund Plan Generator is for educational and informational purposes only. It uses historical data and a simplified model for projections. **Past performance is not indicative of future results.** Investing in mutual funds and stocks involves market risks, including the possible loss of principal. Always consult with a qualified financial advisor before making any investment decisions.
