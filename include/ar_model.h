#ifndef AR_MODEL_H
#define AR_MODEL_H

// Estimates the AR model coefficients using Burg's method
void burg_method(double* signal, int signal_length, int order, double* a, double* variance);

#endif // AR_MODEL_H