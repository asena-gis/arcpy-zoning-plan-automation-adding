# ArcPy Zoning Plan Calculation and Automation Engine

This repository contains an ArcPy-based Python automation tool engineered for urban planners, municipal authorities, and GIS professionals. The script entirely replaces manual data workflows by dynamically calculating core urban development metrics—including **Zoning Coverage Ratios (TAKS)**, **Floor Area Ratios (KAKS)**, and **Building Height Regulations (Kat Nizamı)**—and automating their geometric annotation placement directly onto zoning block centroids.

## 🚀 Key Features

- **Automated TAKS & KAKS Engines:** Computes and verifies maximum building footprints and total allowable floor areas from raw attribute datasets.
- **Building Height Regulations (Kat Nizamı):** Dynamically processes structural parameters, tracks max floor/story counts, and supports layout classifications.
- **Zoning & Building Layout Support:** Native handling for localized structural arrangements such as **Detached Building Types** (Ayrık Nizam) alongside standard blocks.
- **Spatial Labeling Automation:** Automatically identifies geometric centroids of custom zoning polygons to systematically generate clean, non-overlapping map annotations.

## 📋 Technical Terminology Mapping (TR ↔ EN)

To bridge the gap between Turkish municipal frameworks and global GIS development standards, this engine translates spatial metrics using industry-standard English equivalents:
- **TAKS:** Zoning Coverage Ratio (ZCR) / Site Coverage
- **KAKS:** Floor Area Ratio (FAR) / Plot Ratio
- **Kat Nizamı:** Building Height Regulation / Building Order System
- **Ayrık Nizam:** Detached Building Type / Detached Layout Order
- **Kat Sayısı:** Story Count / Number of Floors

## 🛠️ Prerequisites

- **ArcGIS Pro** (Recommended) or **ArcGIS Desktop**
- **Python 3.x** (or Python 2.7 for legacy ArcMap environments)
- `arcpy` site package (bundled natively with Esri ArcGIS installations)

## 💻 Quick Start

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   ```
2. **Configure Environment Variables:** Open the script and modify the local workspace parameters (`arcpy.env.workspace`), attribute field names, and targeted feature classes to match your local file geodatabase (`.gdb`) structure.
3. **Execute the Script:** Run the file through the integrated ArcGIS Python window, ArcGIS Notebooks, or your preferred external IDE.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
