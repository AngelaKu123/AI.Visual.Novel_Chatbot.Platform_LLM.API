import requests
import threading
import time
import sys
import base64
from PIL import Image
from io import BytesIO

# api server(local)
url = "http://127.0.0.1:7860"

prompt = "(((Soryu Asuka Langley))), standing on water, reflection visible, background: cloudy red sky, animation style of 'Neon Genesis Evangelion', dramatic lighting, full body, <lora:asuka:1>"
negative_prompt = "(worst quality, low quality, normal quality), (zombie, interlocked fingers, extra limbs, mutated hands, missing arms, blurry face, deformed eyes, bad anatomy)"


# parameter
# http://127.0.0.1:7860/docs#/default/text2imgapi_sdapi_v1_txt2img_post
parameter = {
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

    "enable_hr": True,
    "hr_scale": 2,
    "hr_upscaler": "R-ESRGAN 4x+ Anime6B",
    "hr_second_pass_steps": 10,
    "denoising_strength": 0.45,

    "override_settings": {
        "sd_model_checkpoint": "meinamix_v12Final.safetensors",
        "sd_vae": "meinamix_v12Final.safetensors", 
        "CLIP_stop_at_last_layers": 2
    }
}

# stop follow progress flag
stop_progress = False

# show progress every second
def poll_progress():    
    while not stop_progress:
        try:
            r = requests.get(f"{url}/sdapi/v1/progress")
            if r.status_code == 200:
                progress_data = r.json()
                progress = progress_data.get("progress", 0)
                eta = progress_data.get("eta_relative", 0)

                # drawing progress bar
                bar_length = 30
                filled_length = int(bar_length * progress)
                bar = "█" * filled_length + '-' * (bar_length - filled_length)
                sys.stdout.write(f"\nprogress: |{bar}| {progress*100:.1f}% - 剩餘約 {eta:.1f} 秒")
                sys.stdout.flush()

            time.sleep(1)
        except Exception as e:
            print("\nfollow failed: ", e)
            break

def main():
    global stop_progress

    # start following progress
    progress_thread = threading.Thread(target=poll_progress)
    progress_thread.start()

    # start txt2img
    response = requests.post(f"{url}/sdapi/v1/txt2img", json=parameter)

    stop_progress = True  # stop following progress
    progress_thread.join()

    if response.status_code == 200:
        print("\nproduce success!")
        result = response.json()
        # get image(base64)
        image_data = result['images'][0]
        print(f"\nall {len(result['images'])} pictures!")

        # decode base64
        image = Image.open(BytesIO(base64.b64decode(image_data)))
        image.save("output.png")
        print(f"\nimage saved at api folder")
    else:
        print("\nproduce failed, http error: ", response.status_code)

if __name__ == "__main__":
    main()
