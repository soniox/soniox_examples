const { SpeechClient } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  const channel_results = await speechClient.transcribeFileShort(
    "../test_data/test_audio_multi_channel.flac",
    {
      num_audio_channels: 2,
      enable_separate_recognition_per_channel: true,
    }
  );

  for (const result of channel_results) {
    console.log(
      `Channel ${result.channel}: ${result.words
        .map((word) => word.text)
        .join(" ")}`
    );
  }
})();
