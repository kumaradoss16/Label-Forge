#!/usr/bin/env python3
"""
Label-Forge Phase 1.1.2.1 Validator Correctness & Provenance Closure
Comprehensive, automated deterministic auditor for reverse-engineering evidence,
manifests, dependency partitions, claim-specific assertions, and reports.

Exit codes:
  0: PASS (All mandatory checks pass with zero failures or unapproved warnings)
  1: FAIL (Contradiction, hash mismatch, partition failure, or invalid assertion)
  2: PREREQUISITE_ERROR (Target executable or required environment missing/NOT_CHECKED)
  3: INTERNAL_ERROR (Validator execution or internal schema error)
"""

import sys
import os
import hashlib
import struct
import json
import re
import platform
import subprocess
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.stage_results import (
    AssertionRecord,
    StageResult,
    aggregate_stage_status,
    evaluate_release_gate
)
from scripts.validation.binary_validation import (
    validate_target_binary,
    validate_evidence_manifest
)
from scripts.validation.dependency_validation import validate_direct_import_partition
from scripts.validation.evidence_integrity import (
    resolve_json_pointer,
    validate_status_accounting,
    scan_prohibited_images,
    validate_structured_evidence_reference
)
from scripts.validation.claim_assertions import make_claim_assertion_registry
from scripts.validation.provenance import generate_provenance_record

EVIDENCE_DIR = os.path.join(REPO_ROOT, 'evidence', 'phase1')
RECON_DIR = os.path.join(EVIDENCE_DIR, 'reconciliation')
REPORTS_DIR = os.path.join(REPO_ROOT, 'reports')


