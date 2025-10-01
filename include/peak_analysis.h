#ifndef PEAK_ANALYSIS_H
#define PEAK_ANALYSIS_H

#include <stdio.h>

// Structure to store information about a detected peak
typedef struct {
    int index;
    double frequency;
    double power_db;
    double width_hz; // Bandwidth at -3dB (FWHM)
} PeakInfo;

// Analyzes the PSD to find all significant peaks
// and writes the results to a file.
void analyze_and_write_peaks(
    const char* filename,
    double* psd,
    int n_freq,
    double sample_rate,
    double threshold_db
);

#endif // PEAK_ANALYSIS_H