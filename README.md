# AI Image Generator with Amazon Bedrock


## Q CLI Prompt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 You are chatting with claude-3.7-sonnet

> i want you to make me a web app i can run in a docker container and I want it to have a UI where I enter in a prompt ( chat ) where i ask for an image to be created and I want the response ( in the server app ) to use the best model on amazon bedrock fortext to image generation
I'll help you create a web app in a Docker container that uses Amazon Bedrock for text-to-image generation.

This web application allows users to generate images from text prompts using Amazon Bedrock's text-to-image models.

## Features

- Simple web interface for entering text prompts
- Backend API that connects to Amazon Bedrock
- Docker containerization for easy deployment
- Responsive design

## Prerequisites

- Docker and Docker Compose
- AWS account with access to Amazon Bedrock
- AWS credentials with appropriate permissions

## Setup

1. Clone this repository
2. Configure your AWS credentials:

   Create a `.env` file in the project root with the following:

   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1  # or your preferred region where Bedrock is available
   ```

3. Build and run the Docker container:

   ```bash
   docker-compose up --build
   ```

4. Access the application at http://localhost:5000

## AWS Permissions

Ensure your AWS credentials have permissions to access the Amazon Bedrock service, specifically:

- `bedrock:InvokeModel`
- `bedrock:ListFoundationModels`

## Technology Stack

- Backend: Python with Flask
- Frontend: HTML, CSS, JavaScript
- Container: Docker
- AWS Services: Amazon Bedrock

## Notes

- The application uses Stable Diffusion XL by default, which is one of the best text-to-image models available on Amazon Bedrock.
- For production use, consider implementing additional security measures and optimizations.
