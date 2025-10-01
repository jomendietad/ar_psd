import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter
from scipy.stats import normaltest
import sys
import subprocess
import time
import os
import json # To export metrics for the plot
import psutil
import platform

def get_memory_speed():
    """
    Attempts to get the RAM speed by running OS-specific commands.
    Returns the speed in MHz or 'N/A' if it cannot be found.
    """
    system = platform.system()
    try:
        if system == "Linux":
            command = "sudo dmidecode -t memory | grep 'Configured Memory Speed'"
            result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            speed = result.split(':')[1].strip().split(' ')[0]
            return f"{speed} MT/s"
        elif system == "Windows":
            command = "wmic memorychip get configuredclockspeed"
            result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            speed = result.strip().split('\n')[1]
            return f"{speed} MHz"
    except Exception:
        return "N/A"
    return "N/A"

def run_c_analyzer_with_monitoring(sample_rate, ar_order, executable_path='./bin/estimator'):
    print(f"\n> Running C analysis with Fs = {sample_rate} Hz, AR Order = {ar_order} and advanced monitoring...")
    proc = subprocess.Popen(
        [executable_path, str(sample_rate), str(ar_order)], # <-- Order argument added
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    p = psutil.Process(proc.pid)
    cpu_measurements, ram_measurements, temp_measurements, freq_measurements = [], [], [], []
    while proc.poll() is None:
        try:
            cpu_measurements.append(p.cpu_percent(interval=0.1))
            ram_measurements.append(p.memory_info().rss / (1024 * 1024))
            freq = psutil.cpu_freq()
            if freq: freq_measurements.append(freq.current)
            try:
                temps = psutil.sensors_temperatures()
                target_sensor = 'k10temp' if 'k10temp' in temps else 'coretemp' if 'coretemp' in temps else None
                if target_sensor:
                    temp_entries = [entry.current for entry in temps[target_sensor]]
                    temp_measurements.append(sum(temp_entries) / len(temp_entries))
            except (AttributeError, KeyError): pass
        except (psutil.NoSuchProcess, psutil.AccessDenied): break
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print("--- ERROR DURING C EXECUTION ---"); print(stderr); return False, {}
    resource_metrics = {
        'peak_cpu_percent': max(cpu_measurements) if cpu_measurements else 0.0,
        'avg_cpu_percent': sum(cpu_measurements) / len(cpu_measurements) if cpu_measurements else 0.0,
        'peak_ram_mb': max(ram_measurements) if ram_measurements else 0.0,
        'avg_ram_mb': sum(ram_measurements) / len(ram_measurements) if ram_measurements else 0.0,
        'peak_temp_c': max(temp_measurements) if temp_measurements else 'N/A',
        'avg_temp_c': sum(temp_measurements) / len(temp_measurements) if temp_measurements else 'N/A',
        'peak_freq_mhz': max(freq_measurements) if freq_measurements else 'N/A',
        'avg_freq_mhz': sum(freq_measurements) / len(freq_measurements) if freq_measurements else 'N/A'
    }
    return True, resource_metrics

def collect_and_save_metrics(audio_file, start_time, resource_metrics, signal_data):
    metrics = resource_metrics.copy()
    metrics['audio_file'] = os.path.basename(audio_file)
    metrics['total_execution_time_s'] = time.time() - start_time
    metrics['memory_speed'] = get_memory_speed()
    
    try:
        with open('data/metrics_c_output.txt', 'r') as f:
            for line in f:
                key, value = line.strip().split(':')
                metrics[key] = float(value)
    except Exception as e:
        print(f"Warning: Could not read C metrics: {e}")
    try:
        ar_coeffs = np.loadtxt('data/ar_coeffs.txt')
        residual_error = lfilter(ar_coeffs, 1, signal_data)
        _, p_value = normaltest(residual_error)
        metrics['gaussianity_p_value'] = p_value
        metrics['is_gaussian'] = "Yes" if p_value >= 0.05 else "No"
    except Exception as e:
        print(f"Warning: Could not perform Gaussianity test: {e}")
        metrics['gaussianity_p_value'] = 'N/A'
        metrics['is_gaussian'] = 'N/A'
    peaks = []
    try:
        peak_data = np.loadtxt('data/peaks_output.txt', delimiter=',', comments='#')
        if peak_data.ndim == 1: peak_data = np.array([peak_data])
        for row in peak_data:
            peaks.append({'frequency_hz': float(row[0]), 'power_db': float(row[1]), 'bandwidth_hz': float(row[2])})
        metrics['detected_peaks'] = peaks
    except Exception as e:
        print(f"Warning: Could not read peak data: {e}")
    
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)
    report_filename = os.path.join(results_dir, f"{os.path.splitext(metrics['audio_file'])[0]}_metrics.txt")
    with open(report_filename, 'w') as f:
        f.write("--- Spectral Analysis and Performance Report ---\n\n")
        f.write(f"File Analyzed: {metrics.get('audio_file', 'N/A')}\n")
        f.write("\n--- Performance and Hardware Resource Metrics ---\n")
        f.write(f"Total Execution Time (full workflow): {metrics.get('total_execution_time_s', 0):.4f} s\n")
        f.write(f"C Analyzer CPU Time: {metrics.get('cpu_time_c', 0):.4f} s\n")
        for key, label, unit in [
            ('peak_cpu_percent', 'Peak CPU Usage', '%'), ('avg_cpu_percent', 'Average CPU Usage', '%'),
            ('peak_ram_mb', 'Peak RAM Usage', 'MB'), ('avg_ram_mb', 'Average RAM Usage', 'MB'),
            ('peak_freq_mhz', 'Peak CPU Frequency', 'MHz'), ('avg_freq_mhz', 'Average CPU Frequency', 'MHz'),
            ('peak_temp_c', 'Peak CPU Temperature', '°C'), ('avg_temp_c', 'Average CPU Temperature', '°C')
        ]:
            value = metrics.get(key, 'N/A')
            if isinstance(value, (int, float)): f.write(f"{label} (C process only): {value:.2f} {unit}\n")
            else: f.write(f"{label} (C process only): {value}\n")
        f.write(f"RAM Frequency (Configured): {metrics.get('memory_speed', 'N/A')}\n")
        f.write("\n--- AR Model Metrics ---\n")
        f.write(f"Model Order Used: {int(metrics.get('used_ar_order', 0))}\n") # Text changed
        f.write(f"Residual Noise Variance: {metrics.get('noise_variance', 0):.12f}\n")
        f.write("\n--- Model Validation (Residual Gaussianity Test) ---\n")
        f.write(f"Result: {metrics.get('is_gaussian', 'N/A')}\n")
        p_val = metrics.get('gaussianity_p_value', 'N/A')
        if isinstance(p_val, (int, float)): f.write(f"p-value: {p_val:.4f} (considered Gaussian if p > 0.05)\n")
        else: f.write(f"p-value: {p_val}\n")
        f.write("\n--- Detected Frequency Peaks ---\n")
        detected_peaks = metrics.get('detected_peaks')
        if detected_peaks:
            sorted_peaks = sorted(detected_peaks, key=lambda p: p['power_db'], reverse=True)
            for i, peak in enumerate(sorted_peaks):
                f.write(f"  Peak #{i+1} (sorted by power):\n")
                f.write(f"    Frequency: {peak['frequency_hz']:.2f} Hz\n")
                f.write(f"    Power:   {peak['power_db']:.2f} dB\n")
                f.write(f"    Width (-3dB): {peak['bandwidth_hz']:.2f} Hz (precision metric)\n")
        else: f.write("  No significant peaks were detected.\n")

    plot_metrics = {
        'total_execution_time_s': metrics.get('total_execution_time_s'),
        'cpu_time_c': metrics.get('cpu_time_c'),
        'peak_cpu_percent': metrics.get('peak_cpu_percent'),
        'avg_cpu_percent': metrics.get('avg_cpu_percent'),
        'peak_ram_mb': metrics.get('peak_ram_mb'),
        'avg_ram_mb': metrics.get('avg_ram_mb'),
        'memory_speed': metrics.get('memory_speed'),
        'is_gaussian': metrics.get('is_gaussian'),
        'gaussianity_p_value': metrics.get('gaussianity_p_value'),
        'used_ar_order': metrics.get('used_ar_order')
    }
    with open('data/plot_metrics.json', 'w') as f:
        json.dump(plot_metrics, f, indent=4)

    print("\n--- ANALYSIS SUMMARY ---")
    print(f"Total Time: {metrics.get('total_execution_time_s', 0):.2f} s")
    cpu_p, cpu_a = metrics.get('peak_cpu_percent', 0), metrics.get('avg_cpu_percent', 0)
    ram_p, ram_a = metrics.get('peak_ram_mb', 0), metrics.get('avg_ram_mb', 0)
    freq_p, freq_a = metrics.get('peak_freq_mhz', 'N/A'), metrics.get('avg_freq_mhz', 'N/A')
    temp_p, temp_a = metrics.get('peak_temp_c', 'N/A'), metrics.get('avg_temp_c', 'N/A')
    print(f"CPU Usage (Peak/Avg): {cpu_p:.2f}% / {cpu_a:.2f}%")
    print(f"RAM Usage (Peak/Avg): {ram_p:.2f} MB / {ram_a:.2f} MB")
    if isinstance(freq_p, (int, float)): print(f"CPU Freq (Peak/Avg): {freq_p:.0f} MHz / {freq_a:.0f} MHz")
    else: print("CPU Freq: N/A")
    if isinstance(temp_p, (int, float)): print(f"CPU Temp (Peak/Avg): {temp_p:.1f}°C / {temp_a:.1f}°C")
    else: print("CPU Temp: N/A")
    print(f"RAM Freq: {metrics.get('memory_speed', 'N/A')}")
    p_val_term = metrics.get('gaussianity_p_value', 'N/A')
    is_gauss_term = metrics.get('is_gaussian', 'N/A')
    if isinstance(p_val_term, (int, float)):
        print(f"Model Validation (Residual): {is_gauss_term} (p={p_val_term:.3f})")
    else:
        print(f"Model Validation (Residual): {is_gauss_term}")
    print(f"AR Order Used: {int(metrics.get('used_ar_order', 0))}") # Text changed
    if metrics.get('detected_peaks'):
        sorted_peaks_summary = sorted(metrics['detected_peaks'], key=lambda p: p['power_db'], reverse=True)
        for peak in sorted_peaks_summary:
            print(f"  - Freq: {peak['frequency_hz']:.2f} Hz | Power: {peak['power_db']:.2f} dB | Width: {peak['bandwidth_hz']:.2f} Hz")
    print(f"\nFull report saved to: '{report_filename}'")

def main(audio_path, ar_order, output_path='data/audio_signal.txt'):
    start_time = time.time()
    try:
        sample_rate, data = wavfile.read(audio_path)
        if data.ndim > 1: data = data.mean(axis=1)
        if np.issubdtype(data.dtype, np.integer):
            data = data.astype(np.float32) / np.iinfo(data.dtype).max
        np.savetxt(output_path, data)
        success, resource_metrics = run_c_analyzer_with_monitoring(sample_rate, ar_order)
        if success:
            collect_and_save_metrics(audio_path, start_time, resource_metrics, data)
    except Exception as e:
        print(f"An error occurred in the main workflow: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/run_analysis.py <path_to_wav_file> <ar_model_order>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    try:
        ar_order_arg = int(sys.argv[2])
    except ValueError:
        print("Error: The AR model order must be an integer.")
        sys.exit(1)
        
    main(audio_file, ar_order_arg)