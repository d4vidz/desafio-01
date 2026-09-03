# Marimo notebook communication contract

This document is the preventive communication contract for project notebooks. Narrative must be created with the implementation, not added as a later editorial cleanup. It supports issue #67 and specification #69; agent handoff is defined in #68.

## Audience and purpose

Every notebook must be readable by someone who did not follow the implementation. Internal comments may record technical details, but they do not replace an explanation in the main flow.

## Required narrative section

Every main result or visualization must visibly state:

1. **Question:** what are we trying to learn?
2. **Population and filters:** which rows, tracks, genres, or artists enter?
3. **Grain:** what does one observation represent?
4. **Method:** what calculation was made, explained independently of code?
5. **How to read:** meaning of axes, color, size, distance, order, and controls.
6. **Denominator:** sample size, top-*n*, aggregation, and membership handling.
7. **Result:** a number or pattern computed in this run from the same table as the chart.
8. **Interpretation:** what the snapshot supports.
9. **Limit:** what cannot be concluded, including selection, uncertainty, and provenance.
10. **Status:** infrastructure, prototype, complete experiment, or validated evidence.

Essential information must be available without interaction. An accordion may contain SQL, schema details, and diagnostics; a tooltip may complement it but cannot be the only explanation.

## Primitives and reactivity

Use `NarrativeSection` and the `spotify_data.notebook_ui` renderer when available. Text must receive metrics and tables from the same cell or pipeline that feeds the figure. Avoid manually copied numbers.

Widgets must declare their default, denominator effect, and render bounds. A filter producing a sparse population must show a warning. Outputs must stay below the project limit.

## Claim language

- association: variables move together in the snapshot;
- comparison: groups differ under the stated slice;
- prediction: performance on held-out data;
- causality: only with a design that supports it.

`popularity` is the observed score, not a promise of future success. Do not use “causes” or “impacts” when the method only shows association. Exploratory results must say that they generate hypotheses.

## Review checklist

- [ ] A reader without context can explain the question and grain.
- [ ] Chart and text use the same population and aggregation.
- [ ] Encoding interpretation is explicit.
- [ ] The result changes correctly when a widget changes.
- [ ] Status and claim ceiling appear in static HTML.
- [ ] Filters, samples, sparsity, and limitations are visible.
- [ ] Tests, HTML, and manifest were updated.

See [glossary.md](glossary.md) for terminology. The English version is supporting translation; Portuguese is canonical.
