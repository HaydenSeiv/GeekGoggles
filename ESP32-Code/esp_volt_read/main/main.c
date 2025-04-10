#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "mqtt_client.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_log.h"
#define ADC1_CHANNEL ADC1_CHANNEL_0 // pin1

#define WIFI_SSID "SM-G928W84017"
#define WIFI_PASS "ojoq6253"
#define MQTT_BROKER "mqtt://192.168.10.11"

static const char *TAG = "ESP32_ADC_MQTT";
esp_mqtt_client_handle_t mqtt_client;

// 📌 WiFi event handler
static void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START)
    {
        esp_wifi_connect();
        ESP_LOGI(TAG, "Wifi Tying to Connect");
    }
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP)
    {
        ESP_LOGI(TAG, "Connected to WiFi!");
    }
}

// 📌 Initialize WiFi
void wifi_init(void)
{
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL);
    esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, NULL);
    ESP_LOGI(TAG, "Before Connect");

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };

    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    ESP_LOGI(TAG, "After Connect");
}

// 📌 MQTT event handler
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGI(TAG, "MQTT Event handler triggered");

    esp_mqtt_event_handle_t event = event_data;
    if (event == NULL)
    {
        ESP_LOGE(TAG, "Event data is NULL!");
        return;
    }

    switch (event->event_id)
    {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT Connected!");
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT Disconnected! Attempting reconnection...");
        esp_mqtt_client_reconnect(mqtt_client);
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT Error occurred!");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT)
        {
            ESP_LOGE(TAG, "Last error code reported from esp-tls: 0x%x", event->error_handle->esp_tls_last_esp_err);
            ESP_LOGE(TAG, "Last tls stack error number: 0x%x", event->error_handle->esp_tls_stack_err);
            ESP_LOGE(TAG, "Last captured errno : %d (%s)", event->error_handle->esp_transport_sock_errno,
                     strerror(event->error_handle->esp_transport_sock_errno));
        }
        break;
    default:
        ESP_LOGI(TAG, "Other MQTT Event: %d", event->event_id);
        break;
    }
}

// 📌 Start MQTT client
void mqtt_app_start(void)
{
    ESP_LOGI(TAG, "Inside MQTT app start");

    // Enable MQTT debug logs
    esp_log_level_set("MQTT_CLIENT", ESP_LOG_DEBUG);

    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER,
    };

    // Check if client initialization succeeds
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (mqtt_client == NULL)
    {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return;
    }

    vTaskDelay(pdMS_TO_TICKS(100)); // Add small delay

    // Register event handler with error checking
    esp_err_t err = esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, mqtt_client);
    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to register MQTT event handler: %s", esp_err_to_name(err));
        return;
    }

    // Start client with error checking
    err = esp_mqtt_client_start(mqtt_client);
    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to start MQTT client: %s", esp_err_to_name(err));
        return;
    }

    ESP_LOGI(TAG, "MQTT client started successfully");
}

// 📌 Read ADC and Publish to MQTT
void adc_task(void *pvParameter)
{
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC1_CHANNEL, ADC_ATTEN_DB_11);

    const float div_ratio = 4.0;
    float offset = 0.06;

    while (1)
    {
        int raw_value = adc1_get_raw(ADC1_CHANNEL);
        float voltage = raw_value * (3.3 / 4095.0);
        float scaled_volt = voltage + offset;
        float actual_volt = scaled_volt * div_ratio;
        float actual_mVolt = actual_volt * 1000;
        // Publish ADC data to MQTT with error checking
        char msg[50];
        if (actual_mVolt > 999.0)
        {
            snprintf(msg, sizeof(msg), "%.3fV", actual_volt);
        }
        else
        {
            snprintf(msg, sizeof(msg), "%.3fmV", actual_mVolt);
        }

        int msg_id = esp_mqtt_client_publish(mqtt_client, "esp32/adc", msg, 0, 1, 0);
        if (msg_id < 0)
        {
            ESP_LOGW(TAG, "Failed to publish MQTT message");
        }

        ESP_LOGI(TAG, "ADC Value: %d | Voltage: %.3fV | MiliVoltage: %.3fmV", raw_value, actual_volt, actual_mVolt);
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}

void app_main(void)
{
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    // Start WiFi and MQTT
    wifi_init();
    ESP_LOGI(TAG, "Finished Wifi init [main]");
    vTaskDelay(pdMS_TO_TICKS(5000)); // Wait for WiFi to connect
    mqtt_app_start();
    ESP_LOGI(TAG, "Finished App start [main]");
    vTaskDelay(pdMS_TO_TICKS(2000)); // Wait for MQTT connection

    ESP_LOGI(TAG, "starting adc task [main]");
    // Start ADC Task
    xTaskCreate(&adc_task, "adc_task", 4096, NULL, 5, NULL);
}
