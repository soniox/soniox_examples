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
    const result = await speechClient.transcribeFileShort(
        "../test_data/test_audio_sd.flac",
        {
            model: "en_v2",
            enable_global_speaker_diarization: true,
            min_num_speakers: 1,
            max_num_speakers: 6,
            enable_speaker_identification: true,
            cand_speaker_names: ["John", "Judy"]
        }
    );

    // Build map from speaker number to name.
    let speaker_num_to_name = {}
    for (const entry of result.speakers) {
        speaker_num_to_name[entry.speaker] = entry.name;
    }

    // Print results with each speaker segment on its own line.

    let speaker = 0;
    let line = "";

    for (const word of result.words) {
        if (word.speaker !== speaker) {
            if (line.length > 0) {
                console.log(line);
            }

            speaker = word.speaker;

            let speaker_name;
            if (speaker in speaker_num_to_name) {
                speaker_name = speaker_num_to_name[speaker]
            } else {
                speaker_name = "unknown"
            }

            line = `Speaker ${speaker} (${speaker_name}): `;

            if (word.text == " ") {
                // Avoid printing leading space at speaker change.
                continue;
            }
        }

        line += word.text;
    }

    console.log(line);
})();
