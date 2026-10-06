# Genomic Chaos

![Genomic Chaos simulation cover](cover.png)

Genomic Chaos is a small evolutionary robotics project. It uses a genetic algorithm to generate articulated creatures, simulates them in PyBullet, and selects for creatures that move closer to the top of a mountain-shaped arena.

I originally built this as a hands-on AI/simulation project. The code is intentionally direct and experimental rather than framework-heavy: the interesting parts are the genome encoding, fitness function, multiprocessing evaluator, and the way simulation state is kept isolated between workers.

## What It Shows

- Genetic algorithm implementation: selection, crossover, mutation, elitism, and genome growth/shrinkage.
- Procedural robot generation: genomes are decoded into URDF links, joints, and motor controls.
- Physics simulation: PyBullet evaluates each creature against the same mountain-climbing task.
- Parallel computation: populations can be evaluated across multiple worker processes.
- Shared state and synchronization: parallel workers update a shared completed-job counter behind a lock, avoiding races while keeping each physics simulation isolated.
- Experiment artifacts: selected evolved creatures are kept in `hall_of_fame/` as reproducible genomes.

## Project Layout

- `genome.py`: genome schema, mutation, crossover, CSV import/export, and URDF link generation.
- `creature.py`: creature state, motor model, URDF export, and fitness calculation.
- `population.py`: population creation, fitness normalization, and parent selection.
- `simulation.py`: PyBullet simulation and multiprocessing evaluation.
- `train.py`: training loop for running evolutionary experiments.
- `run_experiment.py`: small wrapper around `train.py` for direct script-style runs.
- `realtime_from_csv.py`: visual playback of a saved genome.
- `offline_from_csv.py`: headless playback/evaluation of a saved genome.
- `prepare_shapes.py`: mesh generation for mountain terrain.
- `shapes/`: URDF/OBJ terrain assets.
- `hall_of_fame/`: saved genomes from interesting evolved creatures.

## Setup

```bash
uv sync --dev
```

## Run Tests

```bash
uv run pytest
```

Some tests use PyBullet in `DIRECT` mode, so they do not require a GUI.

## Run An Evolution Experiment

```bash
uv run genomic-chaos-train
```

This evaluates a population over multiple generations and writes elite genomes as CSV files. For a quick smoke test during development, pass smaller values at the command line:

```bash
uv run genomic-chaos-train --generations 2 --pop-size 8 --pool-size 2 --iterations 120
```

## Replay A Saved Creature

```bash
uv run genomic-chaos-replay hall_of_fame/rolling_dude.csv
```

For a headless run:

```bash
uv run genomic-chaos-offline hall_of_fame/rolling_dude.csv
```

## Notes On Parallelism

The parallel evaluator creates one PyBullet simulation per worker process. This avoids sharing mutable physics-engine state between processes. The only shared value is a completed-job counter, which is updated under a multiprocessing lock. That makes the synchronization point explicit while keeping the expensive simulation work independent.

This was deliberately kept simple: it is easier to reason about failure modes, avoids hidden global state, and makes race conditions visible in the code.

## Current Limitations

- The simulation is stochastic unless seeds are set externally.
- PyBullet behavior can vary by platform/version.
- The genetic encoding is intentionally compact and experimental; it favors exploration over physical realism.
