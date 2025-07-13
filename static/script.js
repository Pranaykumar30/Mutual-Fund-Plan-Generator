let globalAnalysisData = null; // To store the fetched plan details

document.addEventListener('DOMContentLoaded', async () => {
    // Hide the plan summary and results sections initially
    document.getElementById('plan-summary-section').style.display = 'none';
    document.getElementById('results').style.display = 'none';
    // Also hide the validation error message initially
    document.getElementById('validationErrorMessage').style.display = 'none';

    // Fetch plan details once on page load, but don't display them yet.
    // This pre-loads the data so it's ready when the user clicks "Calculate".
    try {
        const response = await fetch('/api/plan_details');
        const result = await response.json();
        if (result.success) {
            globalAnalysisData = result.data; // Store data globally
        } else {
            console.error('Error fetching initial plan details:', result.error);
            // Display an error message in the plan summary section if initial fetch fails
            const planSummarySection = document.getElementById('plan-summary-section');
            planSummarySection.style.display = 'block'; // Make it visible to show the error
            document.getElementById('plan-details-container').innerHTML = 
                `<p style="color: red;">Error loading portfolio analysis: ${result.error}. Please ensure the backend is running and data file is available.</p>`;
        }
    } catch (error) {
        console.error('Network error during initial fetch:', error);
        const planSummarySection = document.getElementById('plan-summary-section');
        planSummarySection.style.display = 'block'; // Make it visible to show the error
        document.getElementById('plan-details-container').innerHTML = 
            '<p style="color: red;">Could not connect to the analysis service. Please check your network and ensure the backend is running.</p>';
    }
});

// Sends the user's monthly investment amount to the backend for calculation
async function calculateFutureValue() {
    const monthlyInvestmentInput = document.getElementById('monthlyInvestment');
    const monthlyInvestment = parseFloat(monthlyInvestmentInput.value);
    const validationErrorMessage = document.getElementById('validationErrorMessage');
    
    // Clear previous error message and hide it
    validationErrorMessage.textContent = '';
    validationErrorMessage.style.display = 'none';

    // Validation: Amount must be greater than or equal to 1000
    if (isNaN(monthlyInvestment) || monthlyInvestment < 1000) {
        validationErrorMessage.textContent = "Please enter a monthly investment amount of ₹1000 or greater.";
        validationErrorMessage.style.display = 'block';
        monthlyInvestmentInput.focus(); // Focus on the input field
        // Hide summary and results if input is invalid
        document.getElementById('plan-summary-section').style.display = 'none';
        document.getElementById('results').style.display = 'none';
        return; // Stop execution if validation fails
    }

    // Ensure globalAnalysisData is available before proceeding with displaying details
    if (!globalAnalysisData) {
        validationErrorMessage.textContent = "Portfolio analysis data is not yet loaded. Please try again in a moment or check the backend server.";
        validationErrorMessage.style.display = 'block';
        // Hide summary and results if data not loaded
        document.getElementById('plan-summary-section').style.display = 'none';
        document.getElementById('results').style.display = 'none';
        return;
    }

    // Display the plan summary and results sections now that the button is clicked and input is valid
    document.getElementById('plan-summary-section').style.display = 'block';
    document.getElementById('results').style.display = 'block';
    
    // Display the fetched plan details in the summary section
    displayPlanDetails(globalAnalysisData);

    try {
        const response = await fetch('/api/calculate_future_value', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ monthly_investment: monthlyInvestment })
        });

        const result = await response.json();

        if (result.success) {
            plotFutureValue(result.future_values, result.weighted_roi);
        } else {
            console.error('Calculation error:', result.error);
            validationErrorMessage.textContent = 'An error occurred during calculation: ' + result.error;
            validationErrorMessage.style.display = 'block';
            // Hide results if calculation fails after showing them
            document.getElementById('results').style.display = 'none';
            document.getElementById('plan-summary-section').style.display = 'none'; // Also hide summary
        }
    } catch (error) {
        console.error('Network error during calculation:', error);
        validationErrorMessage.textContent = 'Could not connect to the calculation service. Please check your network and backend server.';
        validationErrorMessage.style.display = 'block';
        // Hide results if network call fails
        document.getElementById('results').style.display = 'none';
        document.getElementById('plan-summary-section').style.display = 'none'; // Also hide summary
    }
}

// Displays the selected companies and their investment ratios
function displayPlanDetails(data) {
    const container = document.getElementById('plan-details-container');
    const companies = data.investment_ratios;
    
    // Display the calculated weighted average ROI
    const weightedRoi = data.weighted_avg_roi ? data.weighted_avg_roi.toFixed(2) : 'N/A';
    
    let html = `
        <p><strong>Portfolio Weighted Average ROI:</strong> ${weightedRoi}%</p>
        <p><strong>Selected Companies (High ROI, Low Volatility) and Investment Ratios:</strong></p>
        <ul>
    `;
    
    // Iterate through companies and ratios, displaying ROI if available
    // Ensure we iterate over the sorted companies from the backend
    for (const company in companies) {
        if (Object.hasOwnProperty.call(companies, company)) {
            const ratioPercent = (companies[company] * 100).toFixed(2);
            const roi = data.selected_companies_roi[company] ? data.selected_companies_roi[company].toFixed(2) : 'N/A';
            html += `<li><strong>${company}</strong>: ${ratioPercent}% allocation (ROI: ${roi}%)</li>`;
        }
    }
    
    html += `</ul>`;
    container.innerHTML = html;
}

// Renders the future value chart using Plotly.js
function plotFutureValue(data, weightedRoi) {
    const years = data.map(item => item.years + ' Years');
    const values = data.map(item => item.future_value);

    // Update ROI info heading
    document.getElementById('roi-info').textContent = `Expected Growth based on ${weightedRoi.toFixed(2)}% Annual ROI`;

    const trace = {
        x: years,
        y: values,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { size: 10, color: '#004d99', symbol: 'circle' },
        line: { color: '#007bff', width: 3, shape: 'spline' }, /* Smoother line */
        hovertemplate: '<b>Period:</b> %{x}<br><b>Future Value:</b> ₹%{y:,.2f}<extra></extra>'
    };

    const layout = {
        title: {
            text: `Future Value of ₹${document.getElementById('monthlyInvestment').value} Monthly SIP`,
            font: {
                size: 18,
                color: '#003366'
            }
        },
        xaxis: {
            title: 'Investment Period',
            showgrid: true,
            gridcolor: '#e0e0e0',
            tickangle: 45
        },
        yaxis: {
            title: 'Future Value (INR)',
            tickformat: '₹,.0f', /* Format y-axis ticks as currency */
            showgrid: true,
            gridcolor: '#e0e0e0'
        },
        margin: { t: 60, b: 80, l: 80, r: 20 }, /* Adjust margins for better layout */
        hovermode: 'x unified', /* Unified hover for better UX */
        template: 'plotly_white',
        plot_bgcolor: '#f7f9fc', /* Light background for plot area */
        paper_bgcolor: '#f7f9fc' /* Match paper background */
    };

    // Plot the data in the futureValueChart div
    Plotly.newPlot('futureValueChart', [trace], layout);
}
