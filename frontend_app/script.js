// frontend_app/script.js

// IMPORTANT: Replace this with the URL of your deployed FastAPI API
// For local testing, if your API is running on http://localhost:8000
const API_URL = 'http://localhost:8000/predict';

const sampleSelector = document.getElementById('sampleSelector');
const predictButton = document.getElementById('predictButton');
const predictionText = document.getElementById('predictionText');
const probabilityText = document.getElementById('probabilityText');

let allSamplesData = {}; // To store the loaded sample data

// Function to load samples and populate the dropdown
async function loadSamples() {
    try {
        const response = await fetch('sample_transactions.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        allSamplesData = await response.json();

        // Clear existing options
        sampleSelector.innerHTML = '<option value="">-- Select a sample --</option>';

        // Add non-fraudulent samples
        allSamplesData.non_fraudulent.forEach((sample, index) => {
            const option = document.createElement('option');
            option.value = `non_fraud_${index}`;
            option.textContent = `Non-Fraudulent: ${sample.name}`;
            sampleSelector.appendChild(option);
        });

        // Add fraudulent samples
        allSamplesData.fraudulent.forEach((sample, index) => {
            const option = document.createElement('option');
            option.value = `fraud_${index}`;
            option.textContent = `Fraudulent: ${sample.name}`;
            sampleSelector.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading sample transactions:', error);
        predictionText.textContent = 'Error loading samples. Check console.';
        predictionText.style.color = 'red';
    }
}

// Event listener for the Predict button
predictButton.addEventListener('click', async () => {
    const selectedValue = sampleSelector.value;

    if (!selectedValue) {
        predictionText.textContent = 'Please select a sample transaction.';
        predictionText.style.color = 'red';
        probabilityText.textContent = '';
        return;
    }

    predictionText.textContent = 'Predicting...';
    probabilityText.textContent = '';

    let featuresToSend = [];
    if (selectedValue.startsWith('non_fraud_')) {
        const index = parseInt(selectedValue.split('_')[2]);
        featuresToSend = allSamplesData.non_fraudulent[index].features;
    } else if (selectedValue.startsWith('fraud_')) {
        const index = parseInt(selectedValue.split('_')[1]);
        featuresToSend = allSamplesData.fraudulent[index].features;
    }

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ features: featuresToSend }),
        });

        const result = await response.json();

        if (response.ok) {
            predictionText.style.color = result.prediction === 1 ? 'red' : 'green';
            predictionText.textContent = `Result: ${result.prediction === 1 ? 'Fraudulent' : 'Non-Fraudulent'}`;
            probabilityText.textContent = `Probability of Fraud: ${(result.prediction_proba * 100).toFixed(2)}%`;
        } else {
            predictionText.style.color = 'red';
            predictionText.textContent = `Error: ${result.detail || 'Something went wrong'}`;
            probabilityText.textContent = '';
        }

    } catch (error) {
        predictionText.style.color = 'red';
        predictionText.textContent = `Network Error: ${error.message}. Is the API running and accessible?`;
        probabilityText.textContent = '';
        console.error('Fetch error:', error);
    }
});

// Load samples when the page loads
loadSamples();
