import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.io import wavfile
import sys
import json # To read the metrics file

def plot_psd_with_stats(psd_file, peaks_file, metrics_file, audio_filename, output_folder='plots'):
    """
    Reads audio data, PSD, peaks, and metrics, then plots both the waveform
    and the PSD with annotations. Saves the figure to a PNG file.
    """
    # --- Load metrics from the JSON file ---
    metrics = {}
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
    except Exception as e:
        print(f"Warning: Could not read metrics file '{metrics_file}': {e}")

    # --- Load audio signal for time-domain plot ---
    try:
        sample_rate, audio_data = wavfile.read(audio_filename)
        if audio_data.ndim > 1: # Handle stereo by taking the mean
            audio_data = audio_data.mean(axis=1)
        # Normalize audio data to [-1, 1] for consistent plotting
        if np.issubdtype(audio_data.dtype, np.integer):
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        
        duration = len(audio_data) / sample_rate
        time_axis = np.linspace(0., duration, len(audio_data))
    except Exception as e:
        print(f"Error: Could not read audio file '{audio_filename}': {e}")
        return

    # --- Load PSD and peak data ---
    try:
        psd_data = np.loadtxt(psd_file)
    except IOError:
        print(f"Error: Could not read PSD file '{psd_file}'")
        return

    epsilon = 1e-20
    psd_db = 10 * np.log10(psd_data + epsilon)

    try:
        peaks = np.loadtxt(peaks_file, delimiter=',', comments='#')
    except (IOError, ValueError):
        print(f"Warning: Could not read peaks file '{peaks_file}' or it is empty.")
        peaks = np.array([])

    os.makedirs(output_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_filename))[0]
    output_path = os.path.join(output_folder, f'{base_name}_analysis_plot.png')

    n_freq = len(psd_data)
    frequencies = np.linspace(0, sample_rate / 2, n_freq)

    # --- Create a figure with two subplots (waveform and PSD) ---
    fig, axs = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [1, 2]})
    plt.subplots_adjust(right=0.75, hspace=0.3)

    # --- Top Plot: Waveform ---
    axs[0].plot(time_axis, audio_data, linewidth=0.5)
    axs[0].set_title(f'Waveform')
    axs[0].set_xlabel('Time (s)')
    axs[0].set_ylabel('Amplitude')
    axs[0].grid(True, linestyle='--', linewidth=0.5)
    axs[0].set_xlim(0, duration)

    # --- Bottom Plot: Power Spectral Density (PSD) ---
    axs[1].plot(frequencies, psd_db, label='Estimated PSD')

    if peaks.ndim == 1 and peaks.size > 0:
        peaks = np.array([peaks])
        
    if peaks.size > 0:
        axs[1].plot(peaks[:, 0], peaks[:, 1], "x", color='red', markersize=10, mew=2, label='Detected Peaks')
        for peak in peaks:
            freq, power, width = peak
            axs[1].text(freq, power + 2, f"{freq:.1f} Hz", color='red', ha='center', fontsize=9)

    axs[1].set_title('Power Spectral Density (PSD)')
    axs[1].set_xlabel('Frequency (Hz)')
    axs[1].set_ylabel('Power/Frequency (dB/Hz)')
    axs[1].grid(True, which='both', linestyle='--', linewidth=0.5)
    axs[1].legend(loc='upper left')
    
    if peaks.size > 0:
        max_freq_of_interest = np.max(peaks[:, 0]) * 1.5
        axs[1].set_xlim(0, min(max_freq_of_interest, sample_rate / 2))
    else:
        axs[1].set_xlim(0, sample_rate / 2)

    if psd_db.size > 0:
        max_power = np.max(psd_db)
        axs[1].set_ylim(bottom=max_power - 80, top=max_power + 10)

    # --- Add a main title to the figure ---
    fig.suptitle(f'Signal Analysis - {os.path.basename(audio_filename)}', fontsize=16)

    # --- Add the text with statistics to the figure ---
    if metrics:
        stats_text = "--- Analysis Summary ---\n\n"
        stats_text += f"Total Time: {metrics.get('total_execution_time_s', 0):.2f} s\n"
        stats_text += f"CPU Time (C): {metrics.get('cpu_time_c', 0):.2f} s\n"
        
        cpu_p = metrics.get('peak_cpu_percent', 0)
        cpu_a = metrics.get('avg_cpu_percent', 0)
        ram_p = metrics.get('peak_ram_mb', 0)
        ram_a = metrics.get('avg_ram_mb', 0)
        
        stats_text += f"CPU Usage (Peak/Avg): {cpu_p:.1f}% / {cpu_a:.1f}%\n"
        stats_text += f"RAM Usage (Peak/Avg): {ram_p:.2f} MB / {ram_a:.2f} MB\n"
        
        stats_text += f"RAM Freq: {metrics.get('memory_speed', 'N/A')}\n\n"
        stats_text += "--- Model Validation ---\n"
        is_gauss = metrics.get('is_gaussian', 'N/A')
        p_val = metrics.get('gaussianity_p_value', -1)
        stats_text += f"Gaussian Residual: {is_gauss}\n"
        if p_val != -1 and p_val != 'N/A':
            stats_text += f"  (p-value: {p_val:.3f})\n"
        stats_text += f"AR Order: {int(metrics.get('used_ar_order', 0))}\n"

        fig.text(0.78, 0.9, stats_text, bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.5),
                 fontsize=9, verticalalignment='top', fontfamily='monospace')

    plt.savefig(output_path)
    print(f"Plot with statistics saved to: '{output_path}'")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/plot_psd.py <path_to_audio.wav> <path_to_metrics.json>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    metrics_file = sys.argv[2]
    
    PSD_FILE_PATH = 'data/psd_output.txt'
    PEAKS_FILE_PATH = 'data/peaks_output.txt'
    
    plot_psd_with_stats(PSD_FILE_PATH, PEAKS_FILE_PATH, metrics_file, audio_file)