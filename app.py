import pandas as pd
import numpy as np
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app) # Enable CORS for frontend interaction

# Global variable to store analysis results after processing the data
# This avoids re-running heavy computations on every API request
ANALYSIS_RESULTS = {}

def perform_data_analysis():
    """
    Loads the CSV data, performs the analysis (cleaning, ROI, Volatility, 
    stock selection), and calculates investment ratios.
    This function is designed to be run once when the app starts or when data needs refreshing.
    """
    global ANALYSIS_RESULTS
    
    # Return cached results if already processed
    if ANALYSIS_RESULTS:
        return ANALYSIS_RESULTS

    file_path = 'nifty50_closing_prices.csv'
    if not os.path.exists(file_path):
        # Handle case where the CSV file is not found
        raise FileNotFoundError(f"The data file {file_path} was not found. Please ensure it's in the same directory as app.py.")

    # 1. Load and preprocess data
    data = pd.read_csv(file_path)
    data['Date'] = pd.to_datetime(data['Date'])

    # Identify all columns that are not 'Date'
    stock_columns = data.columns.drop('Date')

    # Convert all stock columns to numeric, coercing errors to NaN
    # This ensures that any non-numeric entries become NaN and can be filled
    for col in stock_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    # Fill null values using the forward fill method, then backward fill to catch any remaining NaNs
    data = data.ffill().bfill()

    # Check for and drop any columns that remain entirely null (e.g., if a column was all NaNs)
    initial_null_counts = data.isnull().sum()
    columns_to_drop = initial_null_counts[initial_null_counts == len(data)].index.tolist()

    if columns_to_drop:
        print(f"Dropping entirely null columns: {columns_to_drop}")
        data.drop(columns=columns_to_drop, inplace=True)
        # Update stock_columns after dropping
        stock_columns = data.columns.drop('Date')
    
    # After cleaning, ensure there are no remaining NaNs that would break calculations
    if data.isnull().sum().sum() > 0:
        print("Warning: Some null values still present after ffill/bfill and dropping entirely null columns.")
        print(data.isnull().sum()[data.isnull().sum() > 0])
        # As a last resort, drop rows with any remaining NaNs for calculations
        data.dropna(inplace=True)
        if data.empty:
            raise ValueError("Dataset became empty after dropping rows with NaN values. Cannot perform analysis.")

    # Ensure daily_returns can be calculated (needs at least 2 rows)
    if len(data) < 2:
        raise ValueError("Not enough data points to calculate daily returns. Need at least two rows.")

    # 2. Calculate Daily Returns
    daily_returns = data.drop('Date', axis=1).pct_change() * 100
    # Drop first row of daily_returns as it will be NaN due to pct_change
    daily_returns.dropna(inplace=True)

    # Ensure daily_returns is not empty after dropping NaNs
    if daily_returns.empty:
        raise ValueError("Daily returns could not be calculated or resulted in an empty DataFrame.")

    # 3. Calculate Volatility (Standard Deviation of Daily Returns)
    volatility_all_companies = daily_returns.std()

    # 4. Calculate Total Return on Investment (ROI)
    initial_prices_all = data.drop('Date', axis=1).iloc[0]
    final_prices_all = data.drop('Date', axis=1).iloc[-1]
    # Handle potential division by zero if initial price is 0
    roi_all_companies = ((final_prices_all - initial_prices_all) / initial_prices_all.replace(0, np.nan)) * 100
    roi_all_companies.dropna(inplace=True) # Drop companies with NaN ROI (e.g., initial price was 0 or NaN)

    # Ensure there are companies left after ROI calculation
    if roi_all_companies.empty:
        raise ValueError("No companies remaining after ROI calculation. Check data for all zero initial prices.")

    # 5. Define thresholds and select companies (High ROI, Low Volatility)
    # Ensure there are enough values to calculate median
    if len(roi_all_companies) == 0 or len(volatility_all_companies) == 0:
        raise ValueError("Insufficient data to calculate ROI or Volatility medians.")
        
    roi_threshold = roi_all_companies.median()
    volatility_threshold = volatility_all_companies.median()

    # Filter companies that meet both criteria
    # Ensure indices are aligned for boolean indexing
    common_companies = roi_all_companies.index.intersection(volatility_all_companies.index)
    
    selected_companies_mask = (roi_all_companies[common_companies] > roi_threshold) & \
                              (volatility_all_companies[common_companies] < volatility_threshold)
    
    selected_companies_roi = roi_all_companies[common_companies][selected_companies_mask].sort_values(ascending=False)

    # Get the volatility for only the selected companies
    selected_volatility = volatility_all_companies[selected_companies_roi.index]

    # Ensure at least one company is selected
    if selected_companies_roi.empty:
        raise ValueError("No companies meet the criteria for high ROI and low volatility. Adjust thresholds or data.")

    # 6. Calculate Investment Ratios (Inverse Volatility)
    # Handle potential division by zero if selected_volatility has 0 values
    inverse_volatility = 1 / selected_volatility.replace(0, np.nan)
    inverse_volatility.dropna(inplace=True) # Drop companies if volatility was 0

    if inverse_volatility.sum() == 0:
        raise ValueError("Sum of inverse volatility is zero, cannot calculate investment ratios.")

    investment_ratios = (inverse_volatility / inverse_volatility.sum()).sort_values(ascending=False)
    
    # Realign selected_companies_roi to match the final investment_ratios index
    selected_companies_roi = selected_companies_roi.reindex(investment_ratios.index)

    # 7. Calculate Portfolio Weighted Average ROI
    weighted_avg_roi = (selected_companies_roi * investment_ratios).sum()

    # Store results in the global variable
    ANALYSIS_RESULTS = {
        'selected_companies_roi': selected_companies_roi.to_dict(),
        'investment_ratios': investment_ratios.to_dict(),
        'weighted_avg_roi': weighted_avg_roi
    }
    
    return ANALYSIS_RESULTS

