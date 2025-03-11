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
    // All final tokens will be collected in this list.
    let all_final_tokens = [];

    const onDataHandler = async (result) => {
        if (!result) {
            return;
        }

        const final_tokens = [];
        const nonfinal_tokens = [];

        for (word of result.words) {
            if (word.is_final) {
                final_tokens.push(word.text);
            } else {
                nonfinal_tokens.push(word.text);
            }
        }

        // Append current final tokens to all final tokens.
        all_final_tokens = all_final_tokens.concat(final_tokens);

        console.log(`Final: ${all_final_tokens.join("")}`);
        console.log(`Non-final: ${nonfinal_tokens.join("")}`);
        console.log("-----");
    };

    const onEndHandler = (error) => {
        if (error) {
            console.log(`Transcription error: ${error}`);
        }
    };

    // transcribeStream returns an object with ".writeAsync()" and ".end()"
    // methods - use them to send data and end stream when done.
    const stream = speechClient.transcribeStream(
        {
            model: "en_v2_lowlatency",
            include_nonfinal: true
        },
        onDataHandler,
        onEndHandler
    );

    // Open file as stream.
    const CHUNK_SIZE = 1024;
    const streamSource = fs.createReadStream(
        "../test_data/test_audio_long.flac",
        {
            highWaterMark: CHUNK_SIZE,
        }
    );

    // Simulate data streaming
    for await (const audioChunk of streamSource) {
        await stream.writeAsync(audioChunk);
    }
    stream.end();
})();
