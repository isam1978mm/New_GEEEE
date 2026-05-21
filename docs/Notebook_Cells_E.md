Phase A — Setup, installs, working dirs (0–8)

[0] Defines ColabFolder = "/content/Radar_GRD_RTC" working dir constant.
[1] pip install of segmentation-models-pytorch, timm, albumentations, transformers.
[2] Second pip install (overlapping): geemap, ee-extra, smp, timm, transformers, albumentations, opencv, rasterio, shapely, seaborn, matplotlib.
[3] Imports the full PyTorch / Swin / SegFormer / albumentations / rasterio / shapely / scipy stack.
[4] Another pip install: geedim, rasterio, rioxarray, geopandas, numpy, pandas, tensorflow.
[5] Imports EE/geemap/sklearn/shapely/rasterio + scipy filters, sets ProjectName = 'test-ecd0d', wipes & recreates ./Pair01, ./Pair02, ColabFolder.
[6] Defines refined_lee_filter (stub), apply_radar_filters (numpy refined-Lee), convert_to_db — radar filter functions.
[7] Duplicate of cell 6's radar-filter functions ("Cell 004: Advanced Radar Processing Kitchen").
[8] Mounts Google Drive at /content/drive.

Phase B — Map, point picker, ROI (9–13)

[9] Builds a geemap.Map centered on 35.555272, 36.085217, adds Google Satellite/Hybrid tiles + a Nominatim search widget; user clicks to set SelectedPoint.
[10] Colab JS hack that auto-scrolls to the next cell after map interaction.
[11] Prints SelectedPoint as EE Geometry / GeoJSON / WKT / lat-lon.
[12] Builds two ROIs: NewRoi15KM (degree-approx 15 km square in WGS84) and NewRoi6KM (exact 6.4 km square in UTM37N around the point).
[13] Prints WKT for both ROIs in WGS84 and UTM and verifies the UTM zone.

Phase C — RUN folder + grid manifest + DEM (14–18)

[14] Builds RUN_<TAG> folder tree on Colab+Drive, writes the authoritative GRID dict (EPSG:32637 / 10 m / 640×640 / crsTransform / bounds_utm) and PATHS / PATHS_DRIVE_GLOBAL, deletes other RUN folders.
[15] Pulls Copernicus GLO-30 DEM via GEE, reprojects to the master grid, writes dem_tif + dem_npy inside RUN.
[16] RUN+GRID guard cell: refuses to proceed if PATHS/GRID missing or write path is outside the RUN.
[17] ZERO-SHIFT GATE: opens DEM file and asserts CRS / width / height / pixel size / origin / rotation / nodata exactly match GRID (1 mm tolerance).
[18] Scans every .tif under RUN folders and audits each one against the master grid; prints any drift.

Phase D — Sentinel-1 GRD → RTC pipeline (19–24)

[19] SAR_CORE FINAL vRUN: defines to_grid() reprojection helper + finalize_for_export(); locks all SAR work to GRID.
[20] MASTER-MATCHED QA: queries S1_GRD over the ROI, picks best track / orbit window / VV-VH pair (≤24 h apart), writes selection JSON to QA folder.
[21] 14.788 NO-COP-DEM: outputs VV_dB, VH_dB, incidence-angle on the master grid using dB→linear→speckle filter→dB, with no Copernicus-DEM call inside GEE.
[22] Initializes Earth Engine with project test-ecd0d (does ee.Authenticate() fallback — that's the auth-flow the screening project's safety constants forbid).
[23] More grid helpers, dB-safe versions (14.999 vRUN SAFE).
[24] Master S1 cell: pulls S1_GRD, runs the SAR chain, exports VV_dB / VH_dB / logRatio_dB / angle to Drive first, copies back to Colab; uses local DEM for RTC instead of GEE-side DEM.

Phase E — Drive-export waits, pixel-alignment QA (25–35)

