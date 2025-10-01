# Power Spectral Density (PSD) Analyzer with Autoregressive (AR) Model

This project is an audio signal analysis tool that estimates the **Power Spectral Density (PSD)** using an **Autoregressive (AR) model**. It is implemented with a high-performance processing core in **C**, orchestrated by **Python** scripts for file handling, visualization, and resource monitoring.

The system is capable of taking a `.wav` audio file, calculating its power spectrum, detecting significant frequency peaks, and generating both a detailed text report and a visual graph of the results. Additionally, it monitors and reports advanced performance metrics such as CPU usage, RAM, and execution time.

## Key Features

  - **High-Resolution PSD Estimation**: Uses the **Burg method** to calculate the coefficients of an AR model, enabling spectral estimation with higher resolution than traditional FFT- based methods, especially for signals with sharp peaks.
  - **Peak Detection and Analysis**: Automatically identifies the most important frequency peaks in the signal, calculating their precise frequency (using **parabolic interpolation**), their power in dB, and their -3dB bandwidth.
  - **Hybrid Architecture (Python + C)**: Combines the ease of use and powerful libraries of Python for orchestration and visualization, with the speed and efficiency of C for intensive numerical operations.
  - **Performance Monitoring**: During the execution of the C core, a Python script monitors the CPU (peak and average) and RAM (peak and average) usage in real-time, providing a clear profile of the algorithm's performance.
  - **Model Validation**: The system calculates the AR model's **residue** and performs a normality test (Shapiro-Wilk) on it. Theoretically, a well-fitted AR model should leave a residue that resembles Gaussian white noise.
  - **Comprehensive Reports**: Generates two types of output for each analysis:
    1.  A **`.png` plot** visualizing the PSD, detected peaks, and a summary of analysis metrics.
    2.  A **`.txt` report** with a detailed breakdown of all performance metrics, model parameters, and a list of found peaks, sorted by power.
  - **Optimized Code**: The C code includes micro-optimizations to reduce memory access and improve calculation speed in the most critical loops.

-----

## How It Works: The Analysis Flow

The process is controlled via a `Makefile` and follows these steps:

1.  **Invocation**: The user runs `make analyze WAVFILE=path/to/audio.wav AR_ORDER=30`.
2.  **Orchestration (Python)**: The `Makefile` invokes `python/run_analysis.py`.
      - This script reads the `.wav` file, normalizes the audio signal, and saves it to a text file (`data/audio_signal.txt`).
      - It launches the compiled C program (`bin/estimator`) as a subprocess, passing the sampling frequency and the AR model order as arguments.
      - While the C program is running, the Python script monitors the process's resource usage (CPU, RAM) using the `psutil` library.
3.  **Main Processing (C)**: The `bin/estimator` executable performs the heavy lifting.
      - Reads the signal from `data/audio_signal.txt`.
      - Applies a **Hanning window** to reduce spectral leakage.
      - Calculates the AR model coefficients of order `p` using the **Burg method**.
      - Calculates the **PSD** from the model coefficients.
      - Performs **peak analysis** on the PSD to find dominant frequencies, using interpolation for greater accuracy.
      - Saves intermediate results: AR coefficients, PSD, peaks, and execution time metrics in the `data/` folder.
4.  **Consolidation and Reporting (Python)**:
      - Once the C process finishes, `run_analysis.py` regains control.
      - It reads the AR coefficients to calculate the **model residue** and performs the Gaussianity test.
      - Aggregates all metrics (from `psutil` monitoring, the C metrics file, and the validation test) into a complete text report in `results/`.
      - Saves a subset of these metrics to a JSON file for the plotting script.
5.  **Visualization (Python)**:
      - The `Makefile` calls `python/plot_psd.py`.
      - This script reads the PSD data, peaks, and the metrics JSON file.
      - It generates a high-quality plot with `matplotlib`, showing the PSD, marking the peaks, and overlaying a text box with the analysis summary. The plot is saved in the `plots/` folder.
6.  **Cleanup**: Finally, the `Makefile` deletes all intermediate files from the `data/` folder.

-----

## Mathematical Foundation

The core of this project is based on **autoregressive modeling** for spectral estimation.

