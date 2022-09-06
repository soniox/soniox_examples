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
    console.log(result.words.map((word) => `${word.text}/${word.speaker}`).join(" "));
  };

  const onEndHandler = (error) => {
    if (error) {
      console.log(error);
    }
  };

  // transcribeStream returns object with ".writeAsync()" and ".end()" methods
  // use them to send data and end stream when done.
  const stream = speechClient.transcribeStream(
    { 
      enable_streaming_speaker_diarization: true,
      include_nonfinal: true
    },
    onDataHandler,
    onEndHandler
  );

    // Here we simulate the stream by reading a file in small chunks.
    const CHUNK_SIZE = 1024;
  const readable = fs.createReadStream("../test_data/test_audio_sd.flac", {
    highWaterMark: CHUNK_SIZE,
  });

  // Simulate data streaming
  for await (const chunk of readable) {
    stream.writeAsync(chunk);
  }

  stream.end();
})();
