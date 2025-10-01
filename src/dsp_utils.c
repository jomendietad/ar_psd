#include "dsp_utils.h"
#include <math.h>

// Applies a Hanning window to the signal to reduce spectral leakage.
// The Hanning window has the form: w(n) = 0.5 * (1 - cos(2*PI*n / (N-1)))
void apply_hanning_window(double* signal, int signal_length) {
    for (int i = 0; i < signal_length; i++) {
        double multiplier = 0.5 * (1.0 - cos(2.0 * M_PI * i / (signal_length - 1)));
        signal[i] *= multiplier;
    }
}

// Calculates the Akaike Information Criterion (AIC).
// AIC = N * log(variance) + 2 * (order + 1)
// It is used to find the optimal model order (the one that minimizes AIC).
double calculate_aic(int signal_length, int order, double variance) {
    if (variance <= 0) {
        return INFINITY; // Avoid logarithms of zero or negative numbers
    }
    return (double)signal_length * log(variance) + 2.0 * (order + 1);
}