[25] Watches Drive for SAR exports to land, copies them into the RUN.
[26] Per-band stats / nodata audit on the SAR GeoTIFFs.
[27] 017-PRO: pixel-center alignment test between SAR bands and DEM (sub-pixel offset).
[28] QA cell that auto-rebuilds logRatio_dB = VV_dB − VH_dB if it's missing, then runs nodata-fraction stats.
[29] 018-PRO: edge-consistency test for nodata along the four tile boundaries.
[30] Guard cell — RUN/GRID lock and nodata fraction check.
[31] Guard variant — ensures final_radar has VV/VH and rebuilds logRatio if missing.
[32] Single shell line: !ls -lh /content/drive/MyDrive/Radar_GRD_RTC/.
[33] Loads cube (HWC numpy stack) and writes per-band GeoTIFFs into RUN using DEM georef.
[34] Reads DEM georef + the four S1 tifs, prints whether CRS / size / transform match.
[35] Big guard cell — full RUN/GRID lock + ensures helpers exist + makes radar dirs.

Phase F — "Nano / Treasure / Geophysics" feature stacks (36–45)

[36] NANO-GEOPHYSICS STACK: builds nano-scale geophysics features from VV/VH, exports per-band TIF+NPY+stack NPY.
[37] Duplicate variant of cell 36 (same naming, different internals).
[38] QA pass over NANO_*.tif files.
[39] TREASURE / GEOPHYSICS STACK 640: more derived layers from VV/VH dB.
[40] QA pass over treasure/geophysics tifs.
[41] Final export presence check — verifies the expected output set actually exists.
[42] Texture / tensors essentials QA — opens every band and prints stats.
[43] Master geometry-consistency check across every official GeoTIFF in the RUN.
[44] FIXED STRATEGIC ALT STACK 640 — yet another stack export.
[45] Final project inventory; emits df_summary.to_csv(...).

Phase G — More feature stacks, rename layer (46–55)

[46] One-line Arabic comment: "all preceding cells just need output-name fixes for AI-library compatibility."
[47] MASTER RTC REFINED 640 — refined RTC layers built from cell-015 pairs.
[48] QA + matplotlib visual check on the refined RTC outputs.
[49] SIGMA0 MASTER 640 — sigma0 master stack from S1 pairs.
[50] Duplicate SIGMA0 MASTER 640 with cleaner AI naming.
[51] GPHYS MASTER 640 — geophysics master stack.
[52] ARCH TARGETS 640 — "archaeology targets" derived stack.
[53] RAD MASTER CUBE 640 — radar master cube.
[54] ULTIMATE GPHYS SCAN 640 — averages many scans into a final stack.
[55] Empty cell.

Phase H — Hypercube + auditor + PCA anomaly + object extraction (56–71)

[56] ARCH INTEL PHYSICS FEATURES 640 — texture / sobel / morphology features from the local cube.
[57] GOLDEN AUDITOR 640 — full audit of grid/CRS/transform/nodata across every official tif, writes CSV.
[58] HYPERCUBE SCI 640 — assembles all official tifs into one robust-normalized hypercube NPY.
[59] HCUBE QUICK CHECK — loads the hypercube and prints shape/min/max/mean.
[60] AUX GPHYS FEATURES 640 — auxiliary geophysics from VV/VH.
[61] AUX GPHYS FEATURES 640 (PHYSICS-CORRECTED) — physics-corrected re-run of cell 60.
[62] One-line Arabic note about which cell switched save-path from Drive to Colab.
[63] AUX METAL FEATURES 640 — "metal-signature" derived layers (Colab-local only).
[64] GLOBAL SAR ARCHAEOLOGY INDEX SET 640 — domain-specific SAR indices from VV/VH only.
[65] GLOBAL SAR ARCHAEO HYPERCUBE 640 — assembles those indices into a second hypercube.
[66] PCA ANOMALY TARGET MAP 640 — fits sklearn PCA to the hypercube, writes anomaly-energy TIF.
[67] Duplicate of cell 66 with same naming.
[68] PCA CANDIDATE LABELS TO OBJECT TABLE — connected-component labeling on the PCA anomaly mask, emits objects_index.csv.
[69] AI OBJECT CLASSIFY + CLUSTER SUMMARY — DBSCAN over the object table, writes classified CSV + cluster summary.
[70] AI CONTEXT EXPORT + TAGGING — exports per-object context patches and tags.
[71] AUTO OBJECT EXTRACTION FROM SCIENTIFIC HYPERCUBE — watershed + peak-local-max + regionprops; writes proposals, binary mask, labels, object index, per-object NPY patches.