# --- Future Value Calculation Function (SIP) ---

def future_value_calculator(P, r, n, t):
    """
    Calculates the future value of a series of investments (SIP).
    P: monthly investment amount
    r: average annual ROI (decimal)
    n: number of times interest is compounded per year (12 for monthly)
    t: number of years
    """
    rate_per_period = r / n
    total_periods = n * t
    
    if rate_per_period == 0:
        return P * total_periods
    
    # Formula for Future Value of an Annuity Due (payments at the beginning of the period)
    future_value = P * (((1 + rate_per_period)**total_periods - 1) / rate_per_period) * (1 + rate_per_period)
    return future_value

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page for the application."""
    return render_template('index.html')

@app.route('/api/plan_details', methods=['GET'])
def get_plan_details():
    """
    API endpoint to provide the analysis results (selected stocks, ratios, average ROI).
    This endpoint triggers the data analysis if it hasn't been performed yet.
    """
    try:
        analysis_results = perform_data_analysis()
        return jsonify({'success': True, 'data': analysis_results})
    except FileNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except ValueError as e:
        return jsonify({'success': False, 'error': f"Data analysis error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f"An unexpected error occurred during analysis: {str(e)}"}), 500

@app.route('/api/calculate_future_value', methods=['POST'])
def calculate_fv():
    """
    API endpoint to calculate future value based on user inputs and the mutual fund's ROI.
    """
    data = request.json
    try:
        monthly_investment = float(data.get('monthly_investment'))
        
        # Ensure analysis data is loaded and retrieved
        analysis_results = perform_data_analysis()
        weighted_avg_roi_percent = analysis_results['weighted_avg_roi']
        
        # Convert ROI to decimal for calculation (e.g., 5.86% -> 0.0586)
        avg_roi_decimal = weighted_avg_roi_percent / 100 
        
        # Standard investment periods and monthly compounding
        investment_periods = [1, 3, 5, 10, 15, 20, 25, 30] # Extended years for long-term projection
        n = 12 # Monthly compounding
        
        results = []
        for years in investment_periods:
            fv = future_value_calculator(monthly_investment, avg_roi_decimal, n, years)
            results.append({
                'years': years,
                'future_value': round(fv, 2)
            })

        return jsonify({'success': True, 'future_values': results, 'weighted_roi': weighted_avg_roi_percent})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    # Perform initial data analysis when the Flask app starts
    print("Performing initial stock data analysis...")
    try:
        perform_data_analysis()
        print("Initial analysis complete. Starting Flask server...")
    except Exception as e:
        print(f"Failed to perform initial data analysis: {e}")
        print("Please ensure 'nifty50_closing_prices.csv' is present and valid.")
        # Exit if initial analysis fails, as the app won't function correctly without it
        exit() 
    app.run(debug=True) # debug=True enables auto-reloading and better error messages
