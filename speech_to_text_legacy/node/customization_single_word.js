const { SpeechClient } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  // Create SpeechContext.
  const speech_context = {
    entries: [
      {
        phrases: ["acetylcarnitine"],
        boost: 15,
      },
      {
        phrases: ["Zestoretic"],
        boost: 15,
      }
    ]
  };

  // Pass SpeechContext with transcribe request.
  const result = await speechClient.transcribeFileShort(
    "../test_data/acetylcarnitine_zestoretic.flac",
    {
      model: "en_v2",
      speech_context: speech_context,
    }
  );

  console.log(result.words.map((word) => word.text).join(""));
})();
