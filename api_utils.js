/* ============================= */
/*       API UTILS               */
/* ============================= */

/**
 * Fetch loan recommendations from a (mock) API
 * Replace URL with real API endpoint or connect backend
 */
async function fetchLoanRecommendations(category) {
    try {
        // Example: free API endpoint placeholder
        // const response = await fetch(`https://api.example.com/loans?category=${category}`);
        // const data = await response.json();

        // Mock data for demo
        const mockData = [
            { type: 'Home Loan', vendor: 'Bank A', interest: '7.5%', tenure: '20 yrs' },
            { type: 'Car Loan', vendor: 'Bank B', interest: '8.2%', tenure: '7 yrs' },
            { type: 'Education Loan', vendor: 'Bank C', interest: '6.8%', tenure: '10 yrs' }
        ];
        return mockData;
    } catch (err) {
        console.error('Error fetching loan recommendations:', err);
        return [];
    }
}

/**
 * Fetch trading/portfolio data from API
 */
async function fetchTradingData() {
    try {
        // Example: free stock API placeholder
        // const response = await fetch('https://api.example.com/trading');
        // const data = await response.json();

        // Mock data for demo
        const mockData = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            values: [10000, 10500, 10200, 11000, 11500, 12000]
        };
        return mockData;
    } catch (err) {
        console.error('Error fetching trading data:', err);
        return { labels: [], values: [] };
    }
}

/**
 * Call Grok AI API for predictions or suggestions
 * Replace with your actual Grok AI endpoint and key
 */
async function fetchAIPrediction(prompt) {
    try {
        const apiKey = 'YOUR_GROK_AI_KEY'; // store securely in production
        const response = await fetch('https://api.grok.ai/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({ prompt })
        });
        const data = await response.json();
        return data.prediction || 'No prediction available';
    } catch (err) {
        console.error('Error fetching AI prediction:', err);
        return 'AI service unavailable';
    }
}
