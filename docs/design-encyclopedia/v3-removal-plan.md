# V3 removal plan after the visual gate

Status: deferred. V3 is still the only active production renderer.

The Genome renderer is available through the explicit `generate_site_genome_experimental` adapter. Do not remove V3 or switch `generate_site` until the Visual Lab receives human approval and the production workflows below have dedicated compatibility evidence.

## Existing V3 profile strategy

Do not translate a V3 profile field by field into SiteDNA. Build a new Genome candidate from the artisan's existing business data and selected media. Preview it in the protected Admin flow, then adopt it explicitly. Adoption must not publish. Existing published HTML remains unchanged until the separate publication action.

## Runtime migration

1. Add persisted SiteDNA/candidate storage only after documenting the schema decision. Prefer existing JSON profile storage if it can retain the full signed SiteDNA without losing history.
2. Route Admin preview generation in `backend/app/admin_service.py` through the Genome adapter behind an explicit migration gate.
3. Verify preview token isolation and `/admin/preview-api` media/form behavior.
4. Verify candidate generation, abandon, adoption, and publication separately.
5. Verify public lead creation and notification with the unchanged `/pub/{slug}/demande-devis` contract.
6. Migrate existing V3 sites by explicit candidate generation, never by silent profile conversion.
7. Switch `generator/site_generator.py::generate_site` only after the human visual gate and workflow tests pass.

## Files and imports to retire

After the gate, remove or replace:

- `generator/v3/` and `render_site_v3`
- `generator/v3/context.py::is_compatible_design_profile`
- V3 imports in `generator/site_generator.py`
- V3 grammar and selector imports in `backend/app/admin_service.py`
- V3 profile imports in `backend/app/admin_schemas.py` and `backend/app/design_schemas.py`
- V3-only media query helpers only after equivalent Genome media selection is proven; provider transport itself may remain shared
- `backend/scripts/generate_v3_visual_audit.py`
- `backend/tests/site_v3_fixtures.py`
- V3-only expectations in `test_site_generator_v3.py`, `test_site_v3_only.py`, and `test_admin_v3_only_workflow.py`
- obsolete V3 user/developer documentation and audit artifacts

Keep tests for tenant isolation, media serving, preview security, candidate history, adoption, publication separation, lead creation, and notifications. Rewrite those tests against the final single-engine entry point rather than deleting their behavioral guarantees.

## Removal gate

Removal is allowed only when the 12-site desktop/mobile review is complete, the result is explicitly `GO`, the production compatibility suite is green, and a rollback path for already published V3 HTML is documented. No database migration is introduced by renderer V0.1.
