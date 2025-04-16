# Browser proxy stream example

This example demonstrates how to set up a Node.js server as a WebSocket proxy to
stream microphone audio from a browser client to the Soniox Speech-to-Text
WebSocket API.

This approach gives you more control and allows processing text on the backend.

### Run Node.js server

Go to `server` folder.

Copy `.env.example` to `.env` and add your Soniox API key.

Install dependencies:

```sh
npm install
```

Start the server:

```sh
npm run start
```

### Run client

Go to `client` folder.

Start an HTTP server to serve `index.html` file.

```sh
npx serve
```

or use a HTTP server of your choice to serve it.

Open http://localhost:3000 in your browser. Click the Start button, approve
microphone audio permissions and start talking.
