const fs = require("fs");
const { SpeechClient } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  const onDataHandler = async (result) => {
    let speaker = "";
    let sentence = "";

    for (const word of result.words) {
      if (word.speaker !== speaker) {
        console.log(sentence);
        speaker = word.speaker;
        sentence = `Speaker ${speaker}: ${word.text}`;
      } else {
        sentence += ` ${word.text}`;
      }
    }

    console.log(sentence);
  };

  const onEndHandler = (error) => {
    if (error) {
      console.log(`Transcription error: ${error}`)
    }
  };

  // transcribeStream returns object with ".writeAsync()" and ".end()" methods
  // use them to send data and end stream when done.
  const stream = speechClient.transcribeStream(
    {
      enable_global_speaker_diarization: true,
      min_num_speakers: 1,
      max_num_speakers: 6,
    },
    onDataHandler,
    onEndHandler
  );

  const CHUNK_SIZE = 1024;
  const readable = fs.createReadStream("../test_data/test_audio_sd.flac", {
    highWaterMark: CHUNK_SIZE,
  });

  // Simulate data streaming
  for await (const chunk of readable) {
    await stream.writeAsync(chunk);
  }

  stream.end();
})();
