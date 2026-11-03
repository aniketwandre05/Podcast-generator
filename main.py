import base64
import os

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                value = val.strip().strip("'\"")
                if value:
                    os.environ[key.strip()] = value

from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))

# Make first call to Sarvam Text-to-Speech using Bulbul
response = client.text_to_speech.convert(
    text="Welcome to the AI Podcast! Today we explore artificial intelligence, voice models, and the future of audio generation.",
    language_code="en-IN",
    model="bulbul:v3",
    speaker="shubh",
)

# Save generated audio to file
audio_bytes = base64.b64decode(response.audios[0])
output_filename = "podcast_sample.wav"
with open(output_filename, "wb") as f:
    f.write(audio_bytes)

print("Successfully generated podcast audio!")
print(f"Request ID: {response.request_id}")
print(f"Audio saved to: {output_filename} ({len(audio_bytes)} bytes)")
