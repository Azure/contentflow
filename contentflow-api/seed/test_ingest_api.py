"""
Test script for the POST /api/ingest multipart document submission endpoint.

Usage:
    1. Place your test documents in a folder (default: ./input)
    2. Set BASE_URL to your API host (local or Azure)
    3. Set PIPELINE_ID to a valid pipeline ID from your Cosmos DB
    4. Run:
         python test_ingest_api.py

What this script does:
    - Step 1: Sends a multipart POST to /api/ingest with case details (form fields)
              and all document files found in the INPUT_DIR folder.
    - Step 2: Prints the 202 Accepted response (execution_id, blob_prefix, etc.).
    - Step 3: Polls GET /api/pipelines/executions/{execution_id} every few seconds
              until the pipeline completes, fails, or the poll limit is reached.
    - Step 4: Prints a final summary with the execution status.

Where to check responses:
    - CONSOLE:  All responses are printed to stdout.
    - SWAGGER:  Open {BASE_URL}/docs in a browser to test interactively.
    - COSMOS DB: Query the "executions" container for the returned execution_id.
    - BLOB:     Check Azure Blob Storage container → input/{caseId}_{executionId}/
                  • ProvidedDetails.json   — generated from form fields
                  • your uploaded documents — as submitted
                  • results.json           — written by the validation executor
"""

import os
import sys
import time
import json
import requests

# ──────────────────────────────────────────────
#  CONFIGURATION — edit these before running
# ──────────────────────────────────────────────

# API base URL (no trailing slash)
#   Local:  http://localhost:8090
#   Azure:  https://<your-container-app>.azurecontainerapps.io
BASE_URL = os.environ.get("CONTENTFLOW_API_URL", "https://api-doa37xivbuto4.wittywave-d4ca8c39.eastus.azurecontainerapps.io")

# A valid pipeline ID from Cosmos DB that is enabled and linked to the
# blob input discovery → content understanding → document validation flow.
PIPELINE_ID = os.environ.get("CONTENTFLOW_PIPELINE_ID", "draft_details_extraction_and_validation_pipeline_d0e4eeb7")

# Folder containing the test documents to upload (PDFs, images, etc.)
INPUT_DIR = os.environ.get("CONTENTFLOW_INPUT_DIR", os.path.join(os.path.dirname(__file__), "input"))

# Polling settings
POLL_INTERVAL_SECONDS = 5
POLL_MAX_ATTEMPTS = 60  # 5 minutes max

# ──────────────────────────────────────────────
#  SAMPLE CASE DATA — edit to match your rules
# ──────────────────────────────────────────────
CASE_DATA = {
    "caseId": "20261117253",
    "firstName": "Lizandra",
    "lastName": "Martes Sierra",
    "mailingAddress": "123 Calle Luna, San Juan, PR 00901",
    "dateOfBirth": "1985-06-15",
    "dateOfDeath": "",
    "fatherFirstName": "Juan",
    "fatherLastName": "Orozco",
    "motherFirstName": "Maria",
    "motherLastName": "Dones",
}


