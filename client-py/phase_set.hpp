#include <stdio.h>
#include <stdint.h>
#include <math.h>

#define PI 3.14159265

int32_t IQ_phase_shift(double phase) {
    int16_t cos_angle;
    int16_t sin_angle;
    cos_angle = (pow(2.0, 15.0))*cos( phase * PI / 180.0 );
    sin_angle = (pow(2.0, 15.0))*sin( phase * PI / 180.0 );

    return  (cos_angle << 16 | (sin_angle & 0xffff));
}