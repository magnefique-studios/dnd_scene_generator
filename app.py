from flask import Flask, render_template, request, jsonify
import boto3
import base64
import json
import os
from io import BytesIO

app = Flask(__name__)

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model_choice = data.get('model', 'stability.stable-diffusion-xl-v1')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Set model ID based on user selection
        model_id = model_choice
        
        negative_prompt = data.get('negative_prompt', '')
        
        if model_id == "stability.stable-diffusion-xl-v1":
            # Prepare request body for Stable Diffusion XL with max size (1024x1024)
            request_body = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": 7,
                "steps": 30,
                "seed": 0,
                "width": 1024,
                "height": 1024
            }
            
            # Add negative prompt if provided
            if negative_prompt:
                request_body["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
                
        elif model_id == "amazon.titan-image-generator-v1":
            # Prepare request body for AWS Titan Text-to-Image v1 with max size (1408x1408)
            request_body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": negative_prompt if negative_prompt else "none",
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1408,
                    "width": 1408,
                    "cfgScale": 8.0,
                    "seed": 0
                }
            }
        elif model_id == "amazon.titan-image-generator-v2:0":
            # Prepare request body for AWS Titan Text-to-Image v2
            request_body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": negative_prompt if negative_prompt else "none",
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "cfgScale": 8.0,
                    "seed": 0
                }
            }
        else:
            return jsonify({'error': 'Invalid model selection'}), 400
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the base64 encoded image based on model
        if model_id == "stability.stable-diffusion-xl-v1":
            image_base64 = response_body['artifacts'][0]['base64']
        else:  # Titan models (v1 and v2)
            image_base64 = response_body['images'][0]
        
        return jsonify({
            'success': True,
            'image': image_base64
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
