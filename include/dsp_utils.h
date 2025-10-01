#ifndef DSP_UTILS_H
#define DSP_UTILS_H

// Applies a Hanning window to a signal
void apply_hanning_window(double* signal, int signal_length);

// Calculates the Akaike Information Criterion (AIC)
double calculate_aic(int signal_length, int order, double variance);

#endif // DSP_UTILS_H