
from flask import Flask, render_template_string, request
import subprocess
import os
import json

# Load .env from the same folder as this script
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

app = Flask(__name__)

# -------------------------------
# Read all config from .env ONLY
# -------------------------------
def _as_bool(val: str, default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "t", "yes", "y", "on")

# Required settings (no defaults here to keep config out of code)
_scripts_json = os.environ.get("SCRIPTS_JSON")
_groups_raw   = os.environ.get("GROUPS")
_default_tab  = os.environ.get("ACTIVE_TAB")

if not _scripts_json:
    raise RuntimeError("Missing SCRIPTS_JSON in .env")
if not _groups_raw:
    raise RuntimeError("Missing GROUPS in .env")
if not _default_tab:
    raise RuntimeError("Missing ACTIVE_TAB in .env")

try:
    SCRIPTS = json.loads(_scripts_json)
    if not isinstance(SCRIPTS, list):
        raise ValueError("SCRIPTS_JSON must be a JSON array of objects.")
except Exception as e:
    raise RuntimeError(f"Failed to parse SCRIPTS_JSON: {e}")

GROUPS = [g.strip() for g in _groups_raw.split(",") if g.strip()]
DEFAULT_TAB = _default_tab
DEBUG_MODE = _as_bool(os.environ.get("DEBUG"), default=False)

# -------------------------------
# HTML template (unchanged logic)
# -------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>command_console</title>
    <style>
        body {
            background-color: #0a0a0a;
            color: #c0c0c0;
            font-family: 'Consolas', 'Courier New', monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            width: 600px;
            background-color: #111;
            border: 1px solid #222;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.4);
            padding: 30px 40px;
        }
        .title {
            text-align: left;
            font-size: 1.2rem;
            color: #888;
            text-transform: lowercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #222;
            padding-bottom: 10px;
            margin-bottom: 15px;
            opacity: 0.9;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 8px 14px;
            border: 1px solid #333;
            border-radius: 6px;
            color: #ddd;
            text-decoration: none;
            background-color: #121212;
            box-shadow: inset 0 0 6px rgba(255,255,255,0.05);
            transition: all 0.2s ease-in-out;
            font-weight: 700; /* bold for visibility */
        }
        .tab:hover {
            background-color: #1c1c1c;
            color: #fff;
            border-color: #666;
            box-shadow: 0 0 8px rgba(255,255,255,0.08);
        }
        .tab.active {
            background-color: #1a1a1a;
            color: #fff;
            border-color: #777;
            box-shadow: 0 0 0 1px #2a2a2a inset;
        }
        .scripts {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: flex-start;
        }
        form { margin: 0; }
        button {
            background-color: #0f0f0f;
            color: #aaa;
            border: 1px solid #444;
            padding: 12px 20px;
            font-size: 14px;
            cursor: pointer;
            border-radius: 6px;
            font-family: 'Consolas', monospace;
            transition: all 0.2s ease-in-out;
            box-shadow: inset 0 0 6px rgba(255,255,255,0.05);
        }
        button:hover {
            background-color: #222;
            color: #ddd;
            border-color: #666;
            box-shadow: 0 0 8px rgba(255,255,255,0.1);
        }
        .message {
            margin-top: 25px;
            font-size: 14px;
            color: #bbb;
            text-align: left;
            background-color: #0d0d0d;
            border: 1px solid #222;
            border-radius: 6px;
            padding: 10px;
            white-space: pre-wrap;
            box-shadow: inset 0 0 8px rgba(255,255,255,0.05);
        }
        .message::before {
            content: "› ";
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="title">command_console</div>

        <div class="tabs">
            {% for g in groups %}
                <a href="/?tab={{ g }}" class="tab {{ 'active' if g == active_tab else '' }}">{{ g.replace('_',' ') }}</a>
            {% endfor %}
        </div>

        <div class="scripts">
            {% for script in scripts if script.group == active_tab %}
                <form action="/run" method="post">
                    <input type="hidden" name="path" value="{{ script.path }}">
                    <input type="hidden" name="type" value="{{ script.type }}">
                    <input type="hidden" name="tab" value="{{ active_tab }}">
                    <button type="submit">{{ script.label }}</button>
                </form>
            {% endfor %}
        </div>

        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    active_tab = request.args.get("tab", DEFAULT_TAB)
    return render_template_string(
        HTML_TEMPLATE,
        scripts=SCRIPTS,
        message=None,
        active_tab=active_tab,
        groups=GROUPS
    )

@app.route("/run", methods=["POST"])
def run_script():
    path = request.form['path']
    script_type = request.form['type']
    active_tab = request.form.get('tab', DEFAULT_TAB)
    print(f"[INFO] Button clicked: {path} ({script_type})")

    message = ""
    try:
        if script_type == "python":
            result = subprocess.run(["python", path], capture_output=True, text=True)
        elif script_type == "powershell":
            result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", path], capture_output=True, text=True)
        else:
            raise ValueError(f"Unknown script type: {script_type}")

        message = f"{path} executed successfully.\n\n{result.stdout.strip() or 'No output'}"
    except Exception as e:
        message = f"Error running {path}: {str(e)}"

    return render_template_string(
        HTML_TEMPLATE,
        scripts=SCRIPTS,
        message=message,
        active_tab=active_tab,
        groups=GROUPS
    )

if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)
