# Design Genome architecture

## Contract

`SiteDNA` is a frozen, JSON-serializable contract. It records archetype, art direction, page silhouette, semantic color and type systems, grid, spacing, geometry, photo direction, component blueprints, motion, spatial fallback, mobile personality, section order and a stable signature. The seed is retained for reproducibility but excluded from the signature.

## Compatibility before randomness

Selection uses hard constraints first: required business data, required artisan media, allowed provenance and component conflicts. Soft scoring then considers trade affinity, archetype, art direction, density and conversion intent. Seeded variation only breaks ties inside the compatible set. If no eligible candidate remains, generation fails explicitly.

## Narrative and rhythm

Thirty silhouettes describe narrative order rather than interchangeable stacks. The rhythm evaluator inspects visual weight and energy, rejects runs of three heavy sections, warns about flat pages, and rewards measured transitions. Sections absent for lack of evidence are removed before the final order is serialized.

## Anti-clone model

Similarity is computed across six explainable distances: structure, typography, color, components, narrative and photo strategy. Candidate generation compares against history and rejects high similarity. The default threshold is intentionally stricter than exact signature uniqueness.

## Quality model

The score covers coherence, hierarchy, readability, contrast, rhythm, conversion clarity, content fit, media fit, business fit, mobile compatibility, originality and over/under-design risk. It is a preflight engineering score. Human desktop/mobile review remains mandatory before any production renderer integration.

## Isolation

No production module imports `generator.design_genome`. The package has no renderer, no route, no database migration, no provider call and no publishing action. A future integration should consume `SiteDNA` behind an explicit feature boundary and preserve the candidate/preview/adopt/publish workflow.
