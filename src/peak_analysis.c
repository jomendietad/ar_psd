#include "peak_analysis.h"
#include <stdlib.h>
#include <math.h>

// Helper function to convert from linear power to dB
static double to_db(double value) {
    if (value <= 0) return -200.0; // Avoid log(0)
    return 10.0 * log10(value);
}

void analyze_and_write_peaks(const char* filename, double* psd, int n_freq, double sample_rate, double threshold_db) {
    FILE* file = fopen(filename, "w");
    if (!file) {
        perror("Could not open peak metrics file");
        return;
    }

    fprintf(file, "# Frequency (Hz), Power (dB), Bandwidth at -3dB (Hz)\n");

    double max_psd_val = 0.0;
    for (int i = 0; i < n_freq; i++) {
        if (psd[i] > max_psd_val) max_psd_val = psd[i];
    }
    double max_db = to_db(max_psd_val);
    double freq_per_bin = (sample_rate / 2.0) / (n_freq - 1);

    // Loop to find peaks (edges are ignored)
    for (int i = 1; i < n_freq - 1; i++) {
        double current_db = to_db(psd[i]);
        // A peak is a local maximum and must exceed a threshold relative to the max peak
        if (psd[i] > psd[i - 1] && psd[i] > psd[i + 1] && current_db > max_db + threshold_db) {
            
            // --- CORRECTED INTERPOLATION LOGIC ---
            // Apply parabolic interpolation locally around index 'i'
            double y_minus_1 = to_db(psd[i - 1]);
            double y_0 = to_db(psd[i]);
            double y_plus_1 = to_db(psd[i + 1]);

            // Formula for the offset 'p' of the parabola's vertex
            double p = 0.5 * (y_minus_1 - y_plus_1) / (y_minus_1 - 2.0 * y_0 + y_plus_1);
            
            // The corrected index is now a floating-point value
            double corrected_index = (double)i + p;
            double corrected_freq = corrected_index * freq_per_bin;
            // --- END OF CORRECTION ---

            // --- Calculate Bandwidth at -3dB (FWHM) ---
            double half_power_db = y_0 - 3.0;
            int l_idx = i, r_idx = i;
            // Search to the left
            while (l_idx > 0 && to_db(psd[l_idx]) > half_power_db) l_idx--;
            // Search to the right
            while (r_idx < n_freq - 1 && to_db(psd[r_idx]) > half_power_db) r_idx++;
            
            double width = (double)(r_idx - l_idx) * freq_per_bin;

            // Write the corrected and calculated values
            fprintf(file, "%.4f, %.4f, %.4f\n", corrected_freq, y_0, width);
        }
    }
    fclose(file);
}