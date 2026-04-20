# Soniox Text-to-Speech examples

## 1. Get API key

Create a free [Soniox account](https://console.soniox.com/signup) and log in to the [Console](https://console.soniox.com) to get your API key.

API keys are created per project. In the Console, go to **My First Project** and click **API Keys** to generate one.

Export it as an environment variable (replace with your key):

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## 2. Get examples

Clone the official examples repo:

```sh
git clone https://github.com/soniox/soniox_examples
cd soniox_examples/text_to_speech
```

## 3. Run examples

Run the ready-to-use examples below.

| Example | What it does | Output |
| --- | --- | --- |
| **REST** | Sends text in a single HTTP POST and generates speech. | Audio file written to disk. |
| **Realtime <br> WebSocket** | Streams text line by line over a WebSocket and collects audio chunks. | Audio file written to disk. |
| **Realtime <br> multi-stream** | Sends multiple streams (English, Spanish, Slovenian) over a single WebSocket. | One audio file per stream written to disk. |

<details open>
<summary><b>Python</b></summary>

```sh
# Set up environment
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# REST example
python soniox_rest.py --text "Hello from Soniox TTS." --language en --voice Adrian --audio_format wav

# Realtime WebSocket example
python soniox_realtime.py --line "Hello from Soniox realtime TTS." --line "This is the second line." --language en --voice Adrian --audio_format wav

# Realtime multi-stream example
python soniox_realtime_multi_stream.py --audio_format wav
```

</details>