Phase I — Bonus/simulator features, tensor exports, alignment QA (72–79)

[72] CLL 21 FINAL BONUS FEATURES.
[73] CLL 19 GEOPHYSICAL SIMULATORS 640 — synthetic simulator layers.
[74] CLL 20 FINAL AI-READY TENSOR EXPORT 640 — robust-normalizes every official layer to 0–1, emits per-band TIF/NPY + stack NPY.
[75] Duplicate variant of cell 74.
[76] CLL 22 EXTRA AI TENSORS — pulls S2 across 2022–2026 (Jan/Apr/Aug, cloud<3 %), aligns to grid.
[77] Variant of cell 76 with stricter grid-fixing.
[78] Drive/Colab twin pixel-match QA — opens same filename on both sides and diffs.
[79] Full TIF alignment QA — sub-pixel check (≤0.25 px) across radar + optical.

Phase J — Stragglers + DEM-matched S2 masks (80–94)

[80] Tiny inspector — lists tifs in radar_tif_dir with shape/dtype/nodata.
[81] CLL 24 DEM-MATCHED AI MASKS 640 — S2 (2022-01-01 → 2026-02-28, cloud<3 %) masks aligned to DEM grid.
[82] Sanity check that picks a "master reference" tif and prints georef.
[83] CLL 24 fix variant — S2 collection rebuild with Tesla v7.2 grid lock.
[84] Master-grid audit comparing a chosen master to every other layer.
[85] Cancels in-flight EE export tasks.
[86] Forces Colab to refresh Drive view (triggers metadata sync).
[87] More path verification + DEM-anchored alignment checks.
[88] Repeat of cell 87 with minor differences.
[89] Opens the final hypercube path, prints shape and bands.
[90] Same as cell 89 with a different reference path.
[91] MASTER_DEM-anchored reproject of remaining layers onto the master grid.
[92] Repeat of cell 89.
[93] Compares ref tif to a test tif (Tesla v7.2 dynamic-reference protocol).
[94] Tesla v7.2 protocol cell — S2 collection median over the ROI.

Phase K — "Tesla v7.2" inference engines (95–103)

[95] CLL 25 — محرك الاستدلال الذري للكنوز والمواد الثمينة (Atomic Inference Engine for Treasures): S2 median, builds an B12/B11 "gold signature" + thermal anomaly index, and other claimed "precious-material" indices.
[96] Tesla v7.2 — small driver that runs the inference cells in order.
[97] CLL 27 — Fusion Center: combines S2 + Landsat 9 thermal into a "Multi-Sensor Intelligence Matrix" with named tensors (AI_BEH_VegRoot_Anomaly, etc.).
[98] Loads the resulting hypercube TIF and runs detailed band-by-band stats.
[99] DEM-anchored S2 reprojection of the fusion outputs back to the 640 grid.
[100] Authoritative-references variant.
[101] Repeat of cell 100.
[102] Metadata-recovery cell — re-derives transforms from existing tifs when manifest is lost.
[103] Forces Drive refresh + iterates over files printing stats.

Phase L — DEM_GEO8 + thermal + Zero-Point report + focus mask (104–119)

[104] DEM_GEO8_TIFS (PRO) — derives 8 DEM-based layers (slope, aspect, curvature, TPI, TRI, roughness, etc.) on the master grid.
[105] Landsat 9 TOA pull + thermal mask aligned to DEM grid.
[106] Same pattern — Landsat 9 TOA aligned to DEM.
[107] Re-run of cell 104 (DEM_GEO8 duplicate).
[108] S1_GRD pull (re-do of part of the SAR chain).
[109] Opens DEM tif and writes derived layers.
[110] Drive file locator — scans Drive to find "REPORT" files.
[111] Debug-zero-point report inside current RUN.
[112] Same family — DEM-source derived layers.
[113] S1 MASK INSPECTOR — chooses the best S1 layer to use as the geometric anchor.
[114] Generates S1_MASK_TIF-anchored derived rasters.
[115] Guards + paths for the next downstream cells; opens hypercube.
[116] Reads HYPERCUBE_IN, writes a transformed hypercube.
[117] Reads HYPERCUBE_TIF, runs per-band ops.
[118] Opens FOCUS_MASK_TIF and validates it.
[119] CELL 005 — ROI-CONSTRAINED AI ANALYSIS INSIDE 17m FOCUS: this is where the "17m focus mask" appears. Restricts hypercube analysis to a ~17 m × 17 m focus region (defines FOCUS_MASK_17M). Writes the FeatureCollection GeoJSON.

