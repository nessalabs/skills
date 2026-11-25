# Performance checklist

This file holds the verification and safety rules behind
[`coding` §5](../SKILL.md#5-performance). Start with profiling and the core loop
there before applying these checks.

## Evidence and benchmarks

- **Match the evidence to the claim.** A quantified speedup claim must state the
  scenario, baseline, result, and machine. A mechanism-only claim ("removes one
  serialisation per request") names the cost that disappeared and states that
  end-to-end impact was not measured. Proxy counts (generated code size,
  allocations, instructions) measure only themselves—report them as counts, and
  do not claim "faster" until you time the actual operation. Check that the
  benchmark actually runs the code you changed.
- **Test strategy switches.** When code picks between strategies, prove two
  things: that it picks the right one reliably (run it many times, including on
  inputs near the threshold where the choice flips), and that the chosen
  strategy is fast. One fast run can hide a choice that flips unpredictably.
- **Benchmark the workload it should lose on**, and report both sides: low and
  high concurrency, short and long tasks, full and partial batches, first run
  and later runs. If you changed execution order, report peak memory alongside
  time to first result. For code-size or compile-time work, report counter-metrics
  too (build time, and runtime if dispatch changed). Report mixed results as
  mixed, never as "faster". For incremental work, vary unchanged input, one
  changed item, and full invalidation, and vary live registry size separately
  from actual removals.

## Preserving the contract

- **Keep the observable contract unchanged.** For a pure performance change or a
  cheaper version of an existing operation, prove the behaviour did not change.
  For a deterministic batch API, verify identical output on the full fixture set
  and on pathological inputs. For APIs that promise streaming, progress,
  cancellation, or scheduling, *when* results become visible, what ordering is
  allowed, and what resources stay bounded are all part of the contract. So are
  steps that keep the peer moving, such as flushing before waiting for more
  input: identical final bytes arriving only at end of stream is a regression,
  and a faster copy that skips a flush can hang the other side forever.
- **Skip work only when no obligation remains.** You can skip a durable write if
  the same complete state is already durable. Keep distinct terminal writes and
  anything still owed to an output, future iteration, error, close, cancel,
  release, or waiter, along with the structural bookkeeping the protocol needs.
  Test a skip by placing malformed data where the skipped work would have run
  and asserting nothing surfaces.

## Scheduling, caching, and upkeep

- **Keep construction lazy when the consumer schedules.** If the consumer owns
  batching, admission, or priority, do not start work before handing it over. An
  operation that is already running when passed in makes the consumer's window
  pointless.
- **Prepare once only while the result stays valid.** Include the selected
  fields and operation direction in your validity argument; cheap recomputation
  is often safer than a cached flag. Cache failures only for their valid
  lifetime so a temporary failure never becomes permanent by accident.
- **Revert an optimisation you cannot maintain.** Regardless of the benchmark
  numbers, code that nobody can modify safely is a liability.
- **Document what every tuned number was measured for.** Next to a magic number
  like "keep entries for 3 frames", note what it was measured against and what
  it protects. When the underlying code changes, measure again or remove the
  number.

Language-specific guidance: [Rust](rust.md#performance-in-rust),
[React & TypeScript](react-typescript.md#performance-in-react).
