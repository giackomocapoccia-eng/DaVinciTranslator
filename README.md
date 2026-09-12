# DaVinciTranslator

**Automated subtitle processing pipeline built with Python, FFmpeg, Whisper and machine translation.**

DaVinciTranslator is a Python application that automates the creation and translation of subtitles from English-language video content.

The pipeline extracts audio with FFmpeg, transcribes speech using OpenAI Whisper with word-level timestamps, generates synchronized SRT subtitles, translates them into Italian and applies custom terminology corrections for DaVinci Resolve.

The project focuses on practical software-development challenges including automation, modular architecture, file processing, text-processing algorithms, synchronization and error handling.

> 🚧 **Project Status:** Active development  
> The core processing pipeline is functional. Current work focuses on improving subtitle segmentation, translation distribution and readability.

## Features

* 🎬 Automatic video detection
* 🎵 Audio extraction with FFmpeg
* 🧠 Speech-to-text transcription with Whisper
* ⏱️ Word-level timestamp processing
* 📄 Automatic SRT subtitle generation
* 🌍 English-to-Italian translation
* 🎞️ DaVinci Resolve terminology corrections
* ✂️ Subtitle segmentation based on readability constraints
* 📁 Separate English and Italian subtitle output

---

## How It Works

The current processing pipeline is:

```text
Video
  ↓
FFmpeg audio extraction
  ↓
Whisper transcription
  ↓
Word timestamps
  ↓
Subtitle segmentation
  ↓
English SRT
  ↓
Translation
  ↓
DaVinci Resolve terminology correction
  ↓
Italian SRT
```

The goal is not only to translate the transcription, but also to maintain readable subtitle blocks while preserving synchronization with the original video.

---

## Technologies

* **Python**
* **FFmpeg**
* **OpenAI Whisper**
* **Deep Translator**
* **SRT subtitle format**
* **Git / GitHub**

---

## Project Structure

```text
DaVinciTranslator/
│
├── DaVinciTranslator.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
│
└── Modules/
    ├── audio.py
    ├── transcribe.py
    ├── subtitles.py
    └── translate.py
```

### Main modules

**`DaVinciTranslator.py`**
Main application entry point. Detects available videos and coordinates the processing pipeline.

**`Modules/audio.py`**
Handles audio extraction from video files using FFmpeg.

**`Modules/transcribe.py`**
Runs Whisper transcription and retrieves word-level timestamps.

**`Modules/subtitles.py`**
Builds subtitle blocks and manages timing, duration and line-length constraints.

**`Modules/translate.py`**
Translates subtitle groups into Italian and applies terminology corrections specific to DaVinci Resolve.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/giackomocapoccia-eng/DaVinciTranslator.git
cd DaVinciTranslator
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

FFmpeg must be installed on the system and available from the command line.

Check the installation with:

```bash
ffmpeg -version
```

---

## Usage

Place the video you want to process inside the `Video/` folder.

Then run:

```bash
python DaVinciTranslator.py

The application detects supported video files and allows the user to select the video to process.

Supported formats include:

```text
.mp4
.mov
.mkv
.avi
```

The generated subtitle files are saved in the output folder.

Example:

```text
Output/
├── DaVinciResolve_EN.srt
└── DaVinciResolve_IT.srt
```

---

## Subtitle Processing

Subtitle generation is one of the main areas of development in the project.

The algorithm works with Whisper word timestamps and attempts to create subtitle blocks that:

* remain synchronized with speech;
* avoid excessively long captions;
* maintain readable line lengths;
* avoid very short subtitle durations;
* preserve natural sentence structure where possible.

Translation introduces an additional challenge because English and Italian sentences often have different lengths and word order.

For this reason, DaVinciTranslator includes custom logic for distributing translated text across the original subtitle timing intervals.

---

## DaVinci Resolve Terminology

The translation system also applies terminology corrections for words and expressions commonly used in DaVinci Resolve.

Examples include:

```text
timeline
Media Pool
Project Manager
Fusion
Fairlight
keyframe
tracker
color grading
voice-over
```

This helps prevent generic machine translations from replacing technical terms that should remain consistent with DaVinci Resolve terminology.

---

## Current Development

Current work is focused on improving:

* subtitle segmentation;
* maximum line-length handling;
* translated text distribution;
* grammatical phrase preservation;
* subtitle readability;
* translation reliability;
* automated subtitle quality tests.

---

## Roadmap

* [x] Automatic video detection
* [x] FFmpeg audio extraction
* [x] Whisper integration
* [x] English SRT generation
* [x] Translation engine
* [x] DaVinci Resolve terminology corrections
* [ ] Improve subtitle segmentation algorithm
* [ ] Improve translated subtitle distribution
* [ ] Add automated tests
* [ ] Add command-line options
* [ ] Add graphical user interface
* [ ] Add multi-language support

---

## Motivation

DaVinciTranslator started as a personal project to explore how speech recognition, translation and subtitle processing can be combined into a practical Python application.

The project is also an opportunity to work on real software-development problems such as modular architecture, file processing, external tools, error handling, text-processing algorithms and automated testing.

---

## Author

**Giacomo Capoccia**

GitHub: [@giackomocapoccia-eng](https://github.com/giackomocapoccia-eng)

---

## License

This project is distributed under the license included in the repository.
