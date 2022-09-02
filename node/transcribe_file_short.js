const { SpeechClient } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  const result = await speechClient.transcribeFileShort(
    "../test_data/test_audio.flac"
  );

  for (const word of result.words) {
    console.log(`${word.text} ${word.start_ms} ${word.duration_ms}`);
  }
})();
