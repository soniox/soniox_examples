require("dotenv").config();

const http = require("http");
const express = require("express");
const fetch = require("node-fetch");
const path = require("path");
const fs = require("fs").promises;

const app = express();

app.use("/templates", express.static(path.join(__dirname, "templates")));

app.get("/", async (req, res) => {
  const index = await fs.readFile(
    path.join(__dirname, "templates/index.html"),
    "utf8"
  );
  res.send(index);
});

app.get("/temporary-api-key", async (req, res) => {
  try {
    const response = await fetch(
      "https://api.soniox.com/v1/auth/temporary-api-key",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.SONIOX_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          usage_type: "transcribe_websocket",
          expires_in_seconds: 60,
        }),
      }
    );

    if (!response.ok) {
      throw await response.json();
    }

    const temporaryApiKeyData = await response.json();

    res.json(temporaryApiKeyData);
  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: `Server failed to obtain temporary api key: ${JSON.stringify(error)}`,
    });
  }
});

// Create HTTP server with Express
const server = http.createServer(app);

server.listen(process.env.PORT, () => {
  console.log(
    `HTTP server listening on http://0.0.0.0:${process.env.PORT}`
  );
});
