# =========================
# FILE: webapp/main.py
# FastAPI app entrypoint
# =========================
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import uuid
import asyncio
import traceback

# Ensure project root is importable (so DataAggregator, Config, etc. can be imported)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import your existing modules (adjust names if your files differ)
try:
    from config import Config
    from data_aggregator import DataAggregator
    from data_processor import DataProcessor
    from report_generator import ReportGenerator
    from output_manager import OutputManager
except Exception as e:
    # If import error, still allow app to start; errors will surface when generating
    print("Warning: could not import project modules at startup:", e)

app = FastAPI(title="University AI Report Generator (Web)")

# Serve static files (frontend)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Allow local javascript access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Task store: { task_id: {"progress": int, "status": str, "filename": str|None } }
TASKS = {}

# Serve the frontend index
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/generate")
async def api_generate(request: Request, background: BackgroundTasks):
    """
    Start report generation.
    Body JSON: { "report_type": "academic"|"cooperation"|"accreditation"|..., "custom_prompt": "..." }
    Returns: { "task_id": "<uuid>" }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    report_type = body.get("report_type", "academic")
    custom_prompt = body.get("custom_prompt", "")

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"progress": 0, "status": "Queued", "filename": None}

    # launch background coroutine
    background.add_task(_background_generate, task_id, report_type, custom_prompt)
    return JSONResponse({"task_id": task_id})


@app.get("/api/progress/{task_id}")
def api_progress(task_id: str):
    """
    Return task progress object: { progress: int, status: str, filename?: str }
    """
    if task_id not in TASKS:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return JSONResponse(TASKS[task_id])


@app.get("/api/download/{filename}")
def api_download(filename: str):
    """
    Serve generated report files from reports/ folder.
    Save paths returned by OutputManager are used when generating.
    """
    # search in reports dir and subdirs
    base = Path.cwd() / "reports"
    candidates = list(base.rglob(filename))
    if not candidates:
        return JSONResponse({"error": "file not found"}, status_code=404)
    path = candidates[0]
    return FileResponse(path, filename=path.name)


async def _background_generate(task_id: str, report_type: str, custom_prompt: str):
    """
    Background worker that runs the full pipeline using existing modules.
    Updates TASKS[task_id]["progress"] and ["status"].
    """
    try:
        # 1. Prepare config & components
        TASKS[task_id].update({"progress": 5, "status": "Initializing components..."})
        await asyncio.sleep(0)  # allow event loop to schedule

        # Load config and decide on ingestion mode (Config uses env AGGREGATION_MODE)
        cfg = Config()

        # DataAggregator initialized with cache dir from cfg
        agg = DataAggregator(cache_dir=str(cfg.CACHE_DIR))
        processor = DataProcessor()
        # Instantiate ReportGenerator with API key only if available, else instantiate minimally
        try:
            api_key = cfg.get_api_key()
        except Exception:
            api_key = None
        model_name = cfg.get_setting("model_name", "gemini-2.5-flash")
        rg = ReportGenerator(api_key=api_key, model_name=model_name)
        out = OutputManager()

        # 2. Ingest
        TASKS[task_id].update({"progress": 10, "status": "Ingesting data..."})
        sources = cfg.get_ingestion_sources()
        # aggregator.ingest expects a list of sources; pass cache=True to save local copies
        combined_df = agg.ingest(sources, cache=True)

        # 3. Clean/process
        TASKS[task_id].update({"progress": 30, "status": "Cleaning and processing data..."})
        cleaned = processor.clean_data(combined_df)

        TASKS[task_id].update({"progress": 60, "status": "Analyzing data..."})
        analysis = processor.analyze_data(cleaned)

        # 4. Generate AI report (pass custom prompt via data_summary if needed)
        TASKS[task_id].update({"progress": 70, "status": "Generating AI report..."})
        # If your ReportGenerator.generate_report signature differs, adapt here.
        report_text, usage_info = rg.generate_report(data_summary=analysis, report_type=report_type, custom_prompt=custom_prompt)

        # If generator supports extra prompt injection, you can post-process report_text or modify generate_report.
        # Save report
        TASKS[task_id].update({"progress": 90, "status": "Saving report..."})
        metadata = {
            "source_files": sources,
            "analysis": analysis,
            "validation": rg.validate_report(report_text, analysis),
            "token_usage": usage_info
        }
        save_res = out.save_report(report_text, report_type=f"{report_type}_report", metadata=metadata)

        # save_res expected to be dict {"markdown_path": "...", "html_path": "..."}
        # normalize filename to return to frontend
        filename = None
        if isinstance(save_res, dict):
            # prefer HTML if available
            html_p = save_res.get("html_path")
            md_p = save_res.get("markdown_path")
            filename = Path(html_p).name if html_p else (Path(md_p).name if md_p else None)
        else:
            # older OutputManager returns string path
            filename = Path(save_res).name if save_res else None

        TASKS[task_id].update({"progress": 100, "status": "Completed", "filename": filename})

    except Exception as e:
        # record error and stack
        tb = traceback.format_exc()
        print(f"Error in background task {task_id}:", tb)
        TASKS[task_id].update({"progress": -1, "status": f"Error: {str(e)}"})
