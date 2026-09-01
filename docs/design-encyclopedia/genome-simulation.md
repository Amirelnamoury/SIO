# Design Genome simulation report

All cohorts use the public generation pipeline with linting, heuristic quality scoring, bounded history and anti-clone rejection. This is combinatorial evidence, not rendered aesthetic approval.

## Main cohort
- Requested: 10,000
- Generated / failed / unique: 10,000 / 0 / 10,000
- Similarity / linter / quality rejections: 32 / 182 / 0
- Mean / maximum attempts: 1.0214 / 4
- Sampled mean / maximum pair similarity: 0.2183 / 0.7768
- Collision pairs: 0; effective-space estimate: 49,995,000 (`lower_bound_under_zero_observed_collisions`)

## 100 plumbers with shared history
- Generated / failed / unique: 100 / 0 / 100
- Maximum pair similarity: 0.8378
- Distinct silhouettes / heroes / palettes / typography: 7 / 26 / 12 / 4

## 50 identical-input plumbers
Only the artisan seed changes. Generated / failed / unique: 50 / 0 / 50.
Distinct silhouettes / heroes / palettes / section compositions: 2 / 15 / 4 / 2. Maximum pair similarity: 0.8068.

## Interpretation boundary
The Design Genome is a knowledge contract. Human desktop/mobile rendering review remains mandatory before any production integration.
