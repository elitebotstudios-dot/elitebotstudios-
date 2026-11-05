# Add an engineering project

The public project cards are rendered from `projects.json`. Use `/project-template.md` as the case-study checklist and keep a draft private until its status and evidence are ready to publish.

## Workflow

1. Copy the structured JSON example from `project-template.md` into `projects.json`.
2. Use a truthful status: `concept`, `simulation`, `design-completed`, `prototype-in-progress`, `bench-tested`, or `complete`.
3. Fill only facts supported by actual files or records. Concepts can state an objective, but must not invent hardware, architecture, firmware, or results.
4. For measurements, provide conditions, method, instruments, units, and limitations. Keep simulated, calculated, expected, and measured values distinct.
5. Add public links only after checking that they work and that publication is authorized.
6. Run the checks below before committing.

## Data fields

Card fields: `slug`, `title`, `status`, `category`, `date`, `summary`, `objective`, `problem`, `approach`, and `results_note`. Add a nested `case_study` object to generate a dedicated `/projects/<slug>.html` page; the generator displays only populated sections such as `architecture`, `hardware`, `software`, `schematics`, `simulation`, `testing`, `results`, `limitations`, `lessons`, `open_questions`, `future_directions`, and `resources`. Optional top-level links include `github_url`, `documentation_url`, and `media`. Arrays may stay empty and text fields may stay blank; absent evidence is not a reason to fabricate content.

## Local checks

```sh
python3 -m json.tool projects.json >/dev/null
node --check assets/site.js
node tests/projects.test.js
python3 -m http.server 8080
```

Open `/projects.html` locally. If the JSON request fails, the page preserves its honest empty-state message. Do not mark a project complete because a CAD render or simulation exists; use the status that matches the strongest evidence actually available.
