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
    let speaker = "";
    let speaker_name = "";
    let sentence = "";
    let speaker_num_to_name = {}
    for (const entry of result.speakers) {
      speaker_num_to_name[entry.speaker] = entry.name
    }

    for (const word of result.words) {
      if (word.speaker !== speaker) {
        speaker = word.speaker;
        if (speaker in speaker_num_to_name) {
          speaker_name = speaker_num_to_name[speaker]
        } else {
          speaker_name = "unknown"
        }
        console.log(sentence);
        sentence = `Speaker ${speaker} (${speaker_name}): ${word.text}`;
      } else {
        sentence += ` ${word.text}`;
      }
    }

    console.log(sentence);
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
      enable_global_speaker_diarization: true,
      min_num_speakers: 1,
      max_num_speakers: 6,
      enable_speaker_identification: true,
      cand_speaker_names: ["John", "Judy"]
    },
    onDataHandler,
    onEndHandler
  );

  const CHUNK_SIZE = 1024;
  const readable = fs.createReadStream("../test_data/test_audio_sd.flac", {
    highWaterMark: CHUNK_SIZE,
  });

  // Simulate data streaming
  for await (const chunk of readable) {
    await stream.writeAsync(chunk);
  }

  stream.end();
})();
