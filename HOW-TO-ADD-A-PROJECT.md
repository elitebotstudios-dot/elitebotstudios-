# How to add a project

The Projects page is driven by a single file: **`projects.json`**.

Edit that one file, commit, and the grid rebuilds itself. You never touch
`projects.html` to add a build — the page reads the JSON in the browser and
renders the cards.

---

## 1. Add an entry

Open `projects.json`. It is an array, so each build is one `{ ... }` object
separated by a comma:

```json
[
  {
    "slug": "esp32-energy-monitor",
    "title": "ESP32-Based Energy Monitor",
    "status": "in-progress",
    "tags": ["esp32", "power", "energy-monitoring"],
    "problem": "Why the build was needed. One or two sentences.",
    "approach": "How you solved it. What the architecture is.",
    "bom": [
      { "part": "ESP32-WROOM-32E", "detail": "MCU + Wi-Fi" },
      { "part": "SCT-013-030", "detail": "30 A split-core CT" }
    ],
    "firmware_repo": "https://github.com/elitebotstudios-dot/your-repo",
    "media": [],
    "results": "Measured numbers. State the conditions.",
    "date": "2026-10"
  }
]
```

### Field reference

| Field | Required | What it does |
|---|---|---|
| `slug` | yes | URL-safe id, lowercase with hyphens. Also becomes `/projects.html#slug`. |
| `title` | yes | Card heading. |
| `status` | yes | `"in-progress"` shows an amber chip, `"complete"` a teal chip. |
| `tags` | no | Array of short labels shown as chips. Keep to 3–5. |
| `problem` | yes | The situation that needed fixing. |
| `approach` | yes | How you attacked it. |
| `bom` | no | Array of `{ "part": "...", "detail": "..." }`, or plain strings. |
| `firmware_repo` | no | GitHub URL. Renders a **Source** button. Leave `""` to hide it. |
| `media` | no | Array of image/video paths. Reserved — not rendered yet. |
| `results` | yes* | Measured outcome. *If not measured yet, use `results_note` instead and leave `results` empty.* |
| `results_note` | no | Shown when `results` is empty. Use it to say plainly that testing is pending. |
| `owner_todo` | no | Renders an amber TODO chip, e.g. `"Repo + test video pending"`. |
| `date` | yes | `YYYY-MM`. Displayed in the card meta row. |

---

## 2. House rules — these are not optional

The whole credibility of this site rests on one claim: **that everything
published here was actually built and actually measured.**

So, when adding a project:

1. **Never invent a result.** If you have not measured it on the bench, leave
   `results` empty and use `results_note` to say what is still pending.
2. **State the conditions with every number.** An efficiency figure without
   input voltage, load, and temperature is not a result, it is a boast.
   Write `"87.1% at 12.0 V in, 3 A load, 24 °C ambient, measured on a
   calibrated electronic load"` — not `"high efficiency"`.
3. **Simulated ≠ measured.** If a figure came out of a simulator, label it
   as simulated in the text.
4. **No client work without permission.** If a build was for a client, get
   written permission before naming them or publishing their schematic.
5. **No stock renderings.** Use photographs of the actual board.

If you cannot fill a section honestly, leave the field out. An empty field
renders nothing. A guessed field renders a lie.

---

## 3. Test it before you commit

1. Run the site locally:
   ```bash
   python3 -m http.server 8080
   ```
2. Open `http://localhost:8080/projects.html`.
3. Check that the card appears, the status chip is the right colour, and the
   BOM list renders.
4. Run the JSON through a validator, or just paste it into
   <https://jsonlint.com> — a trailing comma is the usual mistake and it will
   silently stop the grid from rendering.

If the JSON is broken, the page deliberately keeps its "no builds yet" state
rather than showing a blank grid.

---

## 4. When a build finishes

Change `"status"` to `"complete"` and move your measured numbers from
`results_note` into `results`. That edit is the whole ceremony — the chip
turns teal and the card is done.
