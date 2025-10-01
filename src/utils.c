#include "utils.h"

// --- FUNCTION COMPLETELY REWRITTEN FOR MAXIMUM EFFICIENCY ---
double* read_signal(const char* filename, int* length) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        perror("Could not open signal file");
        return NULL;
    }

    // --- First Step: Count the number of samples ---
    int count = 0;
    double value;
    while (fscanf(file, "%lf", &value) == 1) {
        count++;
    }

    // If the file is empty, do nothing.
    if (count == 0) {
        fclose(file);
        *length = 0;
        return NULL;
    }

    // --- Second Step: Allocate memory once and read the data ---
    double* signal = (double*)malloc(count * sizeof(double));
    if (!signal) {
        perror("Failed to allocate memory for the signal");
        fclose(file);
        return NULL;
    }

    // Go back to the beginning of the file to read it again
    rewind(file);

    for (int i = 0; i < count; i++) {
        if (fscanf(file, "%lf", &signal[i]) != 1) {
            // This should not happen if the file was not modified
            fprintf(stderr, "Read error in the second pass.\n");
            free(signal);
            fclose(file);
            return NULL;
        }
    }

    fclose(file);
    *length = count;
    return signal;
}

void write_psd(const char* filename, double* psd, int length) {
    FILE* file = fopen(filename, "w");
    if (!file) {
        perror("Could not open PSD output file");
        return;
    }

    for (int i = 0; i < length; i++) {
        fprintf(file, "%f\n", psd[i]);
    }

    fclose(file);
}