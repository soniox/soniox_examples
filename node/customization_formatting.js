const { SpeechClient } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  // SpeechContextEntry phrase can contain a mapping.
  const speech_context = {
    entries: [
      {
        phrases: ["youtube => YouTuBe"],
        boost: 5,
      },
      {
        phrases: ["twenty three and me => 23andMe"],
        boost: 10,
      }
    ]
  };

  // Pass SpeechContext with transcribe request.
  const result = await speechClient.transcribeFileShort(
    "../test_data/youtube_23andme.flac",
    { speech_context: speech_context }
  );

  console.log(result.words.map((word) => word.text).join(" "));
})();
