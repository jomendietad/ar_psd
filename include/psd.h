#ifndef PSD_H
#define PSD_H

#include <math.h>

// Calculates the PSD from the AR model coefficients
void calculate_psd(double* a, int order, double variance, int n_freq, double* psd);

// Finds the central frequency from the PSD (simple method)
double find_central_frequency(double* psd, int n_freq, double sample_rate);

// --- IMPROVED FUNCTION ---
// Finds the central frequency with high precision using parabolic interpolation
double find_central_frequency_interpolated(double* psd, int n_freq, double sample_rate);

#endif // PSD_H