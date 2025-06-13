import os
import io
import numpy as np
from PIL import Image
from flask import Flask, request, send_file, render_template_string
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch
from transformers import pipeline

# === Flask App ===
app = Flask(__name__)

# === HTML Template ===
HTML_FORM = """
<!doctype html>
<title>Tile Generator</title>
<h2>Generate Tiled Dungeon Map</h2>
{% if error %}
<div style="color: red; margin-bottom: 15px;">{{ error }}</div>
{% endif %}
<form method=post enctype=multipart/form-data>
  Prompt: <input type=text name=prompt size=60><br>
  Tile Count: <input type=number name=tile_count value=3><br>
  Input Image (required): <input type=file name=input_image accept="image/*" required><br>
  <input type=submit value=Generate>
</form>
{% if image_url %}
<hr>
<h3>Result</h3>
<img src="{{ image_url }}" style="max-width:100%">
{% endif %}
"""

# === Load Model Once ===
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Load depth estimator for better image extension
depth_estimator = pipeline("depth-estimation", model="Intel/dpt-large")

# Use a model better suited for extending images
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-depth", 
    torch_dtype=torch.float16 if device == "mps" else torch.float32
)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16 if device == "mps" else torch.float32,
).to(device)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

# Disable the safety checker
pipe.safety_checker = None
pipe.requires_safety_checker = False

# Only use xformers if not on Mac
if device != "mps" and device != "cpu":
    pipe.enable_xformers_memory_efficient_attention()

# === Image Generator ===
def generate_depth_map(image):
    """Generate a depth map from an image using the depth estimator."""
    depth_result = depth_estimator(image)
    depth_map = depth_result["depth"]
    depth_map = np.array(depth_map)
    
    # Normalize depth map to 0-255 range
    depth_min, depth_max = np.min(depth_map), np.max(depth_map)
    depth_map = 255 * (depth_map - depth_min) / (depth_max - depth_min)
    depth_map = depth_map.astype(np.uint8)
    
    return Image.fromarray(depth_map)

def generate_tiled_image(prompt, tile_count=3, tile_size=512, input_image=None):
    # Only proceed if an input image is provided
    if not input_image:
        raise ValueError("An input image is required")
    
    # Resize input image to match tile size
    input_image = input_image.resize((tile_size, tile_size), Image.LANCZOS)
    
    # Save the original image for reference
    input_image.save("static/original_image.png")
    
    # Use the first image as is
    tiles = [input_image]
    
    # For each additional tile, extend from the previous one
    for i in range(1, tile_count):
        prev_tile = tiles[-1]
        
        # Extract the right edge of the previous tile (64 pixels wide)
        guide_edge = prev_tile.crop((tile_size - 64, 0, tile_size, tile_size))
        
        # Create a new image with the guide edge on the left
        control_image = Image.new("RGB", (tile_size, tile_size), (255, 255, 255))
        control_image.paste(guide_edge, (0, 0))
        
        # Generate depth map for better control
        depth_map = generate_depth_map(control_image)
        
        # Save for debugging
        control_image.save(f"static/control_image_{i}.png")
        depth_map.save(f"static/depth_map_{i}.png")
        
        # Generate the next tile with strong guidance to match the previous one
        generator = torch.Generator(device=device).manual_seed(42 + i)
        next_tile = pipe(
            prompt=f"{prompt}, seamless continuation, same style, same perspective",
            image=depth_map,
            generator=generator,
            width=tile_size,
            height=tile_size,
            num_inference_steps=50,  # More steps for better quality
            guidance_scale=9.0,      # Stronger guidance to follow the prompt
        ).images[0]
        
        # Blend the edge for smoother transition
        blended_tile = next_tile.copy()
        for x in range(64):
            blend_factor = x / 64.0
            for y in range(tile_size):
                # Get pixels from both images
                prev_pixel = guide_edge.getpixel((x, y))
                next_pixel = next_tile.getpixel((x, y))
                
                # Blend pixels
                blended_pixel = tuple(int(prev_pixel[i] * (1 - blend_factor) + next_pixel[i] * blend_factor) for i in range(3))
                blended_tile.putpixel((x, y), blended_pixel)
        
        tiles.append(blended_tile)

    # Create the final map by stitching tiles together
    map_image = Image.new("RGB", (tile_size * tile_count, tile_size))
    
    # Place the first tile (original image)
    map_image.paste(tiles[0], (0, 0))
    
    # Place subsequent tiles with overlap for better blending
    for idx in range(1, len(tiles)):
        # Place each tile with a 64-pixel overlap
        map_image.paste(tiles[idx], ((idx * tile_size) - 64, 0))
    
    return map_image

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        tile_count = int(request.form.get('tile_count', 3))
        
        # Process uploaded image - it's required
        if 'input_image' not in request.files or not request.files['input_image'].filename:
            return render_template_string(HTML_FORM, error="Please upload an input image")
        
        file = request.files['input_image']
        input_image = Image.open(file.stream).convert('RGB')
        print(f"Input image received: {file.filename}")
        
        print(f"Generating image with prompt: {prompt}, tile count: {tile_count}")
        out_img = generate_tiled_image(prompt, tile_count, input_image=input_image)

        os.makedirs("static", exist_ok=True)
        buffer = io.BytesIO()
        out_img.save(buffer, format='PNG')
        buffer.seek(0)

        with open("static/output.png", "wb") as f:
            f.write(buffer.getvalue())

        image_url = '/static/output.png'
    return render_template_string(HTML_FORM, image_url=image_url)

# === Start Server ===
if __name__ == '__main__':
    print("Starting Flask server on port 7860...")
    app.run(debug=True, host="0.0.0.0", port=7860)
