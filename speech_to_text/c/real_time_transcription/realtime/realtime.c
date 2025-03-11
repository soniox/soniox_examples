#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>

#include <libwebsockets.h>
#include <json-c/json.h>

#define AUDIO_CHUNK_SIZE 3840

typedef struct {
    struct lws *wsi;
    struct lws_context *context;

    pthread_mutex_t mutex;

    bool closed;
    bool write_start;
    bool write_audio;
    bool write_eof;

    unsigned char audio_buffer[AUDIO_CHUNK_SIZE];
    size_t audio_buffer_len;

    pthread_t read_audio_thread;
    bool read_audio_thread_started;
} client_data_t;

void *read_audio_thread(void *arg) {
    client_data_t *data = (client_data_t *)arg;

    FILE *audio_file = fopen("coffee_shop.pcm_s16le", "rb");
    if (!audio_file) {
        printf("Failed to open audio file\n");
        return NULL;
    }

    unsigned char audio_chunk[AUDIO_CHUNK_SIZE];
    size_t bytes_read;

    printf("Transcription started.\n");
    while ((bytes_read = fread(audio_chunk, 1, AUDIO_CHUNK_SIZE, audio_file)) > 0) {
        pthread_mutex_lock(&data->mutex);

        if (data->closed) {
            fclose(audio_file);

            pthread_mutex_unlock(&data->mutex);

            return NULL;
        }

        memcpy(data->audio_buffer, audio_chunk, bytes_read);
        data->audio_buffer_len = bytes_read;
        data->write_audio = true;

        lws_callback_on_writable(data->wsi);
        lws_cancel_service(data->context);

        pthread_mutex_unlock(&data->mutex);

        // Sleep for 120 ms
        usleep(120000);
    }

    pthread_mutex_lock(&data->mutex);

    if (!data->closed) {
        data->write_eof = true;

        lws_callback_on_writable(data->wsi);
        lws_cancel_service(data->context);
    }

    pthread_mutex_unlock(&data->mutex);

    fclose(audio_file);

    return NULL;
}

