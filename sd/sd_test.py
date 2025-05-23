import requests

# api server(local)
url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
prompt = "(((Soryu Asuka Langley))), standing on water, reflection visible, background: cloudy red sky, animation style of 'Neon Genesis Evangelion', dramatic lighting, full body, <lora:asuka:1>"
negative_prompt = "(worst quality, low quality, normal quality), (zombie, interlocked fingers, extra limbs, mutated hands, missing arms, blurry face, deformed eyes, bad anatomy)"

# parameter
# http://127.0.0.1:7860/docs#/default/text2imgapi_sdapi_v1_txt2img_post
payload = {
# parameter
    "prompt": prompt,
    "negative_prompt": negative_prompt,
    "seed": -1,
    # "subseed": ,
    "sampler_name": "DPM++ 2M",
    "scheduler": "Karras",
    "steps": 20,
    "cfg_scale": 7,
    "width": 512,
    "height": 768,
    "batch_size": 1,

# model and processing settings
    "override_settings": {
            "sd_model_checkpoint": "meinamix_v12Final.safetensors",
            "sd_vae": "meinamix_v12Final.safetensors",
            "CLIP_stop_at_last_layers": 2  # clip skip
    },

# hires.fix
    "enable_hr": True,
    "hr_scale": 1.5,
    "hr_upscaler": "R-ESRGAN 4x+ Anime6B",
    "hr_second_pass_steps": 10,
    "denoising_strength": 0.5,
}

# http POST
response = requests.post(url, json=payload)

# get image(base64)
result = response.json()
image_data = result['images'][0]

# decode base64 to image.png
import base64
from PIL import Image
from io import BytesIO

image = Image.open(BytesIO(base64.b64decode(image_data)))
image.save("output.png")