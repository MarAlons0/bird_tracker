async function getAIAnalysis() {
    const loadingDiv = document.getElementById('analysis-loading');
    const containerDiv = document.getElementById('ai-analysis-container');
    
    try {
        // Show loading spinner
        loadingDiv.style.display = 'block';
        containerDiv.innerHTML = '';
        
        const response = await fetch('/api/ai-analysis', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        // Hide loading spinner
        loadingDiv.style.display = 'none';
        
        if (data.status === 'success') {
            // Create analysis content
            const analysisContent = document.createElement('div');
            analysisContent.className = 'mt-3';
            
            // Add analysis text
            const analysisText = document.createElement('div');
            analysisText.className = 'analysis-text mb-3';
            analysisText.innerHTML = data.analysis.replace(/\n/g, '<br>');
            analysisContent.appendChild(analysisText);
            
            // Add retry button
            const retryButton = document.createElement('button');
            retryButton.className = 'btn btn-secondary';
            retryButton.textContent = 'Generate New Analysis';
            retryButton.onclick = getAIAnalysis;
            analysisContent.appendChild(retryButton);
            
            containerDiv.innerHTML = '';
            containerDiv.appendChild(analysisContent);
        } else {
            // Handle error
            containerDiv.innerHTML = `
                <div class="alert alert-danger">
                    ${data.message || 'Failed to generate AI analysis. Please try again.'}
                    <button class="btn btn-secondary mt-2" onclick="getAIAnalysis()">Retry</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error getting AI analysis:', error);
        loadingDiv.style.display = 'none';
        containerDiv.innerHTML = `
            <div class="alert alert-danger">
                An error occurred while generating the analysis. Please try again.
                <button class="btn btn-secondary mt-2" onclick="getAIAnalysis()">Retry</button>
            </div>
        `;
    }
} 