### 1\. Autoregressive (AR) Model

An AR model describes a time series (like an audio signal) by assuming that each sample $x[n]$ can be expressed as a linear combination of its $p$ previous samples, plus an unpredictable error term $\varepsilon[n]$ (white noise).

The equation defining an AR model of order $p$ is:

$$x[n] = -\sum_{k=1}^{p} a_k x[n-k] + \varepsilon[n]$$

Where:

  - $x[n]$ is the current signal sample.
  - $a_k$ are the model coefficients we seek to find.
  - $p$ is the **model order**, defining how many past samples are used.
  - $\varepsilon[n]$ is a white noise process with zero mean and constant variance $\sigma^2_\varepsilon$.

Rearranging the equation, we see that the error (or residue) is the difference between the actual sample and its prediction:

$$\varepsilon[n] = x[n] + \sum_{k=1}^{p} a_k x[n-k]$$

The goal of the analysis is to find the coefficients $a_k$ and the variance $\sigma^2_\varepsilon$ that best fit the input signal.

### 2\. Burg Method for Coefficient Estimation

The **Burg method** is an efficient algorithm for calculating the coefficients $a_k$. Instead of directly solving a system of equations (like the Yule-Walker methods), it does so recursively, always guaranteeing a stable model.

The central idea is to minimize the sum of the powers of the forward ($f_j[n]$) and backward ($b_j[n]$) prediction errors at each stage $j$ of the recursion (from $j=1$ to order $p$).

**Algorithm Steps:**

1.  **Initialization (j=0)**:

      - The initial prediction error (order 0) is the signal itself.
      - Forward error: $f_0[n] = x[n]$
      - Backward error: $b_0[n] = x[n]$
      - The initial variance $P_0$ is the mean power of the signal.

2.  **Recursion (for j = 1 to p)**:

      - **Calculate the Reflection Coefficient ($k_j$)**: This coefficient minimizes the error power at stage $j$. It is calculated as:
        $$k_j = \frac{-2 \sum_{n=j}^{N-1} f_{j-1}[n] \cdot b_{j-1}[n-1]}{\sum_{n=j}^{N-1} (f_{j-1}^2[n] + b_{j-1}^2[n-1])}$$

      - **Update the AR Coefficients ($a_k^{(j)}$)**: The coefficients for the order $j$ model are calculated using those from order $j-1$ and the new reflection coefficient $k_j$. This is known as the **Levinson-Durbin recursion**.
        $$a_j^{(j)} = k_j$$       $$a_k^{(j)} = a_k^{(j-1)} + k_j \cdot a_{j-k}^{(j-1)} \quad \text{for } k=1, \dots, j-1$$

      - **Update the Error Variance ($P_j$)**: The variance is also updated recursively.
        $$P_j = P_{j-1} (1 - k_j^2)$$

      - **Update the Errors**: Finally, the forward and backward errors for the next iteration are calculated.
        $$f_j[n] = f_{j-1}[n] + k_j \cdot b_{j-1}[n-1]$$       $$b_j[n] = b_{j-1}[n-1] + k_j \cdot f_{j-1}[n]$$

3.  **Final Result**: After $p$ iterations, the coefficients $a_k = a_k^{(p)}$ and the variance $\sigma^2_\varepsilon = P_p$ are the final parameters of the model.

### 3\. Calculating the PSD from the AR Model

Once we have the AR model, we can treat the signal as the output of a digital filter whose input is white noise ($\varepsilon[n]$) and whose transfer function is:

$$H(z) = \frac{1}{1 + \sum_{k=1}^{p} a_k z^{-k}}$$

The Power Spectral Density (PSD) of the signal $x[n]$ is related to the squared magnitude of this filter's frequency response, scaled by the input noise variance.

The formula for the PSD is:

$$S(f) = \frac{P_p}{|A(e^{j2\pi f})|^2} = \frac{\sigma^2_\varepsilon}{|1 + \sum_{k=1}^{p} a_k e^{-j2\pi f k}|^2}$$

Where:

  - $f$ is the frequency.
  - $j$ is the imaginary unit.
  - $P_p = \sigma^2_\varepsilon$ is the final residue variance.
  - The denominator is the squared magnitude of the polynomial $A$ evaluated on the unit circle of the Z-plane, which corresponds to the frequency response.

