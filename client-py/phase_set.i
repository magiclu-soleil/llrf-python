 /* phase_set.i */
%include "stdint.i"
 %module phase_set
 %{
 /* Put header files here or function declarations like below */
int32_t IQ_phase_shift(double);
 %}

int32_t IQ_phase_shift(double);