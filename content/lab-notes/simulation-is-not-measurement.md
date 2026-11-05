---
slug: simulation-is-not-measurement
title: Simulation is a model, not a measurement
date: 2026-11-05
tags: [simulation, validation, power electronics]
description: How to report simulation output without confusing model results with bench-tested behaviour.
---

## What a simulation can establish

A simulator evaluates a mathematical model under chosen inputs and assumptions. It can help compare topologies, estimate expected behaviour, expose sensitivity to component values, and catch some design mistakes before hardware exists.

The result is conditional. It depends on what the model includes: component parasitics, control behaviour, switching transitions, thermal effects, layout coupling, tolerances, and the boundary conditions. A model that omits a mechanism cannot report its effect.

## Keep the evidence labels separate

| Evidence type | What it represents | What to report |
| --- | --- | --- |
| Analytical estimate | A calculation using stated equations and assumptions | Formula, units, assumptions, and limits |
| Simulation | Output of a specified model | Tool/model, inputs, component models, solver settings, and scope |
| Bench measurement | Observation from physical hardware | Setup, instruments, calibration context, load, environment, and uncertainty |

A simulated efficiency is not a measured efficiency. A waveform plot is not a test report unless its source and conditions are clear. This distinction matters particularly when parasitics, switching behaviour, thermal rise, layout, or control-loop dynamics affect the result.

## A careful comparison

When a prototype exists, compare simulation and measurement at matched operating points. Record the differences rather than forcing the hardware to match the model. The gap is evidence about the model, the implementation, or the test setup—and often points to the next useful investigation.

> Educational explanation only. No particular converter, simulation file, or measured result is represented by this note.
