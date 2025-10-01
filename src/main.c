#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "utils.h"
#include "ar_model.h"
#include "psd.h"
#include "dsp_utils.h"
#include "peak_analysis.h"

int main(int argc, char *argv[]) {
    // 1. Verify that we have the new argument (model order)
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <sample_rate> <ar_model_order>\n", argv[0]);
        return 1;
    }
    double sample_rate = atof(argv[1]);
    // 2. Read the model order directly from the new argument
    int model_order = atoi(argv[2]);

    clock_t start_time = clock();

    const char* signal_filename = "data/audio_signal.txt";
    const char* psd_filename = "data/psd_output.txt";
    int signal_length;
    double* signal = read_signal(signal_filename, &signal_length);
    if (!signal) return 1;

    apply_hanning_window(signal, signal_length);

    // --- REMOVED: Loop for finding optimal order with AIC ---

    // 3. Directly use the provided order
    double a[model_order + 1];
    double final_variance;
    burg_method(signal, signal_length, model_order, a, &final_variance);

    int n_freq = 4096;
    double psd[n_freq];
    calculate_psd(a, model_order, final_variance, n_freq, psd);
    write_psd(psd_filename, psd, n_freq);

    clock_t end_time = clock();
    double cpu_time_used = ((double) (end_time - start_time)) / CLOCKS_PER_SEC;

    FILE* f_metrics = fopen("data/metrics_c_output.txt", "w");
    if (f_metrics) {
        fprintf(f_metrics, "cpu_time_c:%.6f\n", cpu_time_used);
        // Now we report the order that was used, not the "optimal" one
        fprintf(f_metrics, "used_ar_order:%d\n", model_order);
        // AIC is no longer calculated, so we omit it
        fprintf(f_metrics, "noise_variance:%.12f\n", final_variance);
        fclose(f_metrics);
    }

    // --- NEW: Save the AR model coefficients ---
    FILE* f_coeffs = fopen("data/ar_coeffs.txt", "w");
    if (f_coeffs) {
        for (int i = 0; i <= model_order; i++) {
            fprintf(f_coeffs, "%.15f\n", a[i]);
        }
        fclose(f_coeffs);
    }

    analyze_and_write_peaks("data/peaks_output.txt", psd, n_freq, sample_rate, -40.0);

    free(signal);
    return 0;
}