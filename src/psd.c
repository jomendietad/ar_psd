#include "psd.h"
#include <complex.h>

// --- FUNCIÓN OPTIMIZADA ---
void calculate_psd(double* a, int order, double variance, int n_freq, double* psd) {
    for (int i = 0; i < n_freq; i++) {
        double omega = 2.0 * M_PI * i / (2.0 * (n_freq - 1));
        
        // --- INICIO DE LA SECCIÓN OPTIMIZADA ---
        // Pre-calcular el 'twiddle factor'
        double complex w = cexp(-I * omega);
        double complex wk = w; // wk será w^k
        
        double complex den = 1.0;
        for (int k = 1; k <= order; k++) {
            den += a[k] * wk;
            // Actualizar wk para la siguiente iteración (wk = w^(k+1))
            wk *= w; 
        }
        // --- FIN DE LA SECCIÓN OPTIMIZADA ---
        
        psd[i] = variance / (cabs(den) * cabs(den));
    }
}

// El resto del archivo no necesita cambios
double find_central_frequency(double* psd, int n_freq, double sample_rate) {
    int max_index = 0;
    double max_value = 0.0;
    for (int i = 0; i < n_freq; i++) {
        if (psd[i] > max_value) {
            max_value = psd[i];
            max_index = i;
        }
    }
    return (double)max_index * (sample_rate / 2.0) / (double)(n_freq - 1);
}

double find_central_frequency_interpolated(double* psd, int n_freq, double sample_rate) {
    int max_index = 0;
    double max_value = 0.0;
    for (int i = 0; i < n_freq; i++) {
        if (psd[i] > max_value) {
            max_value = psd[i];
            max_index = i;
        }
    }

    if (max_index > 0 && max_index < n_freq - 1) {
        double y_minus_1 = 10 * log10(psd[max_index - 1]);
        double y_0 = 10 * log10(psd[max_index]);
        double y_plus_1 = 10 * log10(psd[max_index + 1]);
        double p = 0.5 * (y_minus_1 - y_plus_1) / (y_minus_1 - 2.0 * y_0 + y_plus_1);
        double corrected_index = (double)max_index + p;
        return corrected_index * (sample_rate / 2.0) / (double)(n_freq - 1);
    }

    return (double)max_index * (sample_rate / 2.0) / (double)(n_freq - 1);
}