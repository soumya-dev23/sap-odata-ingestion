# SAP OData Incremental Data Extractor

A robust Python script designed to extract customer ledger item data (FBL5N) page-by-page from SAP OData services using pagination (`$skip` / `$top`), memory-efficient generators, and incremental CSV writing. It includes built-in HTTP error handling and automatic retry logic with exponential backoff.

---

## Features

* **Memory-Efficient Generator Pattern**: Fetches data in batches to prevent high memory consumption when handling large datasets.
* **Incremental CSV Writing**: Appends each batch directly to a CSV file (`utf-8-sig` encoded for Excel compatibility) as it is fetched.
* **HTTP Error Handling**: Leverages `response.raise_for_status()` to catch and log client (`4xx`) and server (`5xx`) errors cleanly.
* **Automatic Retry Mechanism**: Implements retries with exponential backoff to handle temporary network glitches or SAP server timeouts gracefully.
* **Self-Cleaning File Check**: Automatically removes existing output files before running to prevent data duplication, with a safety warning if the file is currently locked/open.

---

## Prerequisites

Make sure you have Python installed along with the required libraries. You can install the dependencies using `pip`:

```bash
pip install requests pandas urllib3

#### Configuration
Open the script and configure the following variables at the top of the file to match your environment:

SAP_USER: Your SAP username.

SAP_PASS: Your SAP password.

url: The target OData EntitySet URL.

output_file: The destination CSV file name (default: sap_zfbl5n_prd_all.csv).

E####### Execution Flow:
File Check: Verifies if the output CSV already exists and deletes it to start fresh. (If the file is open in Excel or another program, a PermissionError message will guide you to close it).

Batch Fetching: Connects to SAP, bypassing self-signed SSL warnings, and downloads data page-by-page (default batch size: 100 rows).

Resilience: If a network or HTTP error occurs, the script automatically retries up to 3 times, doubling the wait time between each attempt (exponential backoff).

Data Cleanup: Automatically strips technical metadata columns like __metadata.

Completion: Appends records to the CSV and outputs a final success message with the total row count.

Code Overview
fetch_sap_generator(): A Python generator function handling session management, query parameters, error catching, retries, and yielding record batches on demand.

pandas Integration: Converts raw JSON dictionaries into DataFrames batch-by-batch for smooth tabular handling and CSV persistence.