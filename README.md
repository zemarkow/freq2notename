# freq2notename

Toolkit for converting audio frequencies into musical note names and vice versa for music transcription and tuning

## Introduction and Getting Started

### Please see the guide PDF for installation instructions and tutorials with screen photos!

Welcome to freq2notename!  This is a software package for converting audio frequencies into musical note names and vice versa.  This functionality has several uses, including checking the tuning of musical instruments and transcribing sheet music notation from audio recordings and their spectrograms.

This toolkit is organized into two main programs:
1. *freq2notename_dashboard:* a graphical user interface where you can convert between frequencies and notes in text blocks with simple point-and-click, copy-and-paste actions, and
2. *freq2notename/utils.py:* a code module that defines the toolkit's core functions, which you can optionally import and call in other Python scripts.  This module also supports converting within text blocks.

freq2notename can perform these conversions within human-readable blocks of text containing frequencies or note names interspersed with blank lines and commentary, like the comments you might write when analyzing where peaks/hot spots occur in an audio recording's spectrogram to transcribe it into music notation.  In each line of text, simply put a space, comma, tab, forward slash (/), or vertical bar (|) between frequencies or note names.  After the frequencies or note names in each line, place a percent sign (%) before any commentary.  This toolkit supports variable A4 tunings, +/- cents deviations, and transposition for different instruments.

## Installing and Running freq2notename

#### See the guide PDF for a version of these instructions with screen photos!

### Method 1:
#### Recommended if you only need the point-and-click dashboard interface

If you are not using freq2notename for Python programming, simply go to the dashboard_downloads folder and download the standalone dashboard file for your computer's operating system (e.g., Windows, macOS, etc.).  Then double-click on the file to run it.  If Method 1 does not work for you or you don't see a standalone dashboard for your computer's operating system, try Method 2.

### Method 2:
#### Recommended as a backup if Method 1 doesn't work for you

If Method 1 fails or we don't have a single-file dashboard available for your computer's operating system:
1. Install the latest stable version of Python from python.org unless you have already installed the official release of Python 3.8 or later (not just the Python version that may have come with your computer),
2. Download this full freq2notename GitHub repository as a .zip file using the "Download ZIP" button near the upper-right of this main GitHub page, and then unzip it anywhere you like on your computer,
3. Go into the unzipped freq2notename folder on your computer, right-click or Ctrl-click on freq2notename_dashboard.py, go to "Open With", and select IDLE to open that file in IDLE,
4. Within IDLE, go up to and click on the Run menu at the top of the screen, and then click "Run Module."

### Method 3:
#### Recommended for Python programmers who want to use freq2notename's backend in other scripts

Use pip to install freq2notename as a Python package (e.g., by running "pip install freq2notename" in a system terminal).  Then, to run the dashboard interface, run "python3 -m freq2notename" in a system terminal.  To use freq2notename's backend utility functions in another Python script, import freq2notename.utils in that script.  If Method 3 does not work for you, try Method 2.

## Other Useful Software

To interactively create and navigate spectrograms of your music with audio playback, I recommend the free program Audacity.  To type music notation and create scores, I recommend the programs MuseScore 4 (free), Sibelius, or Finale.  To perform a wide range of music processing and feature analysis tasks within your own Python scripts, I also recommend the free software package librosa.  I learned about librosa after I wrote freq2notename, and librosa also supports interconverting between frequencies and note names one at a time.  However, I still use freq2notename for the convenience and efficiency of interconverting within commented blocks of text via an interactive graphical interface.

