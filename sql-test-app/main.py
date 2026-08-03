"""
Simple SQL test endpoint — deploy to Container App to test SQL connectivity from within the VNet.
Also downloads files from source blob and uploads to target blob.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pyodbc
import os
import json
import httpx
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = FastAPI()

# Connection string — reads from env var
SQL_CONNECTION_STRING = os.environ.get(
    "SQL_CONNECTION_STRING",
    "Driver={ODBC Driver 18 for SQL Server};Server=tcp:saluddigitalprodsql.database.windows.net,1433;Database=saluddigital-DEV-SARSP-sql;Uid=svc_contentflow;Pwd=ComplexPass@word1Admin#1234;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
)

# Source blob (customer's storage) — use managed identity
SOURCE_ACCOUNT_NAME = "saluddigitalprodstorage"

# Target blob (your storage account) — also use managed identity
TARGET_ACCOUNT_NAME = os.environ.get("TARGET_STORAGE_ACCOUNT", "st3vxqxhg364vru")
TARGET_CONTAINER = os.environ.get("TARGET_CONTAINER", "sql-fetch-data")

# Shared credential for both source and target
credential = DefaultAzureCredential()

SQL_QUERY = """
SELECT
    up.CaseNumber,
    s.StatusAlias,
    pt.ProcessAlias,
    r.RequirementAlias AS RequirementName,
    upr.FileId,
    'https://saluddigitalprodstorage.blob.core.windows.net/uploadedfilesr/' + CAST(upr.FileId AS NVARCHAR(100)) AS Fileurl
FROM process.UserProcess up
LEFT JOIN process.ProcessType pt ON pt.Id = up.ProcessTypeId
LEFT JOIN sct.Status s ON s.Id = up.CurrentStatusId
LEFT JOIN process.UserProcessRequirement upr ON upr.ProcessId = up.Id
LEFT JOIN process.Requirement r ON r.Id = upr.RequirementId
WHERE r.RequirementTypeId = 2
  AND upr.IsComplete = 1
  AND upr.FileId IS NOT NULL
  AND up.CurrentStatusId <> -12
