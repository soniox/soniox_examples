#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>
#include <json-c/json.h>

size_t write_callback(void *ptr, size_t size, size_t nmemb, void *userdata) {
    size_t real_size = size * nmemb;
    char **response_ptr = (char **)userdata;

    *response_ptr = strndup(ptr, real_size);

    return real_size;
}

int main() {
    const char *api_base = "https://api.soniox.com";
    const char *api_key = getenv("SONIOX_API_KEY");
    if (!api_key) {
        fprintf(stderr, "Environment variable SONIOX_API_KEY is not set\n");
        return 1;
    }

    char auth_header[256];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", api_key);

    char url[512];

    CURL *curl;
    CURLcode res;

    struct curl_slist *headers;
    char *response;
    long http_status;

    // 1. Start a new transcription session by sending the audio URL to the API
    printf("Starting transcription...\n");
    snprintf(url, sizeof(url), "%s/v1/transcriptions", api_base);

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }

    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    headers = curl_slist_append(headers, "Content-Type: application/json");

    struct json_object *create_transcription_data = json_object_new_object();
    json_object_object_add(create_transcription_data, "audio_url", json_object_new_string("https://soniox.com/media/examples/coffee_shop.mp3"));
    json_object_object_add(create_transcription_data, "model", json_object_new_string("stt-async-preview"));

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_object_to_json_string(create_transcription_data));
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    res = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);

    if (res != CURLE_OK || http_status != 201) {
        fprintf(stderr, "Failed to create transcription: %s\n", response ? response : curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(response);
        return 1;
    }

    struct json_object *transcription_json = json_tokener_parse(response);
    const char *transcription_id = json_object_get_string(json_object_object_get(transcription_json, "id"));
    printf("Transcription started with ID: %s\n", transcription_id);

    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    free(response);

    // 2. Poll the transcription endpoint until the status is 'completed'
    while (1) {
        snprintf(url, sizeof(url), "%s/v1/transcriptions/%s", api_base, transcription_id);

        curl = curl_easy_init();
        if (!curl) {
            fprintf(stderr, "Failed to initialize CURL\n");
            return 1;
        }

        headers = NULL;
        headers = curl_slist_append(headers, auth_header);

        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);

        if (res != CURLE_OK || http_status != 200) {
            fprintf(stderr, "Failed to get transcription: %s\n", response ? response : curl_easy_strerror(res));
            curl_easy_cleanup(curl);
            curl_slist_free_all(headers);
            free(response);
            return 1;
        }

        struct json_object *status_json = json_tokener_parse(response);
        char *status = strdup(json_object_get_string(json_object_object_get(status_json, "status")));

        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(response);

        if (strcmp(status, "error") == 0) {
            free(status);
            fprintf(stderr, "Transcription error: %s\n", json_object_get_string(json_object_object_get(status_json, "error_message")));

            return 1;
        } else if (strcmp(status, "completed") == 0) {
            break;
        }
    }

    // 3. Retrieve the final transcript once transcription is completed
    snprintf(url, sizeof(url), "%s/v1/transcriptions/%s/transcript", api_base, transcription_id);

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }

    headers = NULL;
    headers = curl_slist_append(headers, auth_header);

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    res = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);

    if (res != CURLE_OK || http_status != 200) {
        fprintf(stderr, "Failed to get transcript: %s\n", response ? response : curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(response);
        return 1;
    }

    struct json_object *transcript_json = json_tokener_parse(response);
    const char *transcript_text = json_object_get_string(json_object_object_get(transcript_json, "text"));

    printf("Transcript:\n%s\n", transcript_text);

    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    free(response);

    return 0;
}
