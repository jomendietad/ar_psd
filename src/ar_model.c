#include <stdlib.h>
#include <math.h>
#include "ar_model.h"

void burg_method(double* signal, int signal_length, int order, double* a, double* variance) {
    double *f = (double*)calloc(signal_length, sizeof(double));
    double *b = (double*)calloc(signal_length, sizeof(double));
    double *a_temp = (double*)calloc(order + 1, sizeof(double));

    if (!f || !b || !a_temp) {
        if (f) free(f);
        if (b) free(b);
        if (a_temp) free(a_temp);
        *variance = 0;
        return;
    }

    for(int i = 0; i < signal_length; i++) {
        f[i] = signal[i];
        b[i] = signal[i];
    }

    double p = 0.0;
    for(int i = 0; i < signal_length; i++) {
        p += signal[i] * signal[i];
    }
    p /= signal_length;

    for(int i = 0; i <= order; i++) a[i] = 0.0;
    a[0] = 1.0;

    for (int j = 0; j < order; j++) {
        double num = 0.0;
        double den = 0.0;
        for (int i = j + 1; i < signal_length; i++) {
            // Store values in local variables to reduce memory access
            double fi = f[i];
            double b_im1 = b[i - 1];
            num += fi * b_im1;
            den += fi * fi + b_im1 * b_im1;
            // --- END OF MICRO-OPTIMIZATION ---
        }

        if (den <= 0.0) {
            break;
        }
        double k = -2.0 * num / den;

        p *= (1.0 - k * k);

        for (int i = 1; i <= j; i++) {
            a_temp[i] = a[i] + k * a[j - i + 1];
        }
        for (int i = 1; i <= j; i++) {
            a[i] = a_temp[i];
        }
        a[j + 1] = k;

        for (int i = signal_length - 1; i > j; i--) {
            double f_prev = f[i];
            double b_prev = b[i - 1];
            f[i] = f_prev + k * b_prev;
            b[i] = b_prev + k * f_prev;
        }
    }

    *variance = p;
    free(f);
    free(b);
    free(a_temp);
}