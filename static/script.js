document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt-input');
    const negativePromptInput = document.getElementById('negative-prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');
    const resultElement = document.getElementById('result');
    const generatedImage = document.getElementById('generated-image');
    const usedPrompt = document.getElementById('used-prompt');
    const modelSelect = document.getElementById('model-select');

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        const negativePrompt = negativePromptInput.value.trim();
        const selectedModel = modelSelect.value;
        
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
                body: JSON.stringify({ 
                    prompt,
                    negative_prompt: negativePrompt,
                    model: selectedModel
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate image');
            }

            // Display the generated image
            generatedImage.src = `data:image/png;base64,${data.image}`;
            usedPrompt.textContent = prompt;
            document.getElementById('used-negative-prompt').textContent = negativePrompt || 'None';
            
            // Show save button
            const saveBtn = document.getElementById('save-btn');
            saveBtn.classList.remove('hidden');
            
            // Store data for saving
            saveBtn.dataset.imageData = data.image;
            saveBtn.dataset.prompt = prompt;
            saveBtn.dataset.negativePrompt = negativePrompt || 'None';
            saveBtn.dataset.model = selectedModel;
            
            // Hide loading, show result and prompt display
            loadingElement.classList.add('hidden');
            resultElement.classList.remove('hidden');
            document.getElementById('prompt-display').classList.remove('hidden');
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
    // Save button functionality
    document.getElementById('save-btn').addEventListener('click', function() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const imageData = this.dataset.imageData;
        const prompt = this.dataset.prompt;
        const negativePrompt = this.dataset.negativePrompt;
        const model = this.dataset.model;
        
        // Force a small delay between downloads to prevent browser blocking
        setTimeout(() => {
            // Save image
            const imageLink = document.createElement('a');
            imageLink.href = `data:image/png;base64,${imageData}`;
            imageLink.download = `dnd-scene-${timestamp}.png`;
            document.body.appendChild(imageLink); // Append to body to ensure it works in all browsers
            imageLink.click();
            document.body.removeChild(imageLink);
            
            // Create text content
            const textContent = `Prompt: ${prompt}\nNegative Prompt: ${negativePrompt}\nModel: ${model}`;
            
            // Save text file after a small delay
            setTimeout(() => {
                const textLink = document.createElement('a');
                const textBlob = new Blob([textContent], {type: 'text/plain'});
                textLink.href = URL.createObjectURL(textBlob);
                textLink.download = `dnd-scene-${timestamp}.txt`;
                document.body.appendChild(textLink);
                textLink.click();
                document.body.removeChild(textLink);
                URL.revokeObjectURL(textLink.href);
            }, 100);
        }, 0);
    });