# Plan B Item #31 — Model-Build Policy

Status: App-goal / model-build policy no exact notebook export.

## Canonical notebook cell

```text
cell 232:
  imports segmentation_models_pytorch as smp
  imports torch
  imports timm
  selected encoder: tu-swin_base_patch4_window7_224
  builds smp.UnetPlusPlus(..., encoder_weights="imagenet")
  calls model.eval()
  runs torch.no_grad() forward pass
  applies torch.softmax
  includes resnet50 fallback
```

## Notebook export availability

```text
AI_MODEL_BUILD_POLICY_V7_2.json: FOUND 0
notebook #31 candidate count: 0
```

So exact notebook-export parity is unavailable.

## App manifest validation

```text
manifests/AI_MODEL_BUILD_POLICY_V7_2.json:
  exists: true
  schema_version: plan_b31_ai_model_build_policy_v1
  status: implemented_model_build_policy_only
  source_cell: cell_232
```

Required planning terms were present:

```text
UnetPlusPlus
tu-swin_base_patch4_window7_224
AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy
```

Normal app flags were false:

```text
normal_app_runs_must_build_models
normal_app_runs_must_train_models
normal_app_runs_must_install_ml_dependencies
normal_app_runs_must_download_weights
normal_app_runs_must_write_model_artifacts
normal_app_runs_must_run_inference
```

Runtime/model flags were false:

```text
imports_torch
imports_timm
imports_segmentation_models_pytorch
instantiates_model
loads_weights
runs_forward_pass
```

Public exposure flags were false:

```text
http_servable
frontend_visible
downloadable_via_api
```

## Decision

```text
No code patch.
Keep #31 as a safe app-goal policy/config manifest.
Do not mark notebook execution parity because notebook cell 232 builds/runs a model and the app intentionally does not.
```
