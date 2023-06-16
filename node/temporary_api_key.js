const { SpeechClient, timestampToDate } = require("@soniox/soniox-node");

/**
 * Set your Soniox Cloud API key:
 * from command line: export SONIOX_API_KEY=<YOUR-API-KEY>
 * or
 * pass config object: new SpeechClient({ api_key: "<YOUR-API-KEY>" })
 */
const speechClient = new SpeechClient();

(async function () {
    const response = await speechClient.createTemporaryApiKey({
        usage_type: "transcribe_websocket",
        client_request_reference: "test_reference",
    });

    console.log(`API key: ${response.key}`);
    console.log(`Expires: ${timestampToDate(response.expires_datetime)}`);
})();
