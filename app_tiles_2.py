
import os
import io
from PIL import Image
from flask import Flask, request, send_file, render_template_string
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch

# === Flask App ===
app = Flask(__name__)

# === Load Model Once ===
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_inpaint", torch_dtype=torch.float16
)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_xformers_memory_efficient_attention()

# === HTML Template ===
HTML_FORM = """
<!doctype html>
<title>Tile Generator</title>
<h2>Generate Tiled Dungeon Map</h2>
<form method=post enctype=multipart/form-data>
  Prompt: <input type=text name=prompt size=60><br>
  Tile Count: <input type=number name=tile_count value=3><br>
  <input type=submit value=Generate>
</form>
{% if image_url %}
<hr>
<h3>Result</h3>
<img src="{{ image_url }}" style="max-width:100%">
{% endif %}
"""

# === Image Generator ===
def generate_tiled_image(prompt, tile_count=3, tile_size=512):
    generator = torch.Generator(device="cuda").manual_seed(42)
    first_tile = pipe(prompt=prompt, generator=generator, width=tile_size, height=tile_size).images[0]
    tiles = [first_tile]

    for i in range(1, tile_count):
        prev_tile = tiles[-1]
        guide_edge = prev_tile.crop((tile_size - 64, 0, tile_size, tile_size))
        control_image = Image.new("RGB", (tile_size, tile_size), (0, 0, 0))
        control_image.paste(guide_edge, (0, 0))

        generator = torch.Generator(device="cuda").manual_seed(42 + i)
        next_tile = pipe(
            prompt=prompt,
            image=control_image,
            generator=generator,
            width=tile_size,
            height=tile_size,
            num_inference_steps=30,
        ).images[0]
        tiles.append(next_tile)

    map_image = Image.new("RGB", (tile_size * tile_count, tile_size))
    for idx, tile in enumerate(tiles):
        map_image.paste(tile, (idx * tile_size, 0))

    return map_image

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        tile_count = int(request.form.get('tile_count', 3))
        out_img = generate_tiled_image(prompt, tile_count)

        buffer = io.BytesIO()
        out_img.save(buffer, format='PNG')
        buffer.seek(0)

        with open("static/output.png", "wb") as f:
            f.write(buffer.getvalue())

        image_url = '/static/output.png'
    return render_template_string(HTML_FORM, image_url=image_url)

# === Start Server ===
if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=7860)