The code in `psd.c` implements this formula by calculating the value of the denominator for a set of discrete frequencies from 0 up to half the sampling frequency.

### 4\. Parabolic Peak Interpolation

To find a peak's frequency with greater precision than allowed by the frequency grid spacing, **parabolic interpolation** is used.

1.  A local maximum is found at index $i$ (i.e., `psd[i] > psd[i-1]` and `psd[i] > psd[i+1]`).
2.  The power values in dB of this point ($y_0$) and its two neighbors ($y_{-1}$, $y_{+1}$) are taken.
3.  A parabola is fitted to these three points. The vertex of this parabola provides a more precise estimate of the peak's frequency and power.
4.  The vertex shift ($p$) from the center point $i$ is calculated as:
    $$p = \frac{1}{2} \frac{y_{-1} - y_{+1}}{y_{-1} - 2y_0 + y_{+1}}$$
5.  The corrected frequency $f_{corr}$ is:
    $$f_{corr} = (i + p) \cdot \Delta f$$
    where $\Delta f$ is the frequency resolution (frequency per bin).

-----

## File Structure

```
ar_psd/
├── Makefile                # Automates compilation and analysis
├── bin/                    # Contains the compiled C executable
├── data/                   # Intermediate files generated during execution
├── include/                # Header files (.h) for the C code
│   ├── ar_model.h
│   ├── dsp_utils.h
│   ├── peak_analysis.h
│   ├── psd.h
│   └── utils.h
├── obj/                    # Object files (.o) generated during compilation
├── plots/                  # Output plots in .png format
├── python/                 # Orchestration and visualization scripts
│   ├── plot_psd.py
│   └── run_analysis.py
├── results/                # Detailed text reports (.txt)
└── src/                    # C source code (.c)
    ├── ar_model.c
    ├── dsp_utils.c
    ├── main.c
    ├── peak_analysis.c
    ├── psd.c
    └── utils.c
```

## Requirements

  - **C Compiler**: `gcc`
  - **Build System**: `make`
  - **Python Interpreter**: `python3`
  - **Python Libraries**:
      - `numpy`
      - `scipy`
      - `matplotlib`
      - `psutil`

You can install them with pip:
`pip install numpy scipy matplotlib psutil`

-----

## Usage

The entire process of compilation, analysis, and cleanup is automated through the interactive script `build.sh`.

**1. Grant Execution Permissions**

Before using it for the first time, make sure the script has execution permissions. You only need to do this once.

```bash
chmod +x build.sh
```

**2. Run the Analysis**

To start the analysis, simply run the script without arguments:

```bash
./build.sh
```

The script will manage the process intelligently:

  - It will **automatically search** for all `.wav` files in the project's root folder.
  - **If it finds a single `.wav` file**, it will automatically select it and ask you for the AR model order to use.
  - **If it finds multiple `.wav` files**, it will present a numbered list for you to choose which one you want to analyze. It will also include an option to exit.
  - **If it finds no `.wav` files**, it will inform you and stop.

Once the file has been selected and you have entered the AR model order, the script will compile the code (if necessary) and execute the complete analysis. The final results will be saved in the `plots/` (graphs) and `results/` (text reports) folders.

### Usage Examples

**Scenario 1: There are multiple `.wav` files in the directory.**

```bash
$ ./build.sh

The following .wav files were found:
1) multi_tone_signal.wav
2) prueba1.wav
3) fragmento_minuto_1_5s.wav
4) Exit
Please choose a file to analyze (1-4): 2

Selected file: prueba1.wav
Please enter the AR model order to use (e.g., 30): 30

--- Compiling C core ---
...
--- (1/3) Orchestrating complete analysis (Python -> C) with AR Order = 30 ---
...
Plot with statistics saved to: 'plots/prueba1_psd_plot.png'
...
```

**Scenario 2: There is only one `.wav` file in the directory.**

```bash
$ ./build.sh

A single .wav file was found: multi_tone_signal.wav

--- Compiling C core ---
...
--- (1/3) Orchestrating complete analysis (Python -> C) with AR Order = 30 ---
...