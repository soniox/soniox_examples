# Browser direct stream example

This example demonstrates how to set up a Node.js server to serve an HTML page
that loads Soniox Web Library, authenticates using **GET temporary API key**
endpoint and starts a real-time transcription from browser client **directly**
to Soniox Speech-to-Text WebSocket API.

This approach minimizes the latency.

### Run Node.js server

Copy `.env.example` to `.env` and add your Soniox API key.

Install dependencies:

```sh
npm install
```

Start the server:

```sh
npm run start
```