Phase M — Tesla v7.2 hard classifiers (120–135)

[120] One-liner display(top_df).
[121] CELL 005C — CORE-vs-RING-vs-SCENE SCIENTIFIC DECISION at 2 m analysis grid super-resolved over native 10 m; writes targets CSV / TXT / JSON.
[122] Hard classifier writing GeoJSON of detected features.
[123] Another hard-classifier variant with FeatureCollection export.
[124] QA CSV STRUCTURE INSPECTOR — checks QA CSVs before training.
[125] INSPECT PIXEL/TARGET QA FILES FOR 640×640 GRID.
[126] Duplicate of cell 125.
[127] Large classifier cell (559 lines) emitting CSV + image-band outputs.
[128] HARD TYPE CLASSIFIER (STRICT CORE-9 / POINT-LOCKED) — rule-based labels: entrance / shaft / chamber / void / metal / metal-type / metal-shape / estimated stacked boxes / aligned jars / content type.
[129] Stub helper that ensures QA_DIR and TRAIN_CSV exist.
[130] PATCH HYPERCUBE FROM DRIVE — adds/derives missing 10 m layers from Drive.
[131] HYPERCUBE AUDIT — channels / 10 m availability / gaps.
[132] Largest cell in notebook (851 lines) — full multi-class rule-based target classifier with extensive band-by-band logic.
[133] Tesla v7.2 advanced protocol — dumps geojson_features to file.
[134] Duplicate of cell 132.
[135] MULTI-TARGET HARD CLASSIFIER + SUBPIXEL CENTERING (899 lines, biggest in the notebook) — runs the classifier across all targets inside CORE_9 with subpixel-center refinement.

Phase N — Outputs sanity + KMZ generation (136–162)

[136] Small os.listdir(...) check.
[137] print(os.listdir(PATHS_DRIVE_GLOBAL['qa_root'])).
[138] Markdown header: "Generating Intelligence KMZs (Google Earth)."
[139] GENERATE INTELLIGENCE KMZs — emits AI_HEATMAP_CLASSIFICATION.kmz and AI_3D_TARGET_VISUALIZATION.kmz with exact lat/lon.
[140] STAGE 1 — MATRIX AUDIT + AI REQUIREMENTS MAPPER — maps hypercube bands to YOLO/CNN/Swin input requirements.
[141] STAGE 2A — RUN LAYER INVENTORY + 17M MASK REBUILDER.
[142] "عامر تحديث" — Amer update — re-anchors layers to ref tif.
[143] "خلية فحص" — thermal-anomaly inspection cell.
[144] Empty cell.
[145] STAGE 2C-1B — LANDSAT DAY LST BUILDER — Landsat 8/9 ST_B10 daytime LST aligned to grid.
[146] LANDSAT thermal-anomaly variant.
[147] Tensor-builder that opens IN_TIF and produces normalized inputs.
[148] STAGE 4 — AI TENSOR BUILDER for YOLOv11 / CNN / Swin / SegFormer.
[149] Detection-result GeoJSON FeatureCollection exporter.
[150] STAGE 5A — AI LIBRARIES INSTALL (ultralytics, timm, smp, plotly, kaleido).
[151] Variant install: ultralytics + timm + smp + albumentations + einops + plotly + kaleido.
[152] One-line Arabic note: "before Pro subscription for higher accuracy."
[153] !pip install simplekml.
[154] Conditional import simplekml with auto-install fallback.
[155] FINAL KMZ — heatmap + 3D targets, with "depth-safe" fix.
[156] More KMZ heatmap classification output.
[157] Reads back AI_HEATMAP_CLASSIFICATION.png and renders it.
[158] Opens an AI_HEATMAP_CLASSIFICATION.kmz and displays its contents.
[159] AI_TARGETS_ONLY_17M.kmz exporter.
[160] AI_TARGETS_3D_ONLY.kmz exporter.
[161] Searches for existing KMZs.
[162] simplekml-based KMZ heatmap regenerator.

