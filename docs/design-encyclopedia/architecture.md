# Design Genome architecture

## Contract

`SiteDNA` is a frozen, JSON-serializable contract. It records archetype, art direction, page silhouette, semantic color and type systems, grid, spacing, geometry, photo direction, component blueprints, motion, spatial fallback, mobile personality and section order. `design_signature` spans visual styling; `composition_signature` spans component family/variant/fingerprint, order, layout/edge/media/type rhythms and structural systems. The seed is retained for reproducibility but excluded from both signatures.

## Compatibility before randomness

Selection uses hard constraints first: required business data, required artisan media, allowed provenance and component conflicts. Soft scoring then considers trade affinity, archetype, art direction, density and conversion intent. Seeded variation only breaks ties inside the compatible set. If no eligible candidate remains, generation fails explicitly.

## Narrative and rhythm

Thirty silhouettes describe narrative order rather than interchangeable stacks. The rhythm evaluator inspects visual weight, energy, layout pattern, edge behavior, media intensity and type-scale role. It penalizes repeated structural runs and rewards measured transitions. Sections absent for lack of evidence are removed before the final order is serialized.

## Anti-clone model

Similarity is structure-first: blueprint distance, family relation and layout/edge/media/type rhythm carry most of the weight; component IDs and color carry little. A palette-only change therefore cannot disguise a structural clone, while two IDs with the same blueprint remain near-identical. Bands are: 0-.40 clearly distinct, .40-.60 related, .60-.75 visually similar, .75-.84 near clone and above .84 rejected. These engineering thresholds were calibrated through cohorts and remain subject to human rendered review.

## Blueprint differentiation

Every component declares a shared family and an explicit `StructuralVariantSpec` with design intent, desktop flow/anchor/frame, mobile collapse/priority and focus progression. Registry position, component-name inference, hashing and seeds never select a structure. `blueprint_fingerprint()` hashes only the merged renderer-visible structure; `design_intent`, identity labels and notes remain documentation metadata.

## Quality model

The score covers coherence, hierarchy, readability, contrast, rhythm, conversion clarity, content fit, media fit, business fit, mobile compatibility, originality and over/under-design risk. It is a preflight engineering score. Human desktop/mobile review remains mandatory before any production renderer integration.

## Isolation

No production module imports `generator.design_genome`. The package has no renderer, no route, no database migration, no provider call and no publishing action. A future integration should consume `SiteDNA` behind an explicit feature boundary and preserve the candidate/preview/adopt/publish workflow.
