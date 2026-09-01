# Design Genome simulation report

All cohorts use the public generation pipeline with linting, heuristic quality scoring, bounded history and anti-clone rejection. This is combinatorial evidence, not rendered aesthetic approval.

## Main cohort
- Requested: 10,000
- Generated / failed / unique: 10,000 / 0 / 10,000
- Similarity / linter / quality / structural duplicate rejections: 305 / 187 / 0 / 0
- Unique design / composition signatures: 10,000 / 9,996
- Mean / maximum attempts: 1.0492 / 5
- Sampled mean / maximum pair similarity: 0.3175 / 0.7849
- Collision pairs: 0; effective-space estimate: 49,995,000 (`lower_bound_under_zero_observed_collisions`)

## 100 plumbers with shared history
- Generated / failed / unique: 100 / 0 / 100
- Unique composition signatures / hero fingerprints / layout rhythms: 100 / 26 / 86
- Maximum pair similarity: 0.8399
- Distinct silhouettes / heroes / palettes / typography: 7 / 26 / 12 / 4

## 50 identical-input plumbers
Only the artisan seed changes. Generated / failed / unique: 50 / 0 / 50. Unique composition signatures: 50.
Distinct silhouettes / heroes / palettes / section compositions: 2 / 19 / 4 / 2. Maximum pair similarity: 0.8303.

## Color/type ablation
With color and typography removed from comparison, the 100-plumber cohort retains 100 composition signatures and 86 layout rhythms. Maximum pair similarity is 0.8814.

## Interpretation boundary
The Design Genome is a knowledge contract. Human desktop/mobile rendering review remains mandatory before any production integration.
