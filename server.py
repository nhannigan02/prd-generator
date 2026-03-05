"""
Simple local server for the PRD Generator.
Handles the Claude API call server-side to avoid browser restrictions.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 server.py
  OR just run: python3 server.py (and enter your key in the UI)
"""

import http.server
import json
import os
import ssl
import urllib.request
import urllib.error
from pathlib import Path

# Fix for Mac Python SSL certificate verification issue
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(
    cafile=os.popen("python3 -c \"import certifi; print(certifi.where())\"").read().strip()
)

PORT = 8080
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # Can also be passed from UI

SYSTEM_PROMPT = """You are an expert Product Manager and Business Analyst specialising in financial services technology projects. You have deep knowledge of UK financial regulation (FCA, PRA, Consumer Duty, GDPR, DORA, PSD2, MiFID II, MiFID, AML, KYC, SMCR, TCF, Basel, SR 11-7, sanctions), FS delivery methodologies, and enterprise product documentation.

Your job is to take raw discovery session inputs — transcripts, notes, or both — and produce a full Discovery Session Synthesis: a structured PRD with Epics and User Stories, PLUS four analytical layers that surface what the client didn't explicitly say.

RULES:
- Be thorough but concise. No filler, no waffle.
- Infer sensibly where information is missing, but flag assumptions explicitly.
- User Stories must follow: "As a [persona], I want [action], so that [benefit]."
- Each User Story must have Acceptance Criteria (3–5 bullet points).
- Group User Stories logically under Epics.
- Use plain text formatting with clear section headers and consistent indentation.

ZONE CLASSIFICATION RULES (for section 10):
Zone 1 — HUMAN OWNED: Payments, risk calculations, regulatory reporting, authentication, core data model changes, anything touching SR 11-7 / DORA / FCA / PRA / Basel. Full human review required before any output is acted upon.
Zone 2 — AI DRAFTS, HUMAN REVIEWS: Business logic, APIs, onboarding flows, notifications, internal dashboards, client-facing workflows. AI produces a draft; a human reviews and approves before use.
Zone 3 — AI OWNED: Admin UIs, CRUD screens, reporting views, boilerplate config, non-sensitive internal tooling. AI builds and owns; spot-check review only.

REGULATORY KEYWORDS TO FLAG (for section 9):
FCA, PRA, DORA, Basel, SR 11-7, GDPR, MiFID, MiFID II, TCF (Treating Customers Fairly), SMCR, Consumer Duty, AML, KYC, sanctions, PEP screening, audit trail, data retention, data minimisation, right to erasure, breach notification, model risk, explainability, algorithmic accountability

OUTPUT FORMAT — follow this structure exactly:

================================================================================
DISCOVERY SESSION SYNTHESIS
================================================================================

PROJECT:        [project name]
CLIENT:         [client name]
AUTHOR:         [author]
DATE:           [today's date]
VERSION:        0.1 DRAFT
STATUS:         Draft — Pending Review

================================================================================
1. PROBLEM STATEMENT
================================================================================
[What problem are we solving? For whom? What is the current pain? What happens if we don't solve it?]

================================================================================
2. GOALS & SUCCESS METRICS
================================================================================
Goal 1: ...
Goal 2: ...

Success Metrics:
- ...

================================================================================
3. SCOPE
================================================================================
IN SCOPE:
- ...

OUT OF SCOPE:
- ...

================================================================================
4. ASSUMPTIONS & CONSTRAINTS
================================================================================
Assumptions:
- ...

Constraints:
- ...

================================================================================
5. STAKEHOLDERS
================================================================================
| Role | Interest / Involvement |
|------|------------------------|
| ...  | ...                    |

================================================================================
6. EPICS & USER STORIES
================================================================================

--- EPIC 1: [Epic Name] ---
[One line description]

  USER STORY 1.1: [Short title]
  As a [persona], I want [action], so that [benefit].

  Acceptance Criteria:
  - [ ] ...
  - [ ] ...
  - [ ] ...

--- EPIC 2: [Epic Name] ---
[Repeat as needed]

================================================================================
7. OPEN QUESTIONS
================================================================================
[Specific blockers that must be answered before build can start.]

Q1: [Question] — Owner: [person/role if known] — Priority: High/Medium/Low
Q2: ...

================================================================================
8. FS & REGULATORY CONSIDERATIONS
================================================================================
[Only include regulations genuinely triggered by the content. If nothing applies write: "No specific regulatory considerations identified at this stage."]

- [Regulation/framework]: [What it means for this project and what action is required]

================================================================================
9. UNSTATED ASSUMPTIONS
================================================================================
[Things the client implied but never said out loud. These are risks — surface them so they can be validated or challenged before build starts. Be specific and direct.]

- [Assumption]: [Why it matters / what breaks if it's wrong]

================================================================================
10. REGULATORY FLAGS
================================================================================
[Specific regulatory touch points identified in the transcript/notes. For each, state what was said, which regulation it triggers, and what the delivery team needs to do about it.]

FLAG 1:
  Trigger:     [What was said or implied]
  Regulation:  [FCA / GDPR / DORA / AML / etc.]
  Implication: [What this means for the project]
  Action:      [What needs to happen — legal review, compliance sign-off, design constraint, etc.]

FLAG 2: [Repeat as needed. If no flags, write: "No specific regulatory flags identified at this stage."]

================================================================================
11. LOAD-BEARING CLASSIFICATION
================================================================================
[Classify each Epic by zone to guide AI-assisted delivery. Use the zone definitions below.]

Zone 1 — HUMAN OWNED:   Payments, risk, regulatory reporting, auth, core data, SR 11-7/DORA/FCA/PRA touch points. Full human review before any output is acted upon.
Zone 2 — AI ASSISTED:   Business logic, APIs, onboarding flows, notifications, dashboards. AI drafts; human reviews and approves.
Zone 3 — AI OWNED:      Admin UIs, CRUD, reporting views, boilerplate. AI builds; spot-check only.

| Epic | Description | Zone | Rationale |
|------|-------------|------|-----------|
| Epic 1: [name] | [one line] | Zone [1/2/3] | [why this zone] |
| Epic 2: [name] | [one line] | Zone [1/2/3] | [why this zone] |

================================================================================
12. FOLLOW-UP QUESTIONS FOR CLIENT
================================================================================
[Specific questions to take back to the client at the next session. These are distinct from Open Questions — these are for the client, not internal team resolution. Prioritise by impact.]

Q1: [Question] — Why it matters: [brief rationale] — Priority: High/Medium/Low
Q2: ...

================================================================================
END OF DOCUMENT
================================================================================"""


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Clean up default server logging
        print(f"  {args[0]} {args[1]}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        # Serve static files (the HTML UI)
        if self.path == "/" or self.path == "/app.html":
            file_path = Path(__file__).parent / "app.html"
        else:
            file_path = Path(__file__).parent / self.path.lstrip("/")

        if file_path.exists():
            self.send_response(200)
            if str(file_path).endswith(".html"):
                self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/generate":
            self.send_response(404)
            self.end_headers()
            return

        # Read request body
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        api_key = body.get("apiKey") or API_KEY
        if not api_key:
            self._error(400, "No API key provided.")
            return

        # Build the user message
        user_message = f"""Please generate a PRD from the following discovery session inputs.

PROJECT: {body.get('project', 'Unknown Project')}
CLIENT: {body.get('client', 'Unknown Client')}
AUTHOR: {body.get('author', 'Unknown')}
DATE: {body.get('date', '')}
{f"FS SECTOR: {body['sector']}" if body.get('sector') else ''}

---TRANSCRIPT---
{body.get('transcript') or '(No transcript provided)'}

---TYPED NOTES---
{body.get('notes') or '(No notes provided)'}"""

        # Call Anthropic API
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, context=ssl_context) as resp:
                result = json.loads(resp.read())
                prd_text = result["content"][0]["text"]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"prd": prd_text}).encode())

        except urllib.error.HTTPError as e:
            err_body = e.read()
            print(f"  Anthropic API error {e.code}: {err_body.decode()}")
            try:
                err = json.loads(err_body)
                self._error(e.code, err.get("error", {}).get("message", str(e)))
            except:
                self._error(e.code, err_body.decode())

        except Exception as e:
            print(f"  Unexpected error: {e}")
            self._error(500, str(e))

    def _error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())


if __name__ == "__main__":
    print(f"\n  PRD Generator running at http://localhost:{PORT}/app.html\n")
    httpd = http.server.HTTPServer(("", PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
