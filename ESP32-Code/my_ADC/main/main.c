#include <stdio.h>
#include "driver/adc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void app_main(void)
{
    adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_DB_11);
    adc1_config_width(ADC_WIDTH_BIT_12);

    while (1)
    {
        //12 bit ADC, 4096 steps
        //step size = 3.3V / 4096 = 0.0008056640625V

        //Get the ADC value
        int adc_value = adc1_get_raw(ADC1_CHANNEL_0);

        //Convert the ADC value to voltage
        float voltage = adc_value * 0.8056640625;

        printf("Voltage: %.2f\n mv", voltage);
        vTaskDelay(pdMS_TO_TICKS(500)); //500ms delay
    }
}