#!/usr/bin/env python3
"""Injects history.json into dashboard_template.html -> dashboard.html.

Run this after updating history.json, then publish dashboard.html as the
artifact (same URL each time). Keeps the repo as the single source of truth;
the published page just carries an embedded snapshot of the data.
"""
import json

with open("history.json", "r", encoding="utf-8") as f:
    history = f.read().strip()

# Validate it parses, so we never publish a broken page.
json.loads(history)

with open("pipeline_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
trigger_id = config["trigger_id"]

with open("dashboard_template.html", "r", encoding="utf-8") as f:
    template = f.read()

html = template.replace("__HISTORY_JSON__", history).replace("__TRIGGER_ID__", trigger_id)

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Built dashboard.html")
