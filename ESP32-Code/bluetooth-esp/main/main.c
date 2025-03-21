#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_bt.h"
#include "esp_bt_device.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"
#include "esp_spp_api.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "BT_APP";
static uint32_t spp_handle = 0; // Store the Bluetooth connection handle

// Declare Bluetooth SPP callback
static void spp_callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param)
{
    switch (event)
    {
    case ESP_SPP_INIT_EVT:
        ESP_LOGI(TAG, "SPP initialized");
        break;

    case ESP_SPP_START_EVT:
        ESP_LOGI(TAG, "SPP server started");
        break;

    case ESP_SPP_SRV_OPEN_EVT: // A client has connected
        ESP_LOGI(TAG, "Client Connected, handle: %d", param->srv_open.handle);
        spp_handle = param->srv_open.handle; // Save the handle for sending data later
        break;

    case ESP_SPP_CLOSE_EVT: // A client has disconnected
        ESP_LOGI(TAG, "Client Disconnected");
        spp_handle = 0; // Clear the handle
        break;

    case ESP_SPP_DATA_IND_EVT: // Data received from client
        ESP_LOGI(TAG, "Received Data (%d bytes): %.*s",
                 param->data_ind.len,
                 param->data_ind.len,
                 (char *)param->data_ind.data);

        // Echo the received data back to the client
        esp_spp_write(param->data_ind.handle, param->data_ind.len, param->data_ind.data);
        break;

    case ESP_SPP_WRITE_EVT:
        ESP_LOGI(TAG, "Write operation completed, status: %d, bytes written: %d",
                 param->write.status,
                 param->write.len);
        break;

    default:
        ESP_LOGI(TAG, "SPP event: %d", event);
        break;
    }
}

void send_data_periodically()
{
    // Send data only if the client is connected
    if (spp_handle != 0)
    {
        const char *message = "Hello from ESP32! This is a periodic message.";
        esp_spp_write(spp_handle, strlen(message), (uint8_t *)message);
        ESP_LOGI(TAG, "Sent Data: %s", message);
    }
    else
    {
        ESP_LOGI(TAG, "No client connected, not sending data");
    }
}

void app_main(void)
{
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize Bluetooth
    ESP_LOGI(TAG, "Initializing Bluetooth...");

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_CLASSIC_BT));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    // Set device name for pairing
    esp_bt_dev_set_device_name("ESP32_BT");

    // Register Bluetooth SPP callback
    ESP_ERROR_CHECK(esp_spp_register_callback(spp_callback));

    // Initialize SPP
    ESP_ERROR_CHECK(esp_spp_init(ESP_SPP_MODE_CB));

    // Start SPP service
    ESP_ERROR_CHECK(esp_spp_start_srv(ESP_SPP_SEC_AUTHENTICATE, ESP_SPP_ROLE_SLAVE, 0, "SPP_SERVER"));

    ESP_LOGI(TAG, "Bluetooth Initialized, Waiting for Connection...");
    ESP_LOGI(TAG, "Device name: %s", esp_bt_dev_get_device_name());

    // Main loop: periodically send data
    while (true)
    {
        send_data_periodically();
        vTaskDelay(pdMS_TO_TICKS(5000)); // Wait for 5 seconds before sending again
    }
}