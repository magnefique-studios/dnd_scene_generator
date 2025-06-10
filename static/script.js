document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');
    const resultElement = document.getElementById('result');
    const generatedImage = document.getElementById('generated-image');
    const usedPrompt = document.getElementById('used-prompt');

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        
        if (!prompt) {
            showError('Please enter a prompt');
            return;
        }

        // Show loading, hide other elements
        loadingElement.classList.remove('hidden');
        errorElement.classList.add('hidden');
        resultElement.classList.add('hidden');
        generateBtn.disabled = true;

        try {
            const response = await fetch('/generate-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate image');
            }

            // Display the generated image
            generatedImage.src = `data:image/png;base64,${data.image}`;
            usedPrompt.textContent = prompt;
            
            // Hide loading, show result
            loadingElement.classList.add('hidden');
            resultElement.classList.remove('hidden');
        } catch (error) {
            showError(error.message);
            loadingElement.classList.add('hidden');
        } finally {
            generateBtn.disabled = false;
        }
    });

    function showError(message) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
});
