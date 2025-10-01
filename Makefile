CC = gcc
# --- MODIFIED LINE ---
# Add high-level (-O3) and CPU-specific (-march=native) optimizations
CFLAGS = -Iinclude -lm -O3 -march=native
LDFLAGS = -lm
PYTHON = python3

SRCDIR = src
INCDIR = include
OBJDIR = obj
BINDIR = bin

SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(patsubst $(SRCDIR)/%.c, $(OBJDIR)/%.o, $(SOURCES))
EXECUTABLE = $(BINDIR)/estimator

AR_ORDER ?= 30

all: $(EXECUTABLE)

analyze: all
	@if [ -z "$(WAVFILE)" ]; then \
		echo "Error: The WAVFILE variable is not defined." >&2; \
		exit 1; \
	fi
	@mkdir -p results data plots
	@echo "\n--- (1/3) Orchestrating full analysis (Python -> C) with AR Order = $(AR_ORDER) ---"
	@$(PYTHON) python/run_analysis.py $(WAVFILE) $(AR_ORDER)
	@echo "\n--- (2/3) Generating PSD plot with statistics ---"
	@$(PYTHON) python/plot_psd.py $(WAVFILE) data/plot_metrics.json
	@echo "\n--- (3/3) Cleaning up intermediate files ---"
	@rm -f data/audio_signal.txt data/metrics_c_output.txt data/peaks_output.txt data/psd_output.txt data/ar_coeffs.txt data/plot_metrics.json

$(EXECUTABLE): $(OBJECTS)
	@mkdir -p $(BINDIR)
	@echo "Linking the executable..."
	@$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

$(OBJDIR)/%.o: $(SRCDIR)/%.c
	@mkdir -p $(OBJDIR)
	@echo "Compiling $<..."
	@$(CC) $(CFLAGS) -c $< -o $@

clean:
	@echo "Cleaning up builds, outputs, and results..."
	@rm -rf $(OBJDIR) $(BINDIR) data plots results

.PHONY: all clean analyze