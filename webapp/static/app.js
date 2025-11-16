// =========================
// FILE: webapp/static/app.js
// =========================
document.getElementById("generateBtn").addEventListener("click", startGeneration);

function startGeneration() {
    const reportType = document.getElementById("reportType").value;
    const customPrompt = document.getElementById("customPrompt").value;

    // Reset UI
    setProgress(0);
    document.getElementById("status").innerText = "Queued";
    document.getElementById("result").innerHTML = "";

    // Start generation
    fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            report_type: reportType,
            custom_prompt: customPrompt
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.task_id) {
            pollProgress(data.task_id);
            document.getElementById("status").innerText = "Started";
        } else {
            document.getElementById("status").innerText = "Failed to start";
        }
    })
    .catch(err => {
        console.error("Start error:", err);
        document.getElementById("status").innerText = "Error starting task";
    });
}

function pollProgress(taskId) {
    const interval = setInterval(() => {
        fetch(`/api/progress/${taskId}`)
            .then(res => res.json())
            .then(data => {
                const p = Number(data.progress) || 0;
                setProgress(p);
                document.getElementById("status").innerText = data.status || "Working...";

                if (p >= 100) {
                    clearInterval(interval);
                    document.getElementById("status").innerText = "Completed";
                    if (data.filename) {
                        showResultLinks(data.filename);
                    } else {
                        document.getElementById("result").innerText = "Report finished (no file returned).";
                    }
                } else if (p < 0) {
                    clearInterval(interval);
                    document.getElementById("status").innerText = data.status || "Error";
                    document.getElementById("result").innerText = "Error during generation.";
                }
            })
            .catch(err => {
                console.error("Poll error:", err);
                clearInterval(interval);
                document.getElementById("status").innerText = "Error checking progress";
            });
    }, 1000);
}

function setProgress(percent) {
    const fill = document.getElementById("progress-bar");
    fill.style.width = Math.max(0, Math.min(100, percent)) + "%";
}

function showResultLinks(filename) {
    const html = `
        <div>
          <p>✔ Report ready:</p>
          <a href="/api/download/${encodeURIComponent(filename)}" target="_blank">Download Report</a>
        </div>
    `;
    document.getElementById("result").innerHTML = html;
}
