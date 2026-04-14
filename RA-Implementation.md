# Requirements Analysis and Implementation Plan: Tailoring Order OCR & Management System (Native Windows Edition)

## 1. Project Overview
The objective is to develop a comprehensive cross-platform system (iOS mobile application and Next.js web application) to automate the digitization of handwritten tailoring order forms. The system will leverage a local Vision-Language Model (VLM) for Optical Character Recognition (OCR) to extract measurements and customer details, providing an intuitive split-screen UI for human-in-the-loop verification before persisting data to a relational database. 

## 2. System Architecture
* **Mobile Client:** iOS native or cross-platform (React Native / SwiftUI) optimized for camera control and bounding-box overlays.
* **Web Client:** Next.js (React) for desktop-class data correction and master list dashboard viewing.
* **Backend API:** Python (FastAPI) handling asynchronous requests, image processing, and database transactions.
* **Database:** PostgreSQL for robust relational mapping of time-series order data and structured JSON measurements.
* **AI / Vision Engine:** Qwen3.5-9B (4-bit quantized) served locally via **LM Studio**.
* **Host Environment:** Native Windows environment. No Windows Subsystem for Linux (WSL) or Linux distributions will be used.

## 3. Hardware & Resource Specifications
* **System Memory:** 24 GB RAM.
* **GPU:** 12 GB VRAM.
* **Optimization Strategy:** The 12GB VRAM constraint is perfectly managed by using the 4-bit quantized GGUF version of Qwen3.5-9B in LM Studio. This reduces the model footprint to ~6-7GB in VRAM, leaving ample room (5-6GB) for Windows OS overhead, OpenCV processing, and the vision context window.

## 4. Functional Requirements (FR)

### FR1: Guided Image Capture
The client applications must provide a camera interface with a bounding box overlay. This overlay will guide the user to correctly align the physical form, specifically targeting the four black fiducial markers located in the corners of the document.

### FR2: Image Preprocessing Pipeline
Upon receiving the image payload, the native Windows Python backend must:
1.  Utilize OpenCV to detect the fiducial markers.
2.  Apply a Perspective Transform (Homography) to flatten and crop the image.
3.  Convert the image to grayscale and enhance contrast.
4.  Resize the longest edge to a maximum of 1280px to prevent token explosion and avoid Out-of-Memory (OOM) errors.

### FR3: VLM OCR Extraction (via LM Studio)
The preprocessed image is converted to a base64 string and passed to LM Studio's Local Inference Server (which mimics an OpenAI-compatible REST API). The prompt must strictly enforce JSON output matching the target schema (e.g., student name, classification, upper/lower measurements).

### FR4: Human-in-the-Loop Correction (CRUD)
The system must not auto-commit OCR results. 
* The client will receive the uncommitted JSON payload and display it in a split-screen or overlay UI.
* The UI will display the cropped original image alongside the pre-filled digital form.
* The user must be able to edit any misread characters or incorrect numbers before confirming the submission.

### FR5: Data Persistence and Storage Constraints
* Upon user confirmation, only the verified JSON data is transmitted to the `/orders` endpoint for database insertion.
* **Strict Storage Rule:** The system must strictly discard and permanently delete the raw and preprocessed images from the native Windows temporary directories (`%TEMP%`) to conserve disk space. No image blobs will be saved in the database.

### FR6: Master List & Database Lookup
The application must provide a dashboard interface querying the PostgreSQL database. Users must be able to view, filter, and export a master list of all ordered uniforms, indexed efficiently by year, month, and school classification.

## 5. Non-Functional Requirements (NFR)
* **Performance:** The local LM Studio inference pipeline should complete within 5-10 seconds per form.
* **Environment Independence:** Because the system is built natively on Windows, file paths (e.g., temporary image saving) must use Python's `os.path` or `pathlib` dynamically to avoid hardcoded `C:\` paths, ensuring future cloud migration to Linux-based Modal containers won't break the application.
* **Reliability:** The FastAPI backend must implement strict error handling for OCR failures, returning graceful fallbacks to the client for manual data entry if the image is entirely unreadable.

## 6. Implementation Roadmap

### Phase 1: Native Windows Environment & Backend Foundation
* Configure **LM Studio** on Windows, load the Qwen3.5-9B 4-bit model, and start the Local Inference Server (typically on port 1234).
* Install PostgreSQL using the native Windows installer and configure the local database.
* Set up a Python virtual environment (`venv` or `Conda`) natively on Windows.
* Develop the FastAPI backend and OpenCV preprocessing pipeline.

### Phase 2: Client Interface Development
* Develop the Next.js web application focusing on the Master List data grid and the desktop split-screen validation UI.
* Develop the iOS application focusing on optimized camera capture and mobile-friendly validation states.

### Phase 3: Integration & Tuning
* Connect the FastAPI backend to the LM Studio API endpoint.
* Conduct batch testing with varying handwriting samples to refine the system prompt and temperature parameters of the VLM.
* Monitor Windows Task Manager (Performance -> GPU) to ensure VRAM allocation stays comfortably below 12GB during inference.

### Phase 4: Cloud Transition Readiness
* Modularize the FastAPI application so that the endpoint logic can eventually be deployed to Modal or another cloud provider with minimal refactoring.
