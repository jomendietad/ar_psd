#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <stdlib.h>

// Reads a signal from a text file
double* read_signal(const char* filename, int* length);

// Writes the PSD to a text file
void write_psd(const char* filename, double* psd, int length);

#endif // UTILS_H