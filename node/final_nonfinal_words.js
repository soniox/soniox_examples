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
  // All final words will be collected in this list.
  let all_final_words = [];

  const onDataHandler = async (result) => {
    if (!result) {
      return;
    }

    const final_words = [];
    const non_final_words = [];

    for (word of result.words) {
      if (word.is_final) {
        final_words.push(word.text);
      } else {
        non_final_words.push(word.text);
      }
    }

    // Append current final words to all final words.
    all_final_words = all_final_words.concat(final_words);

    console.log(`Final: ${all_final_words.join(" ")}`);
    console.log(`Non-final: ${non_final_words.join(" ")}`);
    console.log("-----");
  };

  const onEndHandler = (error) => {
    if (error) {
      console.log(`Transcription error: ${error}`);
    }
  };

  // transcribeStream returns object with ".writeAsync()" and ".end()" methods
  // use them to send data and end stream when done.
  const stream = speechClient.transcribeStream(
    { include_nonfinal: true },
    onDataHandler,
    onEndHandler
  );

  const CHUNK_SIZE = 1024;
  const streamSource = fs.createReadStream(
    "../test_data/test_audio_long.flac",
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
