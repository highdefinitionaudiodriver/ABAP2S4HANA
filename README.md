# ABAP2S4HANA Migration Tool

A powerful dual-mode (GUI and CLI) application built in Python to seamlessly migrate and convert SAP ECC ABAP code for S/4HANA compatibility.

## Features

- **Dual-Mode Interface**: Provides a user-friendly Tkinter GUI as well as a headless CLI mode for automated workflows.
- **Syntax Modernization**: Automatically updates older ABAP syntax to modern S/4HANA standards.
- **Comprehensive Conversion**: Handles the conversion of standard tables, BAPIs, and Function Modules (FMs) to their S/4HANA equivalents.
- **Impact Analysis Reporting**: Generates detailed migration and impact analysis reports in HTML and CSV formats.
- **Safe Execution**: Automatically creates backups of your original source files before processing.
- **Multiple Languages**: Internationalized interface with built-in language settings.
- **Highly Configurable**: Configure source/target SAP versions (e.g., ECC 6.08 to S/4HANA 2023), file encoding, ABAP extensions, and SAP module filters (FI/CO, MM, SD, etc.).

## Installation

1. Ensure Python 3.8+ is installed.
2. Clone the repository and install any required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Mode
Simply run the application without arguments to launch the graphical user interface:
```bash
python main.py
```

### CLI Mode
Use standard arguments to execute migrations directly from the command line:
```bash
python main.py -i <input_directory> -o <output_directory> [options]
```

**Common CLI Options:**
- `-i, --input`: Input folder containing ABAP files
- `-o, --output`: Output folder for converted ABAP files
- `-e, --encoding`: Source encoding (default: `utf-8`)
- `--source-version`: Source SAP version (e.g., `ECC 6.08`)
- `--target-version`: Target S/4HANA version (e.g., `S/4HANA 2023`)
- `--module`: SAP module filter (default: `ALL`)
- `--report-format`: Output format for the migration report (`HTML`, `CSV`, or `Both`)

Use `python main.py --help` to see all available flags for toggling modernization and backups.

## Tests

Integration and conversion tests are provided. Run them using:
```bash
python test_conversion.py
```
