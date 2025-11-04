from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pathlib import Path

app = FastAPI(
    title="🎓 University Fake Data API",
    description="Serves CSVs for demo mode — Students, Finance, and Akreditasi datasets.",
    version="1.1.0"
)

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

@app.get("/", response_class=HTMLResponse)
def home():
    """Simple HTML dashboard showing all datasets."""
    return """
    <h2>🎓 University Fake Data API</h2>
    <p>This API serves demo CSV files for the report generator.</p>
    <ul>
        <li><a href="/data/students">/data/students</a> — Students dataset</li>
        <li><a href="/data/finance">/data/finance</a> — Finance dataset</li>
        <li><a href="/data/akreditasi">/data/akreditasi</a> — Akreditasi dataset</li>
    </ul>
    <p>Add <code>?format=json</code> to get JSON instead of HTML (e.g. <a href="/data/students?format=json">/data/students?format=json</a>).</p>
    """

@app.get("/data/{dataset}")
def list_csvs(dataset: str, format: str = Query("html", enum=["html", "json"])):
    """
    List all available CSVs for a dataset.

    Example:
      - /data/students → HTML view
      - /data/students?format=json → JSON for app ingestion
    """
    folder = DATA_DIR / dataset
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' not found.")

    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail=f"No CSV files found for '{dataset}'.")

    if format == "json":
        # Return structured JSON for programmatic access
        data = [
            {
                "filename": csv.name,
                "url": f"/download/{dataset}/{csv.name}"
            }
            for csv in csv_files
        ]
        return JSONResponse(content=data)

    # Default = HTML page listing CSVs
    html = f"<h3>Available {dataset.capitalize()} CSVs:</h3><ul>"
    for csv in csv_files:
        html += f'<li><a href="/download/{dataset}/{csv.name}">{csv.name}</a></li>'
    html += "</ul>"
    return HTMLResponse(html)

@app.get("/download/{dataset}/{filename}")
def download_csv(dataset: str, filename: str):
    """Serve a single CSV file for download."""
    file_path = DATA_DIR / dataset / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename
    )
