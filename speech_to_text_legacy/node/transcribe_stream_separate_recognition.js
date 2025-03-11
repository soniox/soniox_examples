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
    console.log(
      `Channel ${result.channel}: ${result.words.map((word) => word.text).join("")}`
    );
  };

  const onEndHandler = (error) => {
    if (error) {
      console.log(`Transcription error: ${error}`);
    }
  };

  // transcribeStream returns object with ".writeAsync()" and ".end()" methods
  // use them to send data and end stream when done.
  const stream = speechClient.transcribeStream(
    {
      model: "en_v2_lowlatency",
      include_nonfinal: true,
      num_audio_channels: 2,
      enable_separate_recognition_per_channel: true,
    },
    onDataHandler,
    onEndHandler
  );

  const CHUNK_SIZE = 1024;
  const streamSource = fs.createReadStream(
    "../test_data/test_audio_multi_channel.flac",
    {
      highWaterMark: CHUNK_SIZE,
    }
  );

  // Simulate data streaming
  for await (const audioChunk of streamSource) {
    await stream.writeAsync(audioChunk);
  }

  stream.end();
})();
