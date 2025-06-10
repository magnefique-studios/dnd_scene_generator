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
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Using Stable Diffusion XL on Amazon Bedrock
        # Model ID for Stable Diffusion XL
        model_id = "stability.stable-diffusion-xl-v1"
        
        # Prepare request body for the model
        request_body = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": 7,
            "steps": 30,
            "seed": 0
        }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the base64 encoded image
        image_base64 = response_body['artifacts'][0]['base64']
        
        return jsonify({
            'success': True,
            'image': image_base64
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