int callback(struct lws *wsi, enum lws_callback_reasons reason,
             void *user, void *in, size_t len) {
    client_data_t *data = (client_data_t *)user;

    char *msg;

    switch (reason) {
        case LWS_CALLBACK_CLIENT_ESTABLISHED:
            data->write_start = true;

            lws_callback_on_writable(wsi);

            break;

        case LWS_CALLBACK_CLIENT_WRITEABLE:
            pthread_mutex_lock(&data->mutex);

            if (data->write_start) {
                // Send start request

                struct json_object *start_req = json_object_new_object();
                json_object_object_add(start_req, "api_key", json_object_new_string(getenv("SONIOX_API_KEY")));
                json_object_object_add(start_req, "audio_format", json_object_new_string("pcm_s16le"));
                json_object_object_add(start_req, "sample_rate", json_object_new_int(16000));
                json_object_object_add(start_req, "num_channels", json_object_new_int(1));
                json_object_object_add(start_req, "model", json_object_new_string("stt-rt-preview"));
                json_object_object_add(start_req, "language_hints", json_object_new_array());

                const char *start_message = json_object_to_json_string(start_req);
                size_t start_message_len = strlen(start_message);

                char *buf = malloc(LWS_PRE + start_message_len);
                strcpy(&buf[LWS_PRE], start_message);

                json_object_put(start_req);

                int n = lws_write(wsi, (unsigned char *)buf + LWS_PRE, start_message_len, LWS_WRITE_TEXT);

                free(buf);

                if (n < (int)start_message_len) {
                    pthread_mutex_unlock(&data->mutex);

                    return -1;
                }

                // Start audio thread

                pthread_create(&data->read_audio_thread, NULL, read_audio_thread, data);

                data->read_audio_thread_started = true;

                data->write_start = false;
            }

            if (data->write_audio) {
                // Send audio data

                unsigned char audio_buf[LWS_PRE + AUDIO_CHUNK_SIZE];

                memcpy(&audio_buf[LWS_PRE], data->audio_buffer, data->audio_buffer_len);

                int n = lws_write(wsi, &audio_buf[LWS_PRE], data->audio_buffer_len, LWS_WRITE_BINARY);
                if (n < (int)data->audio_buffer_len)  {
                    printf("Failed to write audio\n");
                }

                data->write_audio = false;
            }

            if (data->write_eof) {
                // Send end of file (empty message)
                unsigned char eof_buf[LWS_PRE];

                int n = lws_write(wsi, &eof_buf[LWS_PRE], 0, LWS_WRITE_TEXT);
                if (n < 0) {
                    printf("Failed to write EOF\n");
                }

                data->write_eof = false;
            }

            pthread_mutex_unlock(&data->mutex);

            break;

        case LWS_CALLBACK_CLIENT_RECEIVE:
            // Receive and process text messages
            msg = malloc(len + 1);
            memcpy(msg, in, len);
            msg[len] = '\0';

            struct json_object *res = json_tokener_parse(msg);

            // Handle any possible transcription error
            struct json_object *error_code_obj;
            if (json_object_object_get_ex(res, "error_code", &error_code_obj)) {
                struct json_object *error_message_obj;
                if (json_object_object_get_ex(res, "error_message", &error_message_obj)) {
                    printf("Error %d: %s\n",
                        json_object_get_int(error_code_obj),
                        json_object_get_string(error_message_obj));
                }
                lws_close_reason(wsi, LWS_CLOSE_STATUS_NORMAL, NULL, 0);
                lws_cancel_service(data->context);
                json_object_put(res);
                free(msg);
                return -1;
            }

            // Process tokens
            struct json_object *tokens_array;
            if (json_object_object_get_ex(res, "tokens", &tokens_array) &&
                json_object_get_type(tokens_array) == json_type_array) {
                for (size_t i = 0; i < json_object_array_length(tokens_array); i++) {
                    struct json_object *token_obj = json_object_array_get_idx(tokens_array, i);
                    struct json_object *text_obj;
                    if (json_object_object_get_ex(token_obj, "text", &text_obj)) {
                        const char *text = json_object_get_string(text_obj);
                        if (text && strlen(text) > 0) {
                            printf("%s", text);
                            fflush(stdout);
                        }
                    }
                }
            }

            // Handle finished
            struct json_object *finished_obj;
            if (json_object_object_get_ex(res, "finished", &finished_obj)) {
                if (json_object_get_boolean(finished_obj)) {
                    // Close the websocket
                    lws_close_reason(wsi, LWS_CLOSE_STATUS_NORMAL, NULL, 0);
                    lws_cancel_service(data->context);
                }
            }

            json_object_put(res);
            free(msg);

            break;

        case LWS_CALLBACK_CLIENT_CONNECTION_ERROR:
            printf("Connection error: %s\n", in ? (char *)in : "(null)");

            pthread_mutex_lock(&data->mutex);
            data->closed = true;
            pthread_mutex_unlock(&data->mutex);

            break;

        case LWS_CALLBACK_CLIENT_CLOSED:
            printf("\nTranscription done.\n");
            pthread_mutex_lock(&data->mutex);
            data->closed = true;
            pthread_mutex_unlock(&data->mutex);

            if (data->read_audio_thread_started) {
                pthread_join(data->read_audio_thread, NULL);
            }

            break;

        default:
            break;
    }

    return 0;
}

int main() {
    struct lws_context_creation_info info;
    struct lws_context *context;
    struct lws_client_connect_info connect_info;
    client_data_t data = {0};

    pthread_mutex_init(&data.mutex, NULL);

    memset(&info, 0, sizeof(info));
    memset(&connect_info, 0, sizeof(connect_info));

    info.options = LWS_SERVER_OPTION_DO_SSL_GLOBAL_INIT;
    info.port = CONTEXT_PORT_NO_LISTEN;
    info.protocols = (const struct lws_protocols[]){
        {"example", callback, sizeof(client_data_t), 0},
        {NULL, NULL, 0, 0}};

    context = lws_create_context(&info);
    if (!context) {
        fprintf(stderr, "Failed to create context\n");
        return 1;
    }

    connect_info.context = context;
    connect_info.address = "stt-rt.soniox.com";
    connect_info.host = "stt-rt.soniox.com";
    connect_info.port = 443;
    connect_info.path = "/transcribe-websocket";
    connect_info.ssl_connection = LCCSCF_USE_SSL;
    connect_info.protocol = "example";
    connect_info.userdata = &data;

    data.wsi = lws_client_connect_via_info(&connect_info);
    if (!data.wsi) {
        fprintf(stderr, "Failed to establish WebSocket connection\n");
        lws_context_destroy(context);
        return 1;
    }

    data.context = context;

    printf("Opening WebSocket connection...\n");

    while (lws_service(context, 100) >= 0 && !data.closed) {}

    lws_context_destroy(context);

    return 0;
}
