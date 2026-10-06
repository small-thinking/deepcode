# Generated overview image

Built-in image generation was used for `column-sharding-overview.png`. This is a conceptual illustration, not measured performance or an actual distributed run. The first output was corrected because its B₀ arrow reached the wrong device. The final image was inspected for dimensions, column ordering, full A replication, and shard routing.

## Generation prompt

Use case: scientific-educational
Asset type: English textbook overview image for an interactive distributed matrix multiplication lesson.
Primary request: Explain COLUMN-sharded matrix multiplication, accurately. Minimal clean scientific diagram on warm white, clear dark labels, generous whitespace, flat matrix grids and arrows, blue for A, teal for shard 0, amber for shard 1. Portrait 3:4 layout.
Top: A is a blue 2-row by 3-column matrix grid, labeled "A · 2 × 3". B is a 3-row by 4-column grid labeled "B · 3 × 4"; its left TWO columns are teal labeled B₀ and right TWO columns amber labeled B₁. A vertical boundary splits B into 3 × 2 shards.
Middle: two side-by-side devices. Each device receives a full copy of the same A, never half of A. Device 0 computes "Y₀ = A @ B₀" and Device 1 computes "Y₁ = A @ B₁". Show 2 × 2 output grids colored teal and amber, respectively. Broadcast arrows lead from A to both devices and the correct B shard leads to its device.
Bottom: arrows from both outputs to a single 2 × 4 matrix, left two columns teal right two amber, labeled "Y = concatenate([Y₀, Y₁], axis=1)". Caption "Keep the original column order".
Exact title: "Split columns. Compute locally. Concatenate."
Constraints: all text in English; correct grid dimensions; no sum operator anywhere in forward pass; no performance claim, no fake numeric values, no decorative objects, no watermark. This is a conceptual teaching illustration, not a benchmark.

## Correction prompt

Route the teal B₀ arrow from the left half of logical B to Device 0. Keep B₁ routed to Device 1 and the full A broadcast to both devices. Preserve all dimensions, labels, colors, and matrix values.

