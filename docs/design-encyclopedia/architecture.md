# Design Genome architecture

## Contract

`SiteDNA` is a frozen, JSON-serializable contract. It records archetype, art direction, page silhouette, semantic color and type systems, grid, spacing, geometry, photo direction, component blueprints, motion, spatial fallback, mobile personality, section order and a stable signature. The seed is retained for reproducibility but excluded from the signature.

## Compatibility before randomness

Selection uses hard constraints first: required business data, required artisan media, allowed provenance and component conflicts. Soft scoring then considers trade affinity, archetype, art direction, density and conversion intent. Seeded variation only breaks ties inside the compatible set. If no eligible candidate remains, generation fails explicitly.

## Narrative and rhythm

Thirty silhouettes describe narrative order rather than interchangeable stacks. The rhythm evaluator inspects visual weight and energy, rejects runs of three heavy sections, warns about flat pages, and rewards measured transitions. Sections absent for lack of evidence are removed before the final order is serialized.

## Anti-clone model

Similarity uses structure (18%), typography (15%), color (5%), components (38%), narrative (16%) and photo strategy (8%). A palette-only change therefore cannot disguise a structural clone. Bands are: 0-.40 clearly distinct, .40-.60 related, .60-.75 visually similar, .75-.84 near clone and above .84 rejected. These engineering thresholds were calibrated through cohorts and remain subject to human rendered review.

## Quality model

The score covers coherence, hierarchy, readability, contrast, rhythm, conversion clarity, content fit, media fit, business fit, mobile compatibility, originality and over/under-design risk. It is a preflight engineering score. Human desktop/mobile review remains mandatory before any production renderer integration.

## Isolation

No production module imports `generator.design_genome`. The package has no renderer, no route, no database migration, no provider call and no publishing action. A future integration should consume `SiteDNA` behind an explicit feature boundary and preserve the candidate/preview/adopt/publish workflow.