"""


@app.get("/")
def health():
    return {"status": "ok", "service": "sql-test"}


@app.get("/query")
def query_sql():
    """Query the SARSP SQL database and return results."""
    try:
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
        conn.close()
        return JSONResponse(content={
            "status": "success",
            "row_count": len(rows),
            "columns": columns,
            "data": rows
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


@app.get("/query/{case_number}")
def query_case(case_number: str):
    """Query documents for a specific case number."""
    try:
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        query = SQL_QUERY.replace(
            "WHERE r.RequirementTypeId = 2",
            f"WHERE up.CaseNumber = ? AND r.RequirementTypeId = 2"
        )
        cursor.execute(query, (case_number,))
        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
        conn.close()
        return JSONResponse(content={
            "status": "success",
            "case_number": case_number,
            "row_count": len(rows),
            "columns": columns,
            "data": rows
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


@app.get("/list-containers")
def list_containers():
    """List all containers in the source storage account."""
    try:
        source_client = BlobServiceClient(f"https://{SOURCE_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)
        containers = [c.name for c in source_client.list_containers()]
        return JSONResponse(content={"status": "success", "containers": containers})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})


@app.get("/list-blobs/{container_name}")
def list_blobs(container_name: str):
    """List blobs in a container (first 20)."""
    try:
        source_client = BlobServiceClient(f"https://{SOURCE_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)
        container_client = source_client.get_container_client(container_name)
        blobs = []
        for i, blob in enumerate(container_client.list_blobs()):
            if i >= 20:
                break
            blobs.append(blob.name)
        return JSONResponse(content={"status": "success", "container": container_name, "blobs": blobs, "count": len(blobs)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})


@app.get("/fetch-and-store/{case_number}")
def fetch_and_store(case_number: str):
    """Query SQL, download files from source blob via HTTP, upload to target blob."""
    results = {"case_number": case_number, "files": [], "errors": []}

    try:
        # Step 1: Query SQL
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        query = SQL_QUERY + " AND up.CaseNumber = ?"
        cursor.execute(query, (case_number,))
        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
        conn.close()

        if not rows:
            return JSONResponse(content={"status": "no_documents", "case_number": case_number, "row_count": 0})

        # Step 2: Connect to source and target blob (managed identity)
        source_client = BlobServiceClient(f"https://{SOURCE_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)
        target_client = BlobServiceClient(f"https://{TARGET_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)

        # Step 3: Download from source, upload to target
        for row in rows:
            file_id = row.get("FileId", "unknown")
            file_url = row.get("Fileurl", "")
            req_name = row.get("RequirementName", "Unknown")

            try:
                # Try multiple container name variants
                file_data = None
                attempts = [
                    ("uploadedfiles", file_id),
                    ("uploadedfilesr", file_id),
                    ("uploadedfiles", f"r/{file_id}"),
                    ("uploadedfiles", f"r{file_id}"),
                ]
                
                last_error = None
                for container, blob in attempts:
                    try:
                        source_blob_client = source_client.get_blob_client(container=container, blob=blob)
                        download = source_blob_client.download_blob()
                        file_data = download.readall()
                        break  # Success
                    except Exception as attempt_err:
                        last_error = attempt_err
                        continue
                
                if file_data is None:
                    raise last_error or Exception("All download attempts failed")

                # Upload to target
                target_blob_path = f"input/{case_number}/{file_id}"
                target_blob_client = target_client.get_blob_client(container=TARGET_CONTAINER, blob=target_blob_path)
                target_blob_client.upload_blob(file_data, overwrite=True)

                results["files"].append({
                    "file_id": file_id,
                    "requirement": req_name,
                    "size_bytes": len(file_data),
                    "target_path": f"{TARGET_CONTAINER}/{target_blob_path}",
                    "status": "success"
                })
            except Exception as e:
                results["errors"].append({
                    "file_id": file_id,
                    "requirement": req_name,
                    "error": str(e)
                })

        results["status"] = "completed"
        results["total_files"] = len(rows)
        results["uploaded"] = len(results["files"])
        results["failed"] = len(results["errors"])
        return JSONResponse(content=results)

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})


@app.get("/fetch-and-store-all")
def fetch_and_store_all():
    """Query ALL cases from SQL, download files, upload to target blob."""
    results = {"files": [], "errors": [], "cases": set()}

    try:
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
        conn.close()

        if not rows:
            return JSONResponse(content={"status": "no_documents", "row_count": 0})

        source_client = BlobServiceClient(f"https://{SOURCE_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)
        target_client = BlobServiceClient(f"https://{TARGET_ACCOUNT_NAME}.blob.core.windows.net", credential=credential)

        cases = set()
        for row in rows:
            file_id = row.get("FileId", "unknown")
            file_url = row.get("Fileurl", "")
            case_num = row.get("CaseNumber", "unknown")
            req_name = row.get("RequirementName", "Unknown")
            cases.add(case_num)

            try:
                # Try multiple container name variants
                file_data = None
                attempts = [
                    ("uploadedfiles", file_id),
                    ("uploadedfilesr", file_id),
                    ("uploadedfiles", f"r/{file_id}"),
                    ("uploadedfiles", f"r{file_id}"),
                ]
                last_error = None
                for container, blob in attempts:
                    try:
                        source_blob_client = source_client.get_blob_client(container=container, blob=blob)
                        download = source_blob_client.download_blob()
                        file_data = download.readall()
                        break
                    except Exception as attempt_err:
                        last_error = attempt_err
                        continue
                
                if file_data is None:
                    raise last_error or Exception("All download attempts failed")

                target_blob_path = f"input/{case_num}/{file_id}"
                target_blob_client = target_client.get_blob_client(container=TARGET_CONTAINER, blob=target_blob_path)
                target_blob_client.upload_blob(file_data, overwrite=True)

                results["files"].append({
                    "case_number": case_num,
                    "file_id": file_id,
                    "requirement": req_name,
                    "size_bytes": len(file_data),
                    "target_path": f"{TARGET_CONTAINER}/{target_blob_path}",
                    "status": "success"
                })
            except Exception as e:
                results["errors"].append({
                    "case_number": case_num,
                    "file_id": file_id,
                    "requirement": req_name,
                    "error": str(e)
                })

        results["status"] = "completed"
        results["total_cases"] = len(cases)
        results["total_files"] = len(rows)
        results["uploaded"] = len(results["files"])
        results["failed"] = len(results["errors"])
        results["cases"] = list(cases)
        return JSONResponse(content=results)

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
