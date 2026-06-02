# UI Operator Smoke Log

Use this log after the automated checks pass. This is operator-filled evidence for the live browser workflow on the local app.

## Session Metadata

- Date:
- Operator:
- App URL:
- Browser:
- Run used for completed-run checks:
- Run used for delete test:

## Checklist

- [ ] Open `/` and hard refresh with `Ctrl+F5`
- [ ] Homepage loads the React operator dashboard
- [ ] Queue form shows `Latitude`, `Longitude`, and `Run name`
- [ ] External tile preview OFF shows `Map preview disabled`
- [ ] External tile preview ON shows a real tile grid or a clear load error
- [ ] Queue a run successfully
- [ ] Live progress updates without clicking `Open` again
- [ ] Completed run opens successfully
- [ ] `Overview` tab renders expected lifecycle and downloads
- [ ] `Exports` tab search / expand / guarded download works
- [ ] `Status History` tab shows public-safe history only
- [ ] `Diagnostics` tab shows real QA only, no fake metrics
- [ ] `Run Archive` search works
- [ ] `Run Archive` status filter works
- [ ] `Run Archive` sort works
- [ ] `Storage Health` panel appears and looks reasonable
- [ ] Largest / oldest / stale-failed recommendations appear correctly
- [ ] Terminal test run can be deleted through typed confirmation
- [ ] Active run delete is blocked
- [ ] Deleted-runs / freed-space summary updates
- [ ] No coordinates appear outside queue input / preview
- [ ] No local paths or credentials appear
- [ ] Downloads remain guarded

## Observed UX Defects

- None:
- Issue 1:
- Issue 2:
- Issue 3:

## Result

- [ ] PASS
- [ ] PASS WITH DEFECTS
- [ ] FAIL

## Notes

- 
