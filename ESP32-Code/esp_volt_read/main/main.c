#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"

#define ADC1_CHANNEL ADC1_CHANNEL_0 // GPIO36

void app_main()
{
    // Configure ADC
    adc1_config_width(ADC_WIDTH_BIT_12);                      // 12-bit resolution (0-4095)
    adc1_config_channel_atten(ADC1_CHANNEL, ADC_ATTEN_DB_11); // 11dB attenuation for full range (0-3.3V)

    const float div_ratio = 4.0;

    while (1)
    {
        int raw_value = adc1_get_raw(ADC1_CHANNEL); // Read raw ADC value

        // Convert raw value to voltage
        float offset = 0.06;
        float voltage = raw_value * (3.3 / 4095.0);
        float scaled_volt = voltage + offset;
        float actual_volt = scaled_volt * div_ratio;
        printf("ADC Value: %d | Voltage: %.6fV\n", raw_value, actual_volt);

        vTaskDelay(pdMS_TO_TICKS(2000)); // Delay for readability
    }
}
