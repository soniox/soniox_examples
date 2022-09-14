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
  const words = [];

  const onDataHandler = async (result) => {
    for (const word of result.words) {
        words.push(word);
        if (word.text == "<end>") {
            console.log(words.map((word) => word.text).join(" "));
            words.length = 0;
        }
    }
  };

  const onEndHandler = (error) => {
    if (error) {
        console.log("Error!", error);
    }
  };

  const stream = speechClient.transcribeStream(
    {
        model: "precision_ivr",
        enable_endpoint_detection: true,
        include_nonfinal: false,
    },
    onDataHandler,
    onEndHandler
  );

  const CHUNK_SIZE = 1024;
  const readable = fs.createReadStream("../test_data/test_audio_ivr.flac", {
    highWaterMark: CHUNK_SIZE,
  });

  for await (const chunk of readable) {
    await stream.writeAsync(chunk);
  }

  stream.end();
})();
