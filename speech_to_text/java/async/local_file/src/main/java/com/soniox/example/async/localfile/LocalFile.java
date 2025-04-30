package com.soniox.example.async.localfile;

import java.io.File;
import java.io.IOException;

import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;

public class LocalFile {
    private static void pollUntilComplete(CloseableHttpClient client, String apiBase,
            String apiKey, String transcriptionId) throws Exception {
        while (true) {
            HttpGet transcriptionReq = new HttpGet(apiBase + "/v1/transcriptions/" + transcriptionId);
            transcriptionReq.setHeader("Authorization", "Bearer " + apiKey);
            HttpResponse res = client.execute(transcriptionReq);
            if (res.getStatusLine().getStatusCode() != 200) {
                throw new RuntimeException("Failed to get transcription: " + EntityUtils.toString(res.getEntity()));
            }
            JSONObject transcription = new JSONObject(EntityUtils.toString(res.getEntity()));
            if ("completed".equals(transcription.getString("status"))) {
                return;
            } else if ("error".equals(transcription.getString("status"))) {
                throw new RuntimeException("Transcription error: " + transcription.getString("error_message"));
            }
            Thread.sleep(1000);
        }
    }

    public static void main(String[] args) throws Exception {
        // Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
        String apiBase = "https://api.soniox.com";
        String apiKey = System.getenv("SONIOX_API_KEY");
        String fileToTranscribe = "../../coffee_shop.mp3";

        try (CloseableHttpClient client = HttpClients.createDefault()) {
            System.out.println("Starting file upload...");

            File audioFile = new File(fileToTranscribe);
            HttpPost uploadFileReq = new HttpPost(apiBase + "/v1/files");
            uploadFileReq.setHeader("Authorization", "Bearer " + apiKey);
            uploadFileReq.setEntity(MultipartEntityBuilder.create()
                    .addBinaryBody("file", audioFile, ContentType.DEFAULT_BINARY, audioFile.getName())
                    .build());
            HttpResponse res = client.execute(uploadFileReq);
            if (res.getStatusLine().getStatusCode() != 201) {
                throw new RuntimeException("File upload failed: " + EntityUtils.toString(res.getEntity()));
            }
            JSONObject file = new JSONObject(EntityUtils.toString(res.getEntity()));

            System.out.println("Starting transcription...");

            JSONObject createTranscriptionBody = new JSONObject();
            createTranscriptionBody.put("file_id", file.getString("id"));
            createTranscriptionBody.put("model", "stt-async-preview");
            createTranscriptionBody.put("language_hints", new String[]{"en", "es"});
            HttpPost createTranscriptionReq = new HttpPost(apiBase + "/v1/transcriptions");
            createTranscriptionReq.setHeader("Authorization", "Bearer " + apiKey);
            createTranscriptionReq.setHeader("Content-Type", "application/json");
            createTranscriptionReq.setEntity(new StringEntity(createTranscriptionBody.toString(), ContentType.APPLICATION_JSON));
            res = client.execute(createTranscriptionReq);
            if (res.getStatusLine().getStatusCode() != 201) {
                throw new RuntimeException("Failed to create transcription: " + EntityUtils.toString(res.getEntity()));
            }
            JSONObject transcription = new JSONObject(EntityUtils.toString(res.getEntity()));
            String transcriptionId = transcription.getString("id");

            System.out.println("Transcription ID: " + transcriptionId);

            pollUntilComplete(client, apiBase, apiKey, transcriptionId);

            // Get the transcript text
            HttpGet transcriptReq = new HttpGet(apiBase + "/v1/transcriptions/" + transcription.getString("id") + "/transcript");
            transcriptReq.setHeader("Authorization", "Bearer " + apiKey);
            res = client.execute(transcriptReq);
            if (res.getStatusLine().getStatusCode() != 200) {
                throw new RuntimeException("Failed to get transcript: " +
                        EntityUtils.toString(res.getEntity()));
            }
            JSONObject transcript = new JSONObject(EntityUtils.toString(res.getEntity()));
            System.out.println("Transcript:");
            System.out.println(transcript.getString("text"));

            // Delete the transcription
            HttpDelete deleteReq = new HttpDelete(apiBase + "/v1/transcriptions/" + transcription.getString("id"));
            deleteReq.setHeader("Authorization", "Bearer " + apiKey);
            res = client.execute(deleteReq);
            if (res.getStatusLine().getStatusCode() != 204) {
                throw new RuntimeException("Failed to delete transcription: " +
                        EntityUtils.toString(res.getEntity()));
            }

            // Delete the file
            deleteReq = new HttpDelete(apiBase + "/v1/files/" + file.getString("id"));
            deleteReq.setHeader("Authorization", "Bearer " + apiKey);
            res = client.execute(deleteReq);
            if (res.getStatusLine().getStatusCode() != 204) {
                throw new RuntimeException("Failed to delete file: " +
                        EntityUtils.toString(res.getEntity()));
            }
        }
    }
}
