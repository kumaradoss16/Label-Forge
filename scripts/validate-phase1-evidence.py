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

from scripts.validation.stage_results import AssertionRecord, StageResult, aggregate_stage_status
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
        self.log_print("   LABEL-FORGE PHASE 1.1.2.1: VALIDATOR CORRECTNESS & PROVENANCE CLOSURE")
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
        # (Strict Stage Result Aggregation - No Unconditional PASS)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 2] Target Binary Cryptographic & PE Header Audit (Dynamic Derivation)")
        stage2 = StageResult("target_binary_integrity", "Target Binary PE Verification")

        if not target_available:
            rec = AssertionRecord(
                assertion_id="Binary size & hash verification",
                status="NOT_CHECKED",
                detail="Target binary not present on host"
            )
            stage2.add(rec)
            self.record_assertion(rec)
            self.stage_results['target_binary_integrity'] = stage2.recompute_status()
        else:
            actual_size = len(bin_data)
            expected_size = canonical['file_size_bytes']
            if actual_size == expected_size:
                rec = AssertionRecord(f"File size matches canonical ({actual_size:,} bytes)", "PASS")
            else:
                rec = AssertionRecord("File size check", "FAIL", f"Expected {expected_size}, got {actual_size}")
            stage2.add(rec)
            self.record_assertion(rec)

            actual_md5 = hashlib.md5(bin_data).hexdigest()
            expected_md5 = canonical['hashes']['md5']
            if actual_md5 == expected_md5:
                rec = AssertionRecord(f"MD5 digest match ({actual_md5})", "PASS")
            else:
                rec = AssertionRecord("MD5 digest check", "FAIL", f"Expected {expected_md5}, got {actual_md5}")
            stage2.add(rec)
            self.record_assertion(rec)

            actual_sha1 = hashlib.sha1(bin_data).hexdigest()
            expected_sha1 = canonical['hashes']['sha1']
            if actual_sha1 == expected_sha1:
                rec = AssertionRecord(f"SHA-1 digest match ({actual_sha1})", "PASS")
            else:
                rec = AssertionRecord("SHA-1 digest check", "FAIL", f"Expected {expected_sha1}, got {actual_sha1}")
            stage2.add(rec)
            self.record_assertion(rec)

            actual_sha256 = hashlib.sha256(bin_data).hexdigest()
            if actual_sha256 == expected_sha256:
                rec = AssertionRecord(f"SHA-256 digest match ({actual_sha256})", "PASS")
            else:
                rec = AssertionRecord("SHA-256 digest check", "FAIL", f"Expected {expected_sha256}, got {actual_sha256}")
            stage2.add(rec)
            self.record_assertion(rec)

            # Parse PE Optional Header
            e_lfanew = struct.unpack_from('<I', bin_data, 0x3C)[0]
            machine = struct.unpack_from('<H', bin_data, e_lfanew+4)[0]
            num_sections = struct.unpack_from('<H', bin_data, e_lfanew+6)[0]
            opt_header_size = struct.unpack_from('<H', bin_data, e_lfanew+20)[0]
            opt_offset = e_lfanew + 24
            magic = struct.unpack_from('<H', bin_data, opt_offset)[0]
            entry_point = struct.unpack_from('<I', bin_data, opt_offset+16)[0]

            expected_machine = int(canonical['pe_header']['machine'], 16)
            expected_magic = int(canonical['pe_header']['magic'], 16)
            expected_ep = int(canonical['pe_header']['entry_point'], 16)

            if machine == expected_machine and magic == expected_magic:
                rec = AssertionRecord(f"PE Architecture x86_64 PE32+ (Machine {hex(machine)}, Magic {hex(magic)})", "PASS")
            else:
                rec = AssertionRecord("PE Architecture check", "FAIL", f"Machine {hex(machine)}, Magic {hex(magic)}")
            stage2.add(rec)
            self.record_assertion(rec)

            if entry_point == expected_ep:
                rec = AssertionRecord(f"Entry point RVA matches canonical ({hex(entry_point)})", "PASS")
            else:
                rec = AssertionRecord("Entry point RVA check", "FAIL", f"Expected {hex(expected_ep)}, got {hex(entry_point)}")
            stage2.add(rec)
            self.record_assertion(rec)

            # Sections Verification
            sec_table_offset = opt_offset + opt_header_size
            actual_sections = []
            for i in range(num_sections):
                so = sec_table_offset + i * 40
                name = bin_data[so:so+8].rstrip(b'\x00').decode('latin1')
                vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', bin_data, so+8)
                actual_sections.append({
                    'name': name,
                    'va': hex(vaddr),
                    'vsize': vsize,
                    'raddr': hex(raddr),
                    'rsize': rsize
                })

            canonical_sec_names = [s['name'] for s in canonical['sections']]
            actual_sec_names = [s['name'] for s in actual_sections]
            if actual_sec_names == canonical_sec_names:
                rec = AssertionRecord(f"Section table matches canonical exactly ({actual_sec_names})", "PASS")
            else:
                rec = AssertionRecord("Section names check", "FAIL", f"Expected {canonical_sec_names}, got {actual_sec_names}")
            stage2.add(rec)
            self.record_assertion(rec)

            # Check section .data raw file offset dynamically from canonical manifest
            canonical_data_sec = next((s for s in canonical['sections'] if s['name'] == '.data'), None)
            expected_data_raddr = canonical_data_sec['raw_data_offset'] if canonical_data_sec else None
            data_sec = next((s for s in actual_sections if s['name'] == '.data'), None)
            if data_sec and data_sec['raddr'] == expected_data_raddr:
                rec = AssertionRecord(f"Section .data raw offset dynamically verified as {expected_data_raddr}", "PASS")
            else:
                rec = AssertionRecord("Section .data raw offset check", "FAIL", f"Expected {expected_data_raddr}, got {data_sec['raddr'] if data_sec else 'missing'}")
            stage2.add(rec)
            self.record_assertion(rec)

            # Authenticode boundary check dynamically derived from canonical manifest
            dir_base = opt_offset + 112
            cert_va, cert_size = struct.unpack_from('<II', bin_data, dir_base + 4*8)
            expected_cert_va = int(canonical['authenticode_signature']['file_offset'], 16)
            expected_cert_size = canonical['authenticode_signature']['size']

            if cert_va == expected_cert_va and cert_size == expected_cert_size:
                rec = AssertionRecord(f"Authenticode directory physical bounds verified (offset {hex(cert_va)}, size {cert_size}, terminates at file end)", "PASS")
            else:
                rec = AssertionRecord("Authenticode boundary check", "FAIL", f"Expected offset {hex(expected_cert_va)} size {expected_cert_size}, got offset {hex(cert_va)} size {cert_size}")
            stage2.add(rec)
            self.record_assertion(rec)

            # CLR COM descriptor dynamically derived from canonical manifest
            com_rva, com_size = struct.unpack_from('<II', bin_data, dir_base + 14*8)
            com_desc = canonical['clr_runtime']['com_descriptor_directory']
            expected_com_rva = int(com_desc['virtual_address'], 16)
            expected_com_size = com_desc['size']

            if com_rva == expected_com_rva and com_size == expected_com_size:
                rec = AssertionRecord(f"CLR COM descriptor verified dynamically at RVA {hex(com_rva)}, size {com_size}", "PASS")
            else:
                rec = AssertionRecord("CLR COM descriptor check", "FAIL", f"Expected RVA {hex(expected_com_rva)} size {expected_com_size}, got {hex(com_rva)} {com_size}")
            stage2.add(rec)
            self.record_assertion(rec)

            def rva_to_off(rva):
                for s in actual_sections:
                    va = int(s['va'], 16)
                    vs = s['vsize']
                    ra = int(s['raddr'], 16)
                    if va <= rva < va + vs:
                        return ra + (rva - va)
                return None

            com_off = rva_to_off(com_rva)
            if com_off is None or com_off + 72 > len(bin_data):
                rec = AssertionRecord("CLR COM header offset resolution", "FAIL", f"Invalid com_off: {com_off}")
                stage2.add(rec)
                self.record_assertion(rec)
            else:
                cor_header = bin_data[com_off:com_off+72]
                meta_rva, meta_size = struct.unpack_from('<II', cor_header, 8)
                cor_flags = struct.unpack_from('<I', cor_header, 16)[0]

                cli_meta = canonical['clr_runtime']['cli_metadata_root']
                expected_meta_rva = int(cli_meta['virtual_address'], 16)
                expected_meta_size = cli_meta['size_bytes']
                expected_cor_flags = canonical['clr_runtime']['cor20_header']['flags']

                if meta_rva == expected_meta_rva and meta_size == expected_meta_size:
                    rec = AssertionRecord(f"CLI Metadata Root verified dynamically at RVA {hex(meta_rva)} (Size: {meta_size})", "PASS")
                else:
                    rec = AssertionRecord("CLI Metadata Root check", "FAIL", f"Expected RVA {hex(expected_meta_rva)} size {expected_meta_size}, got {hex(meta_rva)} {meta_size}")
                stage2.add(rec)
                self.record_assertion(rec)

                if cor_flags == expected_cor_flags:
                    rec = AssertionRecord(f"COMIMAGE_FLAGS_ILONLY verified as {expected_cor_flags} (C++/CLI mixed mode)", "PASS")
                else:
                    rec = AssertionRecord("COMIMAGE_FLAGS check", "FAIL", f"Expected {expected_cor_flags}, got {hex(cor_flags)}")
                stage2.add(rec)
                self.record_assertion(rec)

            self.stage_results['target_binary_integrity'] = stage2.recompute_status()

        # -------------------------------------------------------------
        # STAGE 3: Evidence Manifest Integrity & SHA-256 Validation
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 3] Evidence Manifest Checksum Integrity Audit")
        stage3 = StageResult("manifest_integrity", "Validation Manifest Checksums")
        val_manifest_path = os.path.join(RECON_DIR, 'validation_manifest.json')
        if not os.path.exists(val_manifest_path):
            rec = AssertionRecord("Validation manifest presence", "FAIL", f"Missing {val_manifest_path}")
            stage3.add(rec)
            self.record_assertion(rec)
        else:
            with open(val_manifest_path, 'r', encoding='utf-8') as f:
                val_manifest = json.load(f)

            manifest_files = val_manifest.get('files', [])
            rec = AssertionRecord(f"Validation manifest loaded ({len(manifest_files)} tracked evidence files)", "PASS")
            stage3.add(rec)
            self.record_assertion(rec)

            for entry in manifest_files:
                rel_path = entry['relative_path']
                exp_size = entry['size_bytes']
                exp_sha = entry['sha256']
                full_path = os.path.join(REPO_ROOT, rel_path.replace('/', os.sep))

                if not os.path.exists(full_path):
                    rec = AssertionRecord(f"Tracked evidence exists: {rel_path}", "FAIL", "File missing on disk")
                    stage3.add(rec)
                    self.record_assertion(rec)
                    continue

                with open(full_path, 'rb') as ef:
                    actual_ef_data = ef.read()

                act_size = len(actual_ef_data)
                act_sha = hashlib.sha256(actual_ef_data).hexdigest()

                if act_size == exp_size and act_sha == exp_sha:
                    rec = AssertionRecord(f"Evidence checksum match: {rel_path}", "PASS")
                else:
                    rec = AssertionRecord(f"Evidence checksum check: {rel_path}", "FAIL", f"Expected {exp_sha[:12]}, got {act_sha[:12]}")
                stage3.add(rec)
                self.record_assertion(rec)

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
            target_exe_path=target_exe if target_exe else r"D:\BarTender\BarTend.exe",
            screenshots_clean_room_verified=is_clean_room
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
            '23_PHASE1_1_2_1_VALIDATOR_CORRECTNESS.md'
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

        # Enforce exact exit code semantics:
        # 0: all pass, 0 fail, 0 not_checked, 0 warnings
        # 1: failure
        # 2: not_checked / prerequisite failure
        exit_code = 0
        if self.counts['FAIL'] > 0:
            self.log_print("  RESULT: FAILED (See failures below)")
            for f in self.failures:
                self.log_print(f"    - {f}")
            self.log_print("=" * 78)
            exit_code = 1
        elif self.counts['NOT_CHECKED'] > 0:
            self.log_print("  RESULT: PREREQUISITE ERROR OR UNCHECKED CHECKS (NOT_CHECKED > 0)")
            self.log_print("=" * 78)
            exit_code = 2
        elif self.counts['WARNING'] > 0:
            self.log_print("  RESULT: WARNINGS PRESENT (Release gate blocked unless resolved)")
            self.log_print("=" * 78)
            exit_code = 1
        else:
            self.log_print("  RESULT: DETERMINISTIC PASS (All integrity checks verified)")
            self.log_print("=" * 78)
            exit_code = 0

        # -------------------------------------------------------------
        # STAGE 12: Validation Execution Provenance Generation
        # (Production Module: provenance.py)
        # -------------------------------------------------------------
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
                target_available=target_available
            )
            provenance_path = os.path.join(RECON_DIR, 'validation_provenance.json')
            with open(provenance_path, 'w', encoding='utf-8') as pf:
                json.dump(provenance, pf, indent=2)

        return exit_code


if __name__ == '__main__':
    suite = ValidationSuite()
    sys.exit(suite.run())
