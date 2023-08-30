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
        let speaker_num_to_name = {}
        for (const entry of result.speakers) {
            speaker_num_to_name[entry.speaker] = entry.name
        }

        const getName = (speaker) => {
            if (speaker in speaker_num_to_name) {
                return speaker_num_to_name[speaker]
            } else {
                return "unknown"
            }
        };

        console.log(result.words.map((word) =>
            `'${word.text}'/${word.speaker}(${getName(word.speaker)})`).join(" ")
        );
    };

    const onEndHandler = (error) => {
        if (error) {
            console.log(`Transcription error: ${error}`);
        }
    };

    // transcribeStream() returns object with ".writeAsync()" and ".end()" methods.
    // Use them to send data and end the stream when done.
    const stream = speechClient.transcribeStream(
        {
            model: "en_v2_lowlatency",
            include_nonfinal: true,
            enable_streaming_speaker_diarization: true,
            enable_speaker_identification: true,
            cand_speaker_names: ["John", "Judy"]
        },
        onDataHandler,
        onEndHandler
    );

    // Here we simulate the stream by reading a file in small chunks.
    const CHUNK_SIZE = 1024;
    const readable = fs.createReadStream("../test_data/test_audio_sd.flac", {
        highWaterMark: CHUNK_SIZE,
    });

    for await (const chunk of readable) {
        await stream.writeAsync(chunk);
    }

    stream.end();
})();