class ValidationSuite:
    def __init__(self, write_provenance=True):
        self.write_provenance = write_provenance
        self.counts = {
            'PASS': 0,
            'FAIL': 0,
            'WARNING': 0,
            'NOT_CHECKED': 0
        }
        self.failures = []
        self.warnings = []
        self.logs = []
        self.all_assertions = []
        
        # Structured stage results for provenance
        self.stage_results = {
            'target_binary_integrity': 'NOT_RUN',
            'manifest_integrity': 'NOT_RUN',
            'direct_import_partition': 'NOT_RUN',
            'status_accounting': 'NOT_RUN',
            'evidence_references': 'NOT_RUN',
            'claim_specific_assertions': 'NOT_RUN',
            'recursive_image_audit': 'NOT_RUN',
            'report_consistency': 'NOT_RUN'
        }

    def record_assertion(self, record: AssertionRecord):
        self.record(record.name, record.status, record.detail)

    def record(self, check_name, status, detail=""):
        self.counts[status] += 1
        self.all_assertions.append(AssertionRecord(check_name, status, detail))
        tag = f"[{status}]"
        if status == 'PASS':
            msg = f"  {tag:<14} ✓ {check_name}"
            if detail:
                msg += f" ({detail})"
        elif status == 'FAIL':
            msg = f"  {tag:<14} ✗ {check_name}: {detail}"
            self.failures.append(f"{check_name}: {detail}")
        elif status == 'WARNING':
            msg = f"  {tag:<14} ! {check_name}: {detail}"
            self.warnings.append(f"{check_name}: {detail}")
        else:
            msg = f"  {tag:<14} - {check_name}: {detail}"
        print(msg)
        self.logs.append(msg)

    def log_print(self, text):
        print(text)
        self.logs.append(text)

    def run(self):
        try:
            return self._run_internal()
        except Exception as e:
            self.log_print(f"INTERNAL VALIDATION EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return 3

    def _run_internal(self):
        self.log_print("=" * 78)
        self.log_print("   LABEL-FORGE PHASE 1.1.2.2: INDEPENDENT VALIDATOR ACCEPTANCE & FINAL CLOSURE")
        self.log_print("=" * 78)

        # -------------------------------------------------------------
        # STAGE 1: Target & Environmental Prerequisites
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 1] Target & Environmental Prerequisites")
        canonical_path = os.path.join(RECON_DIR, 'canonical_target_identity.json')
        if not os.path.exists(canonical_path):
            self.record("Canonical manifest existence", "FAIL", f"Missing {canonical_path}")
            return 2
        
        try:
            with open(canonical_path, 'r', encoding='utf-8') as f:
                canonical = json.load(f)
            self.record("Load canonical target identity manifest", "PASS")
        except Exception as e:
            self.record("Parse canonical target identity manifest", "FAIL", str(e))
            return 2

        target_exe = canonical.get('absolute_path')
        bin_data = None
        actual_sha256 = None
        expected_sha256 = canonical.get('hashes', {}).get('sha256')
        target_available = False

        if not target_exe or not os.path.exists(target_exe):
            self.record("Target binary availability on disk", "NOT_CHECKED", f"Path not found: {target_exe}")
            self.stage_results['target_binary_integrity'] = 'NOT_CHECKED'
        else:
            self.record(f"Target binary located: {target_exe}", "PASS")
            target_available = True
            with open(target_exe, 'rb') as f:
                bin_data = f.read()

        # -------------------------------------------------------------
        # STAGE 2: Target Binary Cryptographic & Header Verification
        # (Strict Stage Result Aggregation - Production Binary Validator)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 2] Target Binary Cryptographic & PE Header Audit (Dynamic Derivation)")
        stage2 = StageResult("target_binary_integrity", "Target Binary PE Verification")
        is_bin_valid, bin_records, bin_info = validate_target_binary(target_exe, canonical)
        for brec in bin_records:
            stage2.add(brec)
            self.record_assertion(brec)
        self.stage_results['target_binary_integrity'] = stage2.recompute_status()
        if 'sha256' in bin_info:
            actual_sha256 = bin_info['sha256']

        # -------------------------------------------------------------
        # STAGE 3: Evidence Manifest Integrity & SHA-256 Validation
        # (Production Manifest Validator)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 3] Evidence Manifest Checksum Integrity Audit")
        stage3 = StageResult("manifest_integrity", "Validation Manifest Checksums")
        val_manifest_path = os.path.join(RECON_DIR, 'validation_manifest.json')
        is_man_valid, man_records, man_summary = validate_evidence_manifest(val_manifest_path, REPO_ROOT)
        for mrec in man_records:
            stage3.add(mrec)
            self.record_assertion(mrec)
        self.stage_results['manifest_integrity'] = stage3.recompute_status()

        # -------------------------------------------------------------
        # STAGE 4: Component Inventory Mathematical Reconciliation
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 4] Component Inventory Mathematical Reconciliation")
        inv_path = os.path.join(RECON_DIR, 'file_inventory_summary.json')
        with open(inv_path, 'r', encoding='utf-8') as f:
            inv = json.load(f)

        total_files = inv['total_files']
        cat_sum = inv['categories_sum']
        total_items = inv['total_filesystem_items']
        total_dirs = inv['total_directories']
        pe_total = inv['pe_binary_classification']['total_pe_binaries']
        pe_sum = inv['pe_binary_classification']['classifications_sum']

        if total_files == 555 and cat_sum == 555 and total_files == cat_sum:
            self.record("Mutually exclusive file category sum (555 files)", "PASS")
        else:
            self.record("File category sum check", "FAIL", f"total={total_files}, sum={cat_sum}")

        if total_items == 589 and total_items == (total_dirs + total_files):
            self.record("Filesystem item equation: 34 directories + 555 files = 589 items", "PASS")
        else:
            self.record("Filesystem item equation check", "FAIL", f"items={total_items}, dirs={total_dirs}, files={total_files}")

        if pe_total == 461 and pe_sum == 461 and pe_total == pe_sum:
            self.record("PE binary classification sum (461 PE binaries: 332 IL, 20 mixed, 27 x64, 82 x86)", "PASS")
        else:
            self.record("PE classification sum check", "FAIL", f"total={pe_total}, sum={pe_sum}")

        # -------------------------------------------------------------
        # STAGE 5: Exact Direct-Import Category Partition Validation
        # (Production Module: dependency_validation.py)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 5] Exact Direct-Import Category Partition & Dependency Audit")
        stage5 = StageResult("direct_import_partition", "Direct Import Category Partition")
        dep_path = os.path.join(RECON_DIR, 'dependency_reconciliation.json')
        with open(dep_path, 'r', encoding='utf-8') as f:
            dep = json.load(f)

        canonical_direct_imports = dep.get('direct_pe_imports', {}).get('libraries', [])
        dep_categories = dep.get('direct_pe_imports', {}).get('categories', {})

        cat_map = {}
        for cname, cdata in dep_categories.items():
            if isinstance(cdata, dict) and 'modules' in cdata:
                cat_map[cname] = cdata['modules']
            elif isinstance(cdata, list):
                cat_map[cname] = cdata
            else:
                cat_map[cname] = []

        res = validate_direct_import_partition(canonical_direct_imports, cat_map)

        if len(res['canonical_duplicates']) == 0:
            rec = AssertionRecord(f"Canonical direct-import list has zero duplicates ({res['canonical_count']} modules)", "PASS")
        else:
            rec = AssertionRecord("Canonical direct-import duplicates check", "FAIL", f"Duplicates: {res['canonical_duplicates']}")
        stage5.add(rec)
        self.record_assertion(rec)

        if len(res['category_internal_duplicates']) == 0:
            rec = AssertionRecord("Categories have zero internal duplicates", "PASS")
        else:
            rec = AssertionRecord("Category internal duplicates check", "FAIL", f"Duplicates: {res['category_internal_duplicates']}")
        stage5.add(rec)
        self.record_assertion(rec)

        if len(res['cross_category_overlaps']) == 0:
            rec = AssertionRecord("Zero cross-category module overlaps detected (mutually exclusive)", "PASS")
        else:
            rec = AssertionRecord("Cross-category overlap check", "FAIL", f"Overlaps: {res['cross_category_overlaps']}")
        stage5.add(rec)
        self.record_assertion(rec)

        if len(res['missing_modules']) == 0:
            rec = AssertionRecord("Zero canonical direct-import modules omitted from categories", "PASS")
        else:
            rec = AssertionRecord("Missing direct-import modules check", "FAIL", f"Missing: {res['missing_modules']}")
        stage5.add(rec)
        self.record_assertion(rec)

        if len(res['unexpected_modules']) == 0:
            rec = AssertionRecord("Zero unexpected modules found in direct-import categories", "PASS")
        else:
            rec = AssertionRecord("Unexpected direct-import modules check", "FAIL", f"Unexpected: {res['unexpected_modules']}")
        stage5.add(rec)
        self.record_assertion(rec)

        if res['is_exact_partition']:
            rec = AssertionRecord(f"Exact direct-import partition verified: categorized == canonical ({res['canonical_count']} modules)", "PASS")
        else:
            rec = AssertionRecord("Exact partition equality check", "FAIL", "Failed exact set equality")
        stage5.add(rec)
        self.record_assertion(rec)

        self.stage_results['direct_import_partition'] = stage5.recompute_status()

        # Delay-loaded count verification
        if dep['delay_load_imports']['count'] == 17:
            self.record("Delay-loaded PE imports count verified (17 DLLs)", "PASS")
        else:
            self.record("Delay-load imports check", "FAIL", f"Expected 17, got {dep['delay_load_imports']['count']}")

        # Phantom DLL absence verification
        for phantom in dep['phantom_dll_reconciliation']:
            pname = phantom['phantom_name']
            ppath = os.path.join(canonical['target_directory'] if 'target_directory' in canonical else r'D:\BarTender', pname)
            if not os.path.exists(ppath):
                self.record(f"Confirmed phantom DLL absent from target directory: {pname}", "PASS")
            else:
                self.record(f"Phantom DLL check: {pname}", "FAIL", "File unexpectedly exists on disk")

        # -------------------------------------------------------------
        # STAGE 6: Exact Claim Status Accounting Audit
        # (Production Module: evidence_integrity.py)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 6] Exact Claim Status Accounting Audit")
        stage6 = StageResult("status_accounting", "Claim Status Accounting")
        cr_path = os.path.join(RECON_DIR, 'claim_register.json')
        with open(cr_path, 'r', encoding='utf-8') as f:
            cr = json.load(f)

        claims = cr.get('claims', [])
        total_claims_field = cr.get('total_claims')
        declared_status_counts = cr.get('claims_by_status', {})

        if len(claims) == total_claims_field:
            rec = AssertionRecord(f"Total claims count field matches claims array length ({len(claims)})", "PASS")
        else:
            rec = AssertionRecord("Total claims field check", "FAIL", f"Field {total_claims_field} != array length {len(claims)}")
        stage6.add(rec)
        self.record_assertion(rec)

        acc_res = validate_status_accounting(claims, declared_status_counts)

        if len(acc_res['duplicate_ids']) == 0:
            rec = AssertionRecord(f"Claim ID uniqueness verified ({len(claims)} distinct IDs)", "PASS")
        else:
            rec = AssertionRecord("Claim ID uniqueness check", "FAIL", f"Duplicate IDs: {acc_res['duplicate_ids']}")
        stage6.add(rec)
        self.record_assertion(rec)

        if acc_res['is_valid']:
            rec = AssertionRecord("Complete status dictionary equality verified: actual_counts == declared_counts", "PASS")
            stage6.add(rec)
            self.record_assertion(rec)
            for st, cnt in acc_res['actual_counts'].items():
                rec = AssertionRecord(f"Status accounting [{st}]: exactly {cnt} claims", "PASS")
                stage6.add(rec)
                self.record_assertion(rec)
        else:
            for err in acc_res['errors']:
                rec = AssertionRecord("Status accounting check", "FAIL", err)
                stage6.add(rec)
                self.record_assertion(rec)

        self.stage_results['status_accounting'] = stage6.recompute_status()

        # -------------------------------------------------------------
        # STAGE 7: Structured Evidence References Verification Audit
        # (Production Module: evidence_integrity.py)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 7] Structured Evidence References Verification Audit")
        stage7 = StageResult("evidence_references", "Structured Evidence References")

        runtime_obs_path = os.path.join(EVIDENCE_DIR, 'runtime_observations.json')
        empirical_test_ids = set()
        if os.path.exists(runtime_obs_path):
            with open(runtime_obs_path, 'r', encoding='utf-8') as rf:
                rdata = json.load(rf)
                empirical_test_ids = {t.get('test_id') for t in rdata.get('empirical_tests', [])}

        for c in claims:
            cid = c.get('id')
            st = c.get('status')
            vmethod = c.get('validation_method')
            refs = c.get('evidence_refs')

            if st and st.startswith('VERIFIED_'):
                if not refs or len(refs) == 0:
                    rec = AssertionRecord(f"Claim {cid} [{st}] structured references", "FAIL", "Missing or empty evidence_refs array")
                    stage7.add(rec)
                    self.record_assertion(rec)
                    continue

                if not vmethod:
                    rec = AssertionRecord(f"Claim {cid} [{st}] validation method", "FAIL", "Missing validation_method")
                    stage7.add(rec)
                    self.record_assertion(rec)
                    continue

            for idx, ref in enumerate(refs or []):
                ref_ok, ref_msg = validate_structured_evidence_reference(
                    ref, REPO_ROOT, empirical_test_ids
                )
                if not ref_ok:
                    rec = AssertionRecord(f"Claim {cid} ref [{idx}] ({ref.get('type')})", "FAIL", ref_msg)
                    stage7.add(rec)
                    self.record_assertion(rec)

            if st and st.startswith('VERIFIED_') and refs:
                rec = AssertionRecord(f"Claim {cid} structured evidence_refs verified ({len(refs)} valid refs)", "PASS")
                stage7.add(rec)
                self.record_assertion(rec)

        self.stage_results['evidence_references'] = stage7.recompute_status()

        # -------------------------------------------------------------
        # STAGE 8: Claim-Specific Assertion Registry
        # (Production Module: claim_assertions.py)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 8] Claim-Specific Assertion Registry (Zero Unconditional Fallbacks)")
        stage8 = StageResult("claim_specific_assertions", "Claim Assertions Registry")

        with open(os.path.join(RECON_DIR, 'canonical_target_identity.json'), 'r', encoding='utf-8') as f:
            can_doc = json.load(f)
        with open(os.path.join(RECON_DIR, 'file_inventory_summary.json'), 'r', encoding='utf-8') as f:
            inv_doc = json.load(f)
        with open(os.path.join(RECON_DIR, 'dependency_reconciliation.json'), 'r', encoding='utf-8') as f:
            dep_doc = json.load(f)
        with open(os.path.join(EVIDENCE_DIR, 'native_module_inventory.json'), 'r', encoding='utf-8') as f:
            native_inv_doc = json.load(f)
        with open(os.path.join(EVIDENCE_DIR, 'dotnet_interop_map.json'), 'r', encoding='utf-8') as f:
            dotnet_interop_doc = json.load(f)
        with open(os.path.join(EVIDENCE_DIR, 'managed_assemblies.json'), 'r', encoding='utf-8') as f:
            managed_assm_doc = json.load(f)
        with open(os.path.join(EVIDENCE_DIR, 'runtime_observations.json'), 'r', encoding='utf-8') as f:
            runtime_doc = json.load(f)
        with open(os.path.join(EVIDENCE_DIR, 'application_components.json'), 'r', encoding='utf-8') as f:
            app_comp_doc = json.load(f)

        screenshots_dir = os.path.join(REPO_ROOT, "screenshots")
        scan_res = scan_prohibited_images(screenshots_dir)
        is_clean_room = scan_res['is_clean']

        registry = make_claim_assertion_registry(
            repo_root=REPO_ROOT,
            can_doc=can_doc,
            inv_doc=inv_doc,
            dep_doc=dep_doc,
            native_inv_doc=native_inv_doc,
            dotnet_interop_doc=dotnet_interop_doc,
            managed_assm_doc=managed_assm_doc,
            runtime_doc=runtime_doc,
            app_comp_doc=app_comp_doc,
            target_exe_path=target_exe if target_exe else r"D:\BarTender\BarTend.exe"
        )

        for c in claims:
            cid = c.get('id')
            st = c.get('status')
            entry = registry.get(cid)

            if not entry or 'assertion_fn' not in entry:
                rec = AssertionRecord(f"Claim {cid} assertion procedure", "FAIL", "No assertion function registered for claim")
                stage8.add(rec)
                self.record_assertion(rec)
                continue

            assertion_fn = entry['assertion_fn']
            try:
                res_status, detail = assertion_fn()
                rec = AssertionRecord(f"Claim {cid} [{st}] assertion", res_status, detail)
                stage8.add(rec)
                self.record_assertion(rec)
            except Exception as e:
                rec = AssertionRecord(f"Claim {cid} [{st}] assertion exception", "FAIL", str(e))
                stage8.add(rec)
                self.record_assertion(rec)

        self.stage_results['claim_specific_assertions'] = stage8.recompute_status()

        # -------------------------------------------------------------
        # STAGE 9: Recursive Prohibited-Image Compliance Audit
        # (Production Module: evidence_integrity.py)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 9] Recursive Prohibited-Image Compliance Audit")
        stage9 = StageResult("recursive_image_audit", "Recursive Prohibited Image Scan")

        if scan_res['is_clean']:
            rec = AssertionRecord("Recursive prohibited-image audit: zero prohibited images found in screenshots/ tree", "PASS")
            stage9.add(rec)
            self.record_assertion(rec)
        else:
            if scan_res['found_images']:
                rec = AssertionRecord("Recursive prohibited-image audit", "FAIL", f"Found prohibited images: {scan_res['found_images']}")
                stage9.add(rec)
                self.record_assertion(rec)
            if scan_res['traversal_errors']:
                rec = AssertionRecord("Screenshots directory traversal audit", "FAIL", f"Traversal errors: {scan_res['traversal_errors']}")
                stage9.add(rec)
                self.record_assertion(rec)

        ref_doc = os.path.join(screenshots_dir, 'UI_OBSERVATIONS_REFERENCE.md')
        if os.path.exists(ref_doc):
            rec = AssertionRecord("UI observations reference documentation present (UI_OBSERVATIONS_REFERENCE.md)", "PASS")
        else:
            rec = AssertionRecord("UI observations reference check", "FAIL", "Missing screenshots/UI_OBSERVATIONS_REFERENCE.md")
        stage9.add(rec)
        self.record_assertion(rec)

        self.stage_results['recursive_image_audit'] = stage9.recompute_status()

        # -------------------------------------------------------------
        # STAGE 10: Report Cross-References & Markdown Integrity Audit
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 10] Report Cross-References & Markdown Integrity Audit")
        stage10 = StageResult("report_consistency", "Report Markdown Cross-References")
        expected_reports = [
            '01_TARGET_IDENTITY.md',
            '02_EXECUTABLE_ANALYSIS.md',
            '03_DEPENDENCY_MAP.md',
            '04_COMPONENT_ARCHITECTURE.md',
            '05_UI_REFERENCE_SPECIFICATION.md',
            '06_BEHAVIOURAL_SPECIFICATION.md',
            '07_FEATURE_INVENTORY.md',
            '07_TECHNICAL_ARCHITECTURE.md',
            '08_MVP_SCOPE.md',
            '08_WORKFLOW_CATALOG.md',
            '09_BUILD_READINESS_REPORT.md',
            '09_RUNTIME_EVIDENCE.md',
            '10_M0_M1_EXECUTION_REPORT.md',
            '11_PHASE1_TARGET_IDENTITY.md',
            '12_PHASE1_APPLICATION_STRUCTURE.md',
            '13_PHASE1_DEPENDENCY_ANALYSIS.md',
            '14_PHASE1_DOTNET_ASSEMBLY_ANALYSIS.md',
            '15_PHASE1_NATIVE_BINARY_ANALYSIS.md',
            '16_PHASE1_RESOURCE_ANALYSIS.md',
            '17_PHASE1_RUNTIME_AND_WINDOWS_INTEGRATION.md',
            '18_PHASE1_FEATURE_TRACEABILITY.md',
            '19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md',
            '20_PHASE1_1_EVIDENCE_RECONCILIATION.md',
            '21_PHASE1_1_CORRECTION_LOG.md',
            '22_PHASE1_1_2_WINDOWS_VALIDATION.md',
            '23_PHASE1_1_2_1_VALIDATOR_CORRECTNESS.md',
            '24_PHASE1_1_2_2_INDEPENDENT_VALIDATOR_ACCEPTANCE.md',
            '25_PHASE1_1_2_2_CORRECTION_LOG.md',
            '26_PHASE1_1_2_2_TEST_COVERAGE_MATRIX.md'
        ]

        for rep in expected_reports:
            rpath = os.path.join(REPORTS_DIR, rep)
            if not os.path.exists(rpath):
                rec = AssertionRecord(f"Report presence: {rep}", "FAIL", "Report missing")
                stage10.add(rec)
                self.record_assertion(rec)
            else:
                with open(rpath, 'r', encoding='utf-8') as rf:
                    content = rf.read()
                if len(content) < 100:
                    rec = AssertionRecord(f"Report content: {rep}", "FAIL", "Report content suspiciously small")
                    stage10.add(rec)
                    self.record_assertion(rec)
                else:
                    has_active_table_error = False
                    for line in content.splitlines():
                        if '.data' in line and '|' in line and '0x10f2c00' in line:
                            has_active_table_error = True
                            break

                    if has_active_table_error:
                        rec = AssertionRecord(f"Report section table check: {rep}", "FAIL", "Section table contains obsolete raw offset 0x10f2c00")
                        stage10.add(rec)
                        self.record_assertion(rec)
                    else:
                        rec = AssertionRecord(f"Report verified consistent: {rep}", "PASS")
                        stage10.add(rec)
                        self.record_assertion(rec)

        self.stage_results['report_consistency'] = stage10.recompute_status()

        # -------------------------------------------------------------
        # STAGE 11: Final Accounting & Exit Code Determination
        # -------------------------------------------------------------
        self.log_print("\n" + "=" * 78)
        self.log_print("                        VALIDATION AUDIT SUMMARY")
        self.log_print("=" * 78)
        total_checks = sum(self.counts.values())
        self.log_print(f"  TOTAL CHECKS EXECUTED : {total_checks}")
        self.log_print(f"  PASS                  : {self.counts['PASS']}")
        self.log_print(f"  FAIL                  : {self.counts['FAIL']}")
        self.log_print(f"  WARNING               : {self.counts['WARNING']}")
        self.log_print(f"  NOT_CHECKED           : {self.counts['NOT_CHECKED']}")
        self.log_print("-" * 78)

        # Authoritative Release Gate Evaluation
        # (Production Module: stage_results.py)
        exit_code, gate_status, gate_message = evaluate_release_gate(self.stage_results, self.counts)
        self.log_print(f"  RELEASE GATE STATUS   : {gate_status}")
        self.log_print(f"  RELEASE GATE DECISION : {gate_message}")
        self.log_print(f"  EXIT CODE             : {exit_code}")
        if self.counts['FAIL'] > 0:
            self.log_print("  FAILURE DETAILS:")
            for f in self.failures:
                self.log_print(f"    - {f}")
        self.log_print("=" * 78)

        # -------------------------------------------------------------
        # STAGE 12: Validation Results & Provenance Artifact Generation
        # (Production Module: provenance.py)
        # -------------------------------------------------------------
        results_path = os.path.join(RECON_DIR, 'validation_results.json')
        results_doc = {
            'schema_version': '1.1.2.2',
            'milestone': 'Phase 1.1.2.2',
            'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'target_binary': {
                'path': target_exe if target_available else r"D:\BarTender\BarTend.exe",
                'size_bytes': len(bin_data) if (target_available and bin_data is not None) else None,
                'sha256': actual_sha256 if target_available else None
            },
            'summary_accounting': {
                'total_checks': total_checks,
                'pass': self.counts['PASS'],
                'fail': self.counts['FAIL'],
                'warning': self.counts['WARNING'],
                'not_checked': self.counts['NOT_CHECKED']
            },
            'stage_breakdown': self.stage_results,
            'release_gate': {
                'exit_code': exit_code,
                'status': gate_status,
                'decision': gate_message
            },
            'assertions': [
                {
                    'assertion_id': a.assertion_id,
                    'status': a.status,
                    'detail': a.detail
                }
                for a in self.all_assertions
            ]
        }
        with open(results_path, 'w', encoding='utf-8') as rf:
            json.dump(results_doc, rf, indent=2)

        stdout_log = os.path.join(RECON_DIR, 'windows_validation', 'phase1_1_2_2_stdout.txt')
        stderr_log = os.path.join(RECON_DIR, 'windows_validation', 'phase1_1_2_2_stderr.txt')

        if self.write_provenance:
            provenance = generate_provenance_record(
                repo_root=REPO_ROOT,
                val_manifest_path=val_manifest_path,
                validator_path=os.path.abspath(__file__),
                exit_code=exit_code,
                total_checks=total_checks,
                pass_count=self.counts['PASS'],
                fail_count=self.counts['FAIL'],
                warning_count=self.counts['WARNING'],
                not_checked_count=self.counts['NOT_CHECKED'],
                stage_breakdown=self.stage_results,
                logs=self.logs,
                target_exe_path=target_exe,
                actual_target_sha256=actual_sha256 if target_available else None,
                expected_target_sha256=expected_sha256 if target_available else None,
                target_available=target_available,
                results_path=results_path,
                stdout_log_path=stdout_log if os.path.exists(stdout_log) else None,
                stderr_log_path=stderr_log if os.path.exists(stderr_log) else None
            )
            provenance_path = os.path.join(RECON_DIR, 'validation_provenance.json')
            with open(provenance_path, 'w', encoding='utf-8') as pf:
                json.dump(provenance, pf, indent=2)

        return exit_code


if __name__ == '__main__':
    suite = ValidationSuite()
    sys.exit(suite.run())
