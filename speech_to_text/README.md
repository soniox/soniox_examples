# Soniox examples

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
cd soniox_examples/speech_to_text
```

## 3. Run examples 

Run the ready-to-use examples below.

| Example                               | What it does                                                                                                     | Output                                                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| **Real-time <br> transcription**      | Transcribes speech in any language in real time.                                                             | Transcript streamed to console.                              |
| **Real-time <br> one-way translation** | Transcribes speech in any language and translates it into Spanish in real time.                              | Transcript + Spanish translation streamed together.          |
| **Real-time <br> two-way translation** | Transcribes speech in any language and translates English ↔ Spanish in real time. Spanish → English, English → Spanish. | Transcript + bidirectional translations streamed together.   |
| **Transcribe <br> file from URL**     | Transcribes an audio file directly from a public URL.                                                        | Transcript printed to console.                               |
| **Transcribe <br> local file**        | Uploads and transcribes an audio file from your computer.                                                    | Transcript printed to console.                               |


<details open>
<summary><b>Python</b></summary>

```sh
# Set up environment
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Real-time examples
python soniox_realtime.py --audio_path ../assets/coffee_shop.mp3
python soniox_realtime.py --audio_path ../assets/coffee_shop.pcm_s16le --audio_format pcm_s16le
python soniox_realtime.py --audio_path ../assets/coffee_shop.mp3 --translation one_way
python soniox_realtime.py --audio_path ../assets/two_way_translation.mp3 --translation two_way

# Async examples
python soniox_async.py --audio_url "https://soniox.com/media/examples/coffee_shop.mp3"
python soniox_async.py --audio_path ../assets/coffee_shop.mp3
python soniox_async.py --delete_all_files
python soniox_async.py --delete_all_transcriptions
```
</details>

<details>
<summary><b>Node.js</b></summary>

```sh
# Set up environment
cd nodejs
npm install

# Real-time examples
node soniox_realtime.js --audio_path ../assets/coffee_shop.mp3
node soniox_realtime.js --audio_path ../assets/coffee_shop.pcm_s16le --audio_format pcm_s16le
node soniox_realtime.js --audio_path ../assets/coffee_shop.mp3 --translation one_way
node soniox_realtime.js --audio_path ../assets/two_way_translation.mp3 --translation two_way

# Async examples
node soniox_async.js --audio_url "https://soniox.com/media/examples/coffee_shop.mp3"
node soniox_async.js --audio_path ../assets/coffee_shop.mp3
node soniox_async.js --delete_all_files
node soniox_async.js --delete_all_transcriptions
```