Phase O — Training scaffolding + AI inference pipeline (163–178)

[163] LEARN REAL WEIGHTS FROM YOUR DATA — outlines a small training step over labeled treasures/burials/weapons signatures.
[164] PROFESSIONAL GLOBAL ARCHAEO-TRAINING (640×640 GRID) memory-optimized for ~12 GB VRAM.
[165] Same training cell, high-fidelity variant.
[166] Same training cell, low-memory (≤11 GB) variant.
[167] Loads hypercube and runs band stats — pre-training check.
[168] Same pattern.
[169] Large 489-line classifier/inference loop.
[170] Markdown: "Executing Model Dependencies."
[171] Colab JS that auto-runs setup cells in order.
[172] Markdown describing the inference engine's class structure (jar of gold, sarcophagus, burial chamber, etc.).
[173] Driver cell that runs the inference once final_data_input and Final_Target_Model exist.
[174] !pip install rasterio timm simplekml.
[175] Markdown about preparing model + data for inference (UnetPlusPlus, ResNet50, ImageNet weights, 224×224 input).
[176] Hypercube guards + paths preparation for inference.
[177] CELL 006 — AI OBJECT DETECTOR (CNN + SHAPE DETECTOR) — runs inside 17 m focus, emits detector CSV + GeoJSON.
[178] CELL 006 — AI OBJECT DETECTOR (V7.4 | 1 DUNAM | GOOGLE SATELLITE) — same idea on a ~1 dunam (1000 m²) ROI.

Phase P — More iterations + CNN exec + metal-fingerprint scanner (179–202)

[179] Markdown: "Executing Dependencies and Model Inference."
[180] Big cell prefixed "do not run" by Lyle's comment — large classifier.
[181] 485-line classifier with FeatureCollection GeoJSON export.
[182] 673-line classifier.
[183] Empty.
[184] CNN execution CSV exporter (CNN_EXEC_CSV).
[185] METAL FINGERPRINT DIAGNOSTIC — direct diagnostic of the metal signature on the nearest pixel of each target.
[186] Empty markdown.
[187] FULL STRATEGIC TARGET SCANNER (MANUAL SWAP EDITION).
[188] Tesla v7.2 protocol cell — references hypercube path.
[189] Folder check for previous outputs.
[190] Authoritative-references variant, dumps geojson_features.
[191] Advanced field-mapping cell — emits TESLA_V7_2_FIELD_OPERATIONS.kmz.
[192] Anchors hypercube to S1 mask + reprojects to ref geometry.
[193] Authoritative-paths sync + ref-DEM open.
[194] More auth-refs cell.
[195] "كود مراقبة" — monitoring cell for REPORT_640_FINAL_Zero_Point_Targets.tif.
[196] Defines Focus_ROI_17m from SelectedPoint + EE feature styling.
[197] Master-DEM-anchored open.
[198] Auth-refs check with geemap + ee + pyproj.
[199] Dynamic auth-refs hypercube open.
[200] Same as 191 — TESLA_V7_2_FIELD_OPERATIONS.kmz emit.
[201] Same as 199.
[202] Checks that TESLA_V7_2_FIELD_OPERATIONS.kmz exists in QA folder.

Phase Q — Drive scans + S2 era pulls + radar pulls (203–215)

[203] Iterates a "secrets" folder and opens every tif (file_full_path).
[204] Walks every output folder.
[205] CLL 32 — S2_SR_HARMONIZED pull with "Incompatible Bands" workaround.
[206] Same as 203.
[207] Sweep & inspect separate 640 layers.
[208] Path correction for Drive access.
[209] Same as 203/206.
[210] Old-S2 (2018–2019) vs current-S2 comparison.
[211] Pulls the last S2 image at the selected point.
[212] Radar VV via COPERNICUS/S1_GRD filter.
[213] Walks /content/ and prints every folder/file.
[214] Loads depth_file numpy arrays.
[215] Creates /content/Radar_GRD_RTC_Tensors dir for manual file upload.

