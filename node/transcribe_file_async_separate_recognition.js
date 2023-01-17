const { SpeechClient } = require("@soniox/soniox-node");
const { asyncSleep } = require("./utils");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
  console.log("Uploading file.");
  const file_id = await speechClient.transcribeFileAsync(
    "../test_data/test_audio_multi_channel.flac",
    "test", // reference_name
    {
      num_audio_channels: 2,
      enable_separate_recognition_per_channel: true,
    }
  );
  console.log(`File ID: ${file_id}`);

  let status;
  let error_message;

  while (true) {
    console.log("Calling getTranscribeAsyncStatus.");
    const response = await speechClient.getTranscribeAsyncStatus(file_id);
    status = response.status;
    error_message = response.error_message;

    console.log(`Status: ${status}`);

    if (status === "COMPLETED" || status === "FAILED") {
      break;
    }

    await asyncSleep(2000);
  }

  if (status === "COMPLETED") {
    const channel_results = await speechClient.getTranscribeAsyncResult(
      file_id
    );
    for (result of channel_results) {
      console.log(
        `Channel ${result.channel}: ${result.words
          .map((word) => word.text)
          .join(" ")}`
      );
    }
  } else {
    console.log(`Transcription failed with error: ${error_message}`);
  }

  console.log("Calling deleteTranscribeAsyncFile.");
  await speechClient.deleteTranscribeAsyncFile(file_id);
})();
