#include<stdio.h>
#include <stdint.h>
#include <math.h>

//  sudo gcc -shared -Wl,-soname,phase_set -o phase_set.so -fPIC phase_set.c
#define PI 3.14159265
int32_t IQ_phase_shift(double);

int32_t IQ_phase_shift(double phase) {
    printf("phase is %f",phase);
	int16_t cos_angle;
	int16_t sin_angle;
	cos_angle = (pow(2.0, 15.0)-1)*cos(phase*PI/ 180.0 );
	sin_angle = (pow(2.0, 15.0)-1)*sin( phase * PI / 180.0 );

	/*printf(" cos_angle= %d ",cos_angle);
    printf(" sin_angle= %d ",sin_angle);*/

	return  (cos_angle << 16 | (sin_angle & 0xffff));
}
