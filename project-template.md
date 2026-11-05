# Project case-study template

Copy this file into a private/local draft first. Replace every bracketed field with verified information or remove the section. A project remains unpublished until it has evidence worth sharing.

## Record metadata

- **Title:** [Project name]
- **Slug:** [lowercase-hyphenated-name]
- **Category:** [embedded systems / power electronics / PCB / IoT / control / simulation / academic]
- **Status:** [Concept / In simulation / Design completed / Prototype in progress / Bench tested / Completed]
- **Date:** [YYYY-MM]
- **Summary:** [One or two factual sentences]

## Project overview

[What system is this? What problem or question does it address? Do not imply a working device if it is still a concept.]

## Engineering objective

- [Requirement or research question]
- [Constraint, range, or target and where it came from]

## System architecture

[Describe signal and power flow. Include a diagram only when it represents the actual documented design. Label a conceptual diagram as conceptual.]

## Hardware

[List confirmed parts and revisions, or state that selection is pending.]

## Firmware and software

[Repository, language, toolchain, architecture, interfaces, tests—or say not applicable / not yet available.]

## Design decisions and methodology

[Trade-offs, alternatives, calculations, datasheets, design rules, and assumptions.]

## Schematics and PCB

[Link actual project files or images. Do not use a render as proof of fabricated hardware.]

## Simulation

[Model, tool/version, input conditions, assumptions, outputs, limitations. Clearly label simulated results.]

## Testing and validation

- **Setup:** [fixture, instruments, calibration context]
- **Conditions:** [input, load, temperature, duration]
- **Method:** [steps and acceptance criteria]
- **Data:** [raw data or traceable results]

## Results

Separate measured, simulated, calculated, and expected values. Include units and test conditions. Do not report target values as achieved results.

## Challenges, limitations, and lessons

[What did not work? What remains uncertain? What changed?]

## Future improvements

[Clearly label plans as plans.]

## Resources

- **Source repository:** [verified public URL or omit]
- **Technical report:** [verified URL or omit]
- **Demonstration:** [actual video URL or omit]
- **Images:** [actual project images, with useful alt text]

---

## Structured project data fields

When ready to publish a project, add one object to `projects.json` using these keys as needed:

```json
{
  "slug": "short-project-name",
  "title": "Project title",
  "status": "concept",
  "category": "Power Electronics",
  "date": "2026-11",
  "summary": "Short, evidence-based description.",
  "objective": "Engineering objective or research question.",
  "problem": "Context and constraints.",
  "approach": "Verified design approach, not a future intention.",
  "hardware": [],
  "software": [],
  "simulation": "",
  "measured_results": "",
  "lessons": "",
  "github_url": "",
  "documentation_url": "",
  "case_study_url": "",
  "media": []
}
```

Use an empty array/string when no evidence exists. Do not populate estimated parts, results, repositories, photos, or measurements. Keep an unfinished project as a local draft if even the concept is not ready for public review.