Phase R — Reference-tif comparison utilities (216–230)

[216] Reads basic info from a filepath tif.
[217] Diagnoses a problem reading Master_reference_dim.tif.
[218] Auto-detects the reference layer based on filename.
[219] Sets # Tishreen — explicitly names the target region (Tishreen, Aleppo Governorate, Syria).
[220] Reads each layer over the common bounds.
[221] Lists tifs in Radar_GRD_RTC_Tensors.
[222] Loads ref tif + iterates layers.
[223] Saves layers as numpy.
[224] Lists files in /content/Matrex/NPY.
[225] Loads all numpy arrays with scipy signal processing.
[226] No-op cell — "logic moved to previous cell."
[227] "البحث عن نقاط GPS و مقارنتها" — GPS-point search and comparison cell.
[228] Writes a TXT report of right-vs-wrong matches.
[229] Filename glob search by NAME_HINT.
[230] Links numpy matrices to analysis pipeline, emits CSV report.

Phase S — CNN model build attempts (231–243)

[231] Builds 3-layer RGB-like stack for CNN input.
[232] First model attempt: smp.UnetPlusPlus(encoder='tu-swin_base_patch4_window7_224', classes=5) → softmax → hotspot localization.
[233] Broken: defines class ArcheoAI_Leader(nn.Module) with def init(self) instead of def __init__ — the class never actually constructs.
[234] Incidence-angle correction for radar.
[235] Working model build: Final_Target_Model = smp.UnetPlusPlus(encoder='resnet50', encoder_weights='imagenet', in_channels=3, classes=5).
[236] FINAL TARGET INFERENCE — runs model, uses an "archeo_dictionary" with classes like Gold_Metal_Jar, Sarcophagus_Naos, Statue_Box, Open_Tunnel_Void, Buried_Entrance, Compressed_Chamber, Solar_Tomb, Temple_Hall, Red_Mercury_Trace, Black_Mercury_Trace, Weapons_Shield_Cache, Ancient_Well.
[237] Exports FINAL_TARGETS_FIELD_MAP.kmz with detection geometry.
[238] final_archeo_engine(prob_map, threshold) — geometric engine that classifies into gold/glass/pottery/sarcophagus.
[239] pro_structural_scanner — applies man-made-geometry filters (right angles, longitudinal voids) to suppress nature.
[240] final_decision_scanner — "CNN + YOLO Architecture" overall driver.
[241] Same as 237 — emits FINAL_TARGETS_FIELD_NAV_V7_2.kmz.
[242] trace_stairs_path(probs_map, stairs_loc) — traces a path forward from a detected "staircase" pixel, prints class label + score + lat/lon for each finding.
[243] Final cell — overlays the CNN probability matrix directly onto a live geemap.Map with HYBRID basemap, draws markers and area buffers at every detected target's exact coordinates, then attempts to draw lines between "temple-hall" and "stairs" features.
[244] Markdown: stub # Task.


Quick numbers

Useful science core (defensible): cells 14–35, 56–67, 74, 79, 104, 145. That's the grid lock + S1 pipeline + DEM derivatives + Landsat thermal + PCA anomaly + hypercube + alignment QA — about 30 cells worth of real signal.
Candidate/object extraction (defensible logic, vague output naming): cells 68–71.
Duplicates / near-duplicates: at least 30 cells (multiple Cell 015, SIGMA0 MASTER, PCA ANOMALY, "Authoritative References", DEM_GEO8 etc.).
One known code bug: cell 233 (def init should be def __init__).
Cells that emit exact lat/lon to KMZ/GeoJSON: 119, 122, 123, 128, 132, 134, 135, 139, 149, 155, 156, 158, 159, 160, 162, 177, 178, 181, 190, 191, 200, 237, 241, 243.
Cells whose label/concept is the part that pushes from "anomaly detector" into "treasure hunter": 39, 40, 52, 56, 63, 64, 65, 95, 97, 128, 132, 134, 135, 163, 172, 236, 238, 240, 242, 243.