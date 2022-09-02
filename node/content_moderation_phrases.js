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
    "../test_data/test_audio.flac",
    {
      content_moderation_phrases: ["two years", "homesick"],
    }
  );

  console.log(`Words: ${result.words.map((word) => word.text).join(" ")}`);
})();