def collect_files(input_dir: str) -> list[str]:
    """Collect all supported files from the input directory."""
    allowed = {".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".tiff"}
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        print(f"       Create this folder and place your test documents inside it.")
        sys.exit(1)

    files = []
    for fname in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in allowed:
            files.append(os.path.join(input_dir, fname))

    if not files:
        print(f"ERROR: No supported document files found in: {input_dir}")
        print(f"       Supported extensions: {allowed}")
        sys.exit(1)

    return files


def submit_ingest(base_url: str, pipeline_id: str, case_data: dict, file_paths: list[str]) -> dict:
    """
    POST /api/ingest — multipart form data with case fields + files.
    Returns the parsed JSON response (IngestResponse).
    """
    url = f"{base_url}/api/ingest/"

    # Build form fields (sent as multipart form data, not JSON)
    form_data = {**case_data, "pipeline_id": pipeline_id}

    # Build file tuples: ("files", (filename, file_handle, content_type))
    file_handles = []
    files_payload = []
    for path in file_paths:
        fname = os.path.basename(path)
        fh = open(path, "rb")
        file_handles.append(fh)
        files_payload.append(("files", (fname, fh, "application/octet-stream")))

    print("=" * 60)
    print("STEP 1 — Submitting ingest request")
    print("=" * 60)
    print(f"  URL:         {url}")
    print(f"  Pipeline:    {pipeline_id}")
    print(f"  Case ID:     {case_data['caseId']}")
    print(f"  Files ({len(file_paths)}):")
    for p in file_paths:
        size_kb = os.path.getsize(p) / 1024
        print(f"    • {os.path.basename(p)}  ({size_kb:.1f} KB)")
    print()

    try:
        resp = requests.post(url, data=form_data, files=files_payload, timeout=120)
    finally:
        for fh in file_handles:
            fh.close()

    print(f"  HTTP Status: {resp.status_code}")

    if resp.status_code == 202:
        result = resp.json()
        print(f"  Response:")
        print(json.dumps(result, indent=4))
        return result
    else:
        print(f"  ERROR RESPONSE:")
        try:
            print(json.dumps(resp.json(), indent=4))
        except Exception:
            print(resp.text)
        sys.exit(1)


def poll_execution(base_url: str, execution_id: str) -> dict:
    """
    GET /api/pipelines/executions/{execution_id} — poll until terminal state.
    Returns the final execution record.
    """
    url = f"{base_url}/api/pipelines/executions/{execution_id}"

    print()
    print("=" * 60)
    print("STEP 2 — Polling execution status")
    print("=" * 60)
    print(f"  URL:          {url}")
    print(f"  Execution ID: {execution_id}")
    print(f"  Interval:     {POLL_INTERVAL_SECONDS}s (max {POLL_MAX_ATTEMPTS} attempts)")
    print()

    terminal_states = {"completed", "failed", "cancelled"}

    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"  [{attempt:3d}] Connection error: {e}")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown")
            print(f"  [{attempt:3d}] Status: {status}")

            if status in terminal_states:
                print()
                print("  Final execution record:")
                print(json.dumps(data, indent=4, default=str))
                return data
        elif resp.status_code == 404:
            print(f"  [{attempt:3d}] Execution not found (may still be creating)")
        else:
            print(f"  [{attempt:3d}] HTTP {resp.status_code}: {resp.text[:200]}")

        time.sleep(POLL_INTERVAL_SECONDS)

    print()
    print("  WARNING: Max poll attempts reached. The pipeline may still be running.")
    print(f"  Check manually: {url}")
    return {}


def print_summary(ingest_response: dict, execution_result: dict):
    """Print a final summary of the test run."""
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Case ID:        {ingest_response.get('case_id')}")
    print(f"  Execution ID:   {ingest_response.get('execution_id')}")
    print(f"  Blob Prefix:    {ingest_response.get('blob_prefix')}")
    print(f"  Files Uploaded:  {ingest_response.get('files_uploaded')}")
    print(f"  Pipeline:       {ingest_response.get('pipeline_name')} ({ingest_response.get('pipeline_id')})")

    final_status = execution_result.get("status", "unknown")
    print(f"  Final Status:   {final_status}")

    if final_status == "completed":
        print()
        print("  SUCCESS — Pipeline completed. Check these locations:")
    elif final_status == "failed":
        error = execution_result.get("error", "")
        print(f"  Error:          {error}")
        print()
        print("  FAILED — Check these locations for debugging:")
    else:
        print()
        print("  Check these locations:")

    blob_prefix = ingest_response.get("blob_prefix", "input/<caseId>_<executionId>/")
    print(f"    Blob Storage:  container → {blob_prefix}")
    print(f"        • ProvidedDetails.json  (generated from form fields)")
    print(f"        • results.json          (validation output)")
    print(f"    Cosmos DB:     executions container → id = {ingest_response.get('execution_id')}")
    print(f"    Swagger UI:    {BASE_URL}/docs")
    print(f"    Polling URL:   {BASE_URL}/api/pipelines/executions/{ingest_response.get('execution_id')}")
    print()


if __name__ == "__main__":
    print()
    print("ContentFlow Ingest API — Integration Test")
    print("=" * 60)

    if PIPELINE_ID == "<YOUR_PIPELINE_ID>":
        print("ERROR: Set PIPELINE_ID to a valid pipeline ID before running.")
        print("       Either edit this file or set CONTENTFLOW_PIPELINE_ID env var.")
        print()
        print("       Find pipeline IDs via:")
        print(f"         GET {BASE_URL}/api/pipelines/")
        sys.exit(1)

    # Collect document files from input folder
    file_paths = collect_files(INPUT_DIR)

    # Step 1: Submit ingest
    ingest_response = submit_ingest(BASE_URL, PIPELINE_ID, CASE_DATA, file_paths)

    # Step 2: Poll until complete
    execution_id = ingest_response["execution_id"]
    execution_result = poll_execution(BASE_URL, execution_id)

    # Step 3: Summary
    print_summary(ingest_response, execution_result)
