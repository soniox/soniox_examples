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

int poll_until_complete(const char *auth_header, const char *api_base, const char *transcription_id) {
    char url[512];
    CURL *curl;
    CURLcode res_code;
    struct curl_slist *headers = NULL;
    char *res = NULL;
    long http_status;

    while (1) {
        curl = curl_easy_init();
        if (!curl) {
            fprintf(stderr, "Failed to initialize CURL\n");
            return 1;
        }
        snprintf(url, sizeof(url), "%s/v1/transcriptions/%s", api_base, transcription_id);
        curl_easy_setopt(curl, CURLOPT_URL, url);
        headers = NULL;
        headers = curl_slist_append(headers, auth_header);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        res = NULL;
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
        res_code = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
        if (res_code != CURLE_OK || http_status != 200) {
            fprintf(stderr, "Failed to get transcription: %s\n", res ? res : curl_easy_strerror(res_code));
            curl_easy_cleanup(curl);
            curl_slist_free_all(headers);
            free(res);
            return 1;
        }
        struct json_object *status_json = json_tokener_parse(res);
        char *status = strdup(json_object_get_string(json_object_object_get(status_json, "status")));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(res);

        if (strcmp(status, "completed") == 0) {
            return 0;
        } else if (strcmp(status, "error") == 0) {
            free(status);
            fprintf(stderr, "Transcription error: %s\n", json_object_get_string(json_object_object_get(status_json, "error_message")));

            return 1;
        }
    }
}

int main() {
    // Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
    const char *api_key = getenv("SONIOX_API_KEY");
    if (!api_key) {
        fprintf(stderr, "Environment variable SONIOX_API_KEY is not set\n");
        return 1;
    }
    const char *api_base = "https://api.soniox.com";
    const char *file_to_transcribe = "coffee_shop.mp3";

    char auth_header[256];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", api_key);
    char url[512];
    CURL *curl;
    CURLcode res_code;
    struct curl_slist *headers = NULL;
    char *res = NULL;
    long http_status;

    printf("Starting file upload...\n");

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }
    curl_mime *form = curl_mime_init(curl);
    curl_mimepart *field = curl_mime_addpart(form);
    curl_mime_name(field, "file");
    curl_mime_filedata(field, file_to_transcribe);
    snprintf(url, sizeof(url), "%s/v1/files", api_base);
    curl_easy_setopt(curl, CURLOPT_URL, url);
    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_MIMEPOST, form);  // Use CURLOPT_MIMEPOST
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    res = NULL;
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
    res_code = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
    if (res_code != CURLE_OK || http_status != 201) {
        fprintf(stderr, "File upload failed: %s\n", res ? res : curl_easy_strerror(res_code));
        curl_easy_cleanup(curl);
        curl_mime_free(form);
        curl_slist_free_all(headers);
        free(res);
        return 1;
    }
    struct json_object *file_json = json_tokener_parse(res);
    const char *file_id = json_object_get_string(json_object_object_get(file_json, "id"));
    curl_easy_cleanup(curl);
    curl_mime_free(form);
    curl_slist_free_all(headers);
    free(res);

    printf("Starting transcription...\n");

    struct json_object *create_transcription_data = json_object_new_object();
    json_object_object_add(create_transcription_data, "file_id", json_object_new_string(file_id));
    json_object_object_add(create_transcription_data, "model", json_object_new_string("stt-async-preview"));
    json_object *language_hints_array = json_object_new_array();
    json_object_array_add(language_hints_array, json_object_new_string("en"));
    json_object_array_add(language_hints_array, json_object_new_string("es"));
    json_object_object_add(create_transcription_data, "language_hints", language_hints_array);

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }
    snprintf(url, sizeof(url), "%s/v1/transcriptions", api_base);
    curl_easy_setopt(curl, CURLOPT_URL, url);
    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_object_to_json_string(create_transcription_data));
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    res = NULL;
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
    res_code = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
    if (res_code != CURLE_OK || http_status != 201) {
        fprintf(stderr, "Failed to create transcription: %s\n", res ? res : curl_easy_strerror(res_code));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(res);
        return 1;
    }
    struct json_object *transcription_json = json_tokener_parse(res);
    const char *transcription_id = json_object_get_string(json_object_object_get(transcription_json, "id"));
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    free(res);

    printf("Transcription ID: %s\n", transcription_id);

    int code;
    if ((code = poll_until_complete(auth_header, api_base, transcription_id))) {
        return code;
    }

    // Get the transcript text

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }
    snprintf(url, sizeof(url), "%s/v1/transcriptions/%s/transcript", api_base, transcription_id);
    curl_easy_setopt(curl, CURLOPT_URL, url);
    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    res = NULL;
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
    res_code = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
    if (res_code != CURLE_OK || http_status != 200) {
        fprintf(stderr, "Failed to get transcript: %s\n", res ? res : curl_easy_strerror(res_code));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(res);
        return 1;
    }
    struct json_object *transcript_json = json_tokener_parse(res);
    const char *transcript_text = json_object_get_string(json_object_object_get(transcript_json, "text"));

    printf("Transcript:\n%s\n", transcript_text);

    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    free(res);

    // Delete the transcription

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }
    snprintf(url, sizeof(url), "%s/v1/transcriptions/%s", api_base, transcription_id);
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    res = NULL;
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
    res_code = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
    if (res_code != CURLE_OK || http_status != 204) {
        fprintf(stderr, "Failed to delete transcription: %s\n", res ? res : curl_easy_strerror(res_code));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(res);
        return 1;
    }
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    if (res) {
        free(res);
    }

    // Delete the file

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }
    snprintf(url, sizeof(url), "%s/v1/files/%s", api_base, file_id);
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    headers = NULL;
    headers = curl_slist_append(headers, auth_header);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    res = NULL;
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);
    res_code = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_status);
    if (res_code != CURLE_OK || http_status != 204) {
        fprintf(stderr, "Failed to delete file: %s\n", res ? res : curl_easy_strerror(res_code));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        free(res);
        return 1;
    }
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    if (res) {
        free(res);
    }

    return 0;
}
