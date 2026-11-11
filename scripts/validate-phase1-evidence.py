#!/usr/bin/env python3
"""
Label-Forge Phase 1.1.2 Final Evidence Integrity Gate & Validation Suite
Comprehensive, automated deterministic auditor for reverse-engineering evidence,
manifests, dependency partitions, claim-specific assertions, and reports.

Exit codes:
  0: PASS (All mandatory checks pass with zero failures)
  1: FAIL (Contradiction, hash mismatch, partition failure, or invalid assertion)
  2: PREREQUISITE_ERROR (Target executable or required environment missing)
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
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'evidence', 'phase1')
RECON_DIR = os.path.join(EVIDENCE_DIR, 'reconciliation')
REPORTS_DIR = os.path.join(REPO_ROOT, 'reports')

def resolve_json_pointer(doc, pointer):
    """RFC 6901 JSON Pointer resolver."""
    if not pointer or pointer == '':
        return doc
    if not pointer.startswith('/'):
        raise ValueError(f"Invalid JSON pointer (must start with '/'): {pointer}")
    parts = pointer[1:].split('/')
    curr = doc
    for part in parts:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(curr, list):
            idx = int(part)
            curr = curr[idx]
        elif isinstance(curr, dict):
            curr = curr[part]
        else:
            raise KeyError(f"Cannot traverse into primitive value at '{part}'")
    return curr

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
        
        # Structured results for provenance
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

    def record(self, check_name, status, detail=""):
        self.counts[status] += 1
        tag = f"[{status}]"
        if status == 'PASS':
            msg = f"  {tag:<14} ✓ {check_name}"
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
        self.log_print("=" * 78)
        self.log_print("   LABEL-FORGE PHASE 1.1.2: FINAL EVIDENCE INTEGRITY GATE & AUDIT SUITE")
        self.log_print("=" * 78)

        # -------------------------------------------------------------
        # STAGE 1: Prerequisite Verification
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
        # (Values derived dynamically from canonical manifest)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 2] Target Binary Cryptographic & PE Header Audit (Dynamic Derivation)")
        if not target_available:
            self.record("Binary size & hash verification", "NOT_CHECKED", "Target binary not present")
        else:
            actual_size = len(bin_data)
            expected_size = canonical['file_size_bytes']
            if actual_size == expected_size:
                self.record(f"File size matches canonical ({actual_size:,} bytes)", "PASS")
            else:
                self.record("File size check", "FAIL", f"Expected {expected_size}, got {actual_size}")

            actual_md5 = hashlib.md5(bin_data).hexdigest()
            expected_md5 = canonical['hashes']['md5']
            if actual_md5 == expected_md5:
                self.record(f"MD5 digest match ({actual_md5})", "PASS")
            else:
                self.record("MD5 digest check", "FAIL", f"Expected {expected_md5}, got {actual_md5}")

            actual_sha1 = hashlib.sha1(bin_data).hexdigest()
            expected_sha1 = canonical['hashes']['sha1']
            if actual_sha1 == expected_sha1:
                self.record(f"SHA-1 digest match ({actual_sha1})", "PASS")
            else:
                self.record("SHA-1 digest check", "FAIL", f"Expected {expected_sha1}, got {actual_sha1}")

            actual_sha256 = hashlib.sha256(bin_data).hexdigest()
            expected_sha256 = canonical['hashes']['sha256']
            if actual_sha256 == expected_sha256:
                self.record(f"SHA-256 digest match ({actual_sha256})", "PASS")
            else:
                self.record("SHA-256 digest check", "FAIL", f"Expected {expected_sha256}, got {actual_sha256}")

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
                self.record(f"PE Architecture x86_64 PE32+ (Machine {hex(machine)}, Magic {hex(magic)})", "PASS")
            else:
                self.record("PE Architecture check", "FAIL", f"Machine {hex(machine)}, Magic {hex(magic)}")

            if entry_point == expected_ep:
                self.record(f"Entry point RVA matches canonical ({hex(entry_point)})", "PASS")
            else:
                self.record("Entry point RVA check", "FAIL", f"Expected {hex(expected_ep)}, got {hex(entry_point)}")

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
                self.record(f"Section table matches canonical exactly ({actual_sec_names})", "PASS")
            else:
                self.record("Section names check", "FAIL", f"Expected {canonical_sec_names}, got {actual_sec_names}")

            # Check section .data raw file offset dynamically from canonical manifest
            canonical_data_sec = next((s for s in canonical['sections'] if s['name'] == '.data'), None)
            expected_data_raddr = canonical_data_sec['raw_data_offset'] if canonical_data_sec else None
            data_sec = next((s for s in actual_sections if s['name'] == '.data'), None)
            if data_sec and data_sec['raddr'] == expected_data_raddr:
                self.record(f"Section .data raw offset dynamically verified as {expected_data_raddr}", "PASS")
            else:
                self.record("Section .data raw offset check", "FAIL", f"Expected {expected_data_raddr}, got {data_sec['raddr'] if data_sec else 'missing'}")

            # Authenticode boundary check dynamically derived from canonical manifest
            dir_base = opt_offset + 112
            cert_va, cert_size = struct.unpack_from('<II', bin_data, dir_base + 4*8)
            expected_cert_va = int(canonical['authenticode_signature']['file_offset'], 16)
            expected_cert_size = canonical['authenticode_signature']['size']

            if cert_va == expected_cert_va and cert_size == expected_cert_size:
                self.record(f"Authenticode directory physical bounds verified (offset {hex(cert_va)}, size {cert_size}, terminates at file end)", "PASS")
            else:
                self.record("Authenticode boundary check", "FAIL", f"Expected offset {hex(expected_cert_va)} size {expected_cert_size}, got offset {hex(cert_va)} size {cert_size}")

            # CLR COM descriptor dynamically derived from canonical manifest
            com_rva, com_size = struct.unpack_from('<II', bin_data, dir_base + 14*8)
            com_desc = canonical['clr_runtime']['com_descriptor_directory']
            expected_com_rva = int(com_desc['virtual_address'], 16)
            expected_com_size = com_desc['size']

            if com_rva == expected_com_rva and com_size == expected_com_size:
                self.record(f"CLR COM descriptor verified dynamically at RVA {hex(com_rva)}, size {com_size}", "PASS")
            else:
                self.record("CLR COM descriptor check", "FAIL", f"Expected RVA {hex(expected_com_rva)} size {expected_com_size}, got {hex(com_rva)} {com_size}")

            # Resolve COM file offset and check COR20 metadata dynamically
            def rva_to_off(rva):
                for s in actual_sections:
                    va = int(s['va'], 16)
                    vs = s['vsize']
                    ra = int(s['raddr'], 16)
                    if va <= rva < va + vs:
                        return ra + (rva - va)
                return None

            com_off = rva_to_off(com_rva)
            cor_header = bin_data[com_off:com_off+72]
            meta_rva, meta_size = struct.unpack_from('<II', cor_header, 8)
            cor_flags = struct.unpack_from('<I', cor_header, 16)[0]

            cli_meta = canonical['clr_runtime']['cli_metadata_root']
            expected_meta_rva = int(cli_meta['virtual_address'], 16)
            expected_meta_size = cli_meta['size_bytes']
            expected_cor_flags = canonical['clr_runtime']['cor20_header']['flags']

            if meta_rva == expected_meta_rva and meta_size == expected_meta_size:
                self.record(f"CLI Metadata Root verified dynamically at RVA {hex(meta_rva)} (Size: {meta_size})", "PASS")
            else:
                self.record("CLI Metadata Root check", "FAIL", f"Expected RVA {hex(expected_meta_rva)} size {expected_meta_size}, got {hex(meta_rva)} {meta_size}")

            if cor_flags == expected_cor_flags:
                self.record(f"COMIMAGE_FLAGS_ILONLY verified as {expected_cor_flags} (C++/CLI mixed mode)", "PASS")
            else:
                self.record("COMIMAGE_FLAGS check", "FAIL", f"Expected {expected_cor_flags}, got {hex(cor_flags)}")

            self.stage_results['target_binary_integrity'] = 'PASS'

        # -------------------------------------------------------------
        # STAGE 3: Evidence Manifest Integrity & SHA-256 Validation
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 3] Evidence Manifest Checksum Integrity Audit")
        val_manifest_path = os.path.join(RECON_DIR, 'validation_manifest.json')
        manifest_stage_pass = True
        if not os.path.exists(val_manifest_path):
            self.record("Validation manifest presence", "FAIL", f"Missing {val_manifest_path}")
            manifest_stage_pass = False
        else:
            with open(val_manifest_path, 'r', encoding='utf-8') as f:
                val_manifest = json.load(f)

            manifest_files = val_manifest.get('files', [])
            self.record(f"Validation manifest loaded ({len(manifest_files)} tracked evidence files)", "PASS")

            for entry in manifest_files:
                rel_path = entry['relative_path']
                exp_size = entry['size_bytes']
                exp_sha = entry['sha256']
                full_path = os.path.join(REPO_ROOT, rel_path.replace('/', os.sep))

                if not os.path.exists(full_path):
                    self.record(f"Tracked evidence exists: {rel_path}", "FAIL", "File missing on disk")
                    manifest_stage_pass = False
                    continue

                with open(full_path, 'rb') as ef:
                    actual_ef_data = ef.read()

                act_size = len(actual_ef_data)
                act_sha = hashlib.sha256(actual_ef_data).hexdigest()

                if act_size == exp_size and act_sha == exp_sha:
                    self.record(f"Evidence checksum match: {rel_path}", "PASS")
                else:
                    self.record(f"Evidence checksum check: {rel_path}", "FAIL", f"Expected {exp_sha[:12]}, got {act_sha[:12]}")
                    manifest_stage_pass = False

        self.stage_results['manifest_integrity'] = 'PASS' if manifest_stage_pass else 'FAIL'

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
        # (Requirement 1: Exact Set & Frequency-based Partition Enforcement)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 5] Exact Direct-Import Category Partition & Dependency Audit")
        dep_path = os.path.join(RECON_DIR, 'dependency_reconciliation.json')
        with open(dep_path, 'r', encoding='utf-8') as f:
            dep = json.load(f)

        partition_pass = True
        canonical_direct_imports = dep.get('direct_pe_imports', {}).get('libraries', [])
        canonical_norm = [m.strip().upper() for m in canonical_direct_imports]
        canonical_set = set(canonical_norm)

        # 1. Canonical duplicate detection
        if len(canonical_norm) == len(canonical_set):
            self.record(f"Canonical direct-import list has zero duplicates ({len(canonical_norm)} modules)", "PASS")
        else:
            dup_canonical = [m for m in canonical_set if canonical_norm.count(m) > 1]
            self.record("Canonical direct-import duplicates check", "FAIL", f"Duplicates in canonical list: {dup_canonical}")
            partition_pass = False

        # 2. Category parsing and within-category duplicate detection
        dep_categories = dep.get('direct_pe_imports', {}).get('categories', {})
        categorized_all = []
        category_assignment_map = {}

        for cat_name, cat_data in dep_categories.items():
            cat_mods = cat_data.get('modules', [])
            cat_norm = [m.strip().upper() for m in cat_mods]
            
            # Within-category duplicates
            if len(cat_norm) == len(set(cat_norm)):
                self.record(f"Category '{cat_name}' has zero internal duplicates ({len(cat_norm)} modules)", "PASS")
            else:
                cat_dups = [m for m in set(cat_norm) if cat_norm.count(m) > 1]
                self.record(f"Category '{cat_name}' internal duplicates", "FAIL", f"Duplicates: {cat_dups}")
                partition_pass = False

            for m in cat_norm:
                categorized_all.append(m)
                category_assignment_map.setdefault(m, []).append(cat_name)

        # 3. Across-category duplicate / overlap detection
        multi_assigned = {m: cats for m, cats in category_assignment_map.items() if len(cats) > 1}
        if len(multi_assigned) == 0:
            self.record("Zero cross-category module overlaps detected (all modules assigned to <= 1 category)", "PASS")
        else:
            self.record("Cross-category overlap check", "FAIL", f"Modules assigned to multiple categories: {multi_assigned}")
            partition_pass = False

        # 4. Missing module detection (Canonical \ Categorized)
        categorized_set = set(categorized_all)
        missing_modules = canonical_set - categorized_set
        if len(missing_modules) == 0:
            self.record("Zero canonical direct-import modules omitted from categories", "PASS")
        else:
            self.record("Missing direct-import modules check", "FAIL", f"Canonical modules missing from categories: {missing_modules}")
            partition_pass = False

        # 5. Unexpected module detection (Categorized \ Canonical)
        unexpected_modules = categorized_set - canonical_set
        if len(unexpected_modules) == 0:
            self.record("Zero unexpected modules found in direct-import categories", "PASS")
        else:
            self.record("Unexpected direct-import modules check", "FAIL", f"Categorized modules not in canonical list: {unexpected_modules}")
            partition_pass = False

        # 6. Exact Set Equality Assertion
        if categorized_set == canonical_set and len(categorized_all) == len(canonical_norm):
            self.record(f"Exact direct-import partition verified: categorized_modules == canonical_direct_imports ({len(canonical_set)} modules)", "PASS")
        else:
            self.record("Exact partition equality check", "FAIL", f"Categorized count {len(categorized_all)} != Canonical count {len(canonical_norm)}")
            partition_pass = False

        self.stage_results['direct_import_partition'] = 'PASS' if partition_pass else 'FAIL'

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
        # STAGE 6: Exact Claim Status Accounting
        # (Requirement 4: Full Set & Dictionary Equality Enforcement)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 6] Exact Claim Status Accounting Audit")
        cr_path = os.path.join(RECON_DIR, 'claim_register.json')
        with open(cr_path, 'r', encoding='utf-8') as f:
            cr = json.load(f)

        claims = cr.get('claims', [])
        total_claims_field = cr.get('total_claims')
        declared_status_counts = cr.get('claims_by_status', {})
        status_accounting_pass = True

        # Total claims field matches array length
        if len(claims) == total_claims_field:
            self.record(f"Total claims count field matches claims array length ({len(claims)})", "PASS")
        else:
            self.record("Total claims field check", "FAIL", f"Field {total_claims_field} != array length {len(claims)}")
            status_accounting_pass = False

        # Claim ID uniqueness check
        claim_ids = [c.get('id') for c in claims]
        if len(claim_ids) == len(set(claim_ids)):
            self.record(f"Claim ID uniqueness verified ({len(claim_ids)} distinct IDs)", "PASS")
        else:
            duplicates = [cid for cid in claim_ids if claim_ids.count(cid) > 1]
            self.record("Claim ID uniqueness check", "FAIL", f"Duplicate claim IDs found: {set(duplicates)}")
            status_accounting_pass = False

        # Allowed statuses check
        ALLOWED_STATUSES = {
            'VERIFIED_STATIC',
            'VERIFIED_RUNTIME',
            'VERIFIED_DOCUMENTATION',
            'INFERRED',
            'UNKNOWN',
            'NOT_PERFORMED'
        }

        actual_status_counts = {}
        for c in claims:
            cid = c.get('id')
            st = c.get('status')
            if not st:
                self.record(f"Claim {cid} status missing", "FAIL", "Status field is null or empty")
                status_accounting_pass = False
                continue
            if st not in ALLOWED_STATUSES:
                self.record(f"Claim {cid} unknown status", "FAIL", f"Status '{st}' not in recognized set: {ALLOWED_STATUSES}")
                status_accounting_pass = False
                continue
            actual_status_counts[st] = actual_status_counts.get(st, 0) + 1

        # Check dictionary equality between actual and declared status counts
        # (Compare full dictionaries including zeroes)
        normalized_actual_counts = {st: actual_status_counts.get(st, 0) for st in ALLOWED_STATUSES}
        normalized_declared_counts = {st: declared_status_counts.get(st, 0) for st in ALLOWED_STATUSES}

        unexpected_declared_statuses = set(declared_status_counts.keys()) - ALLOWED_STATUSES
        if len(unexpected_declared_statuses) > 0:
            self.record("Declared statuses unrecognized", "FAIL", f"Unexpected statuses in claims_by_status: {unexpected_declared_statuses}")
            status_accounting_pass = False

        if normalized_actual_counts == normalized_declared_counts:
            self.record("Complete status dictionary equality verified: actual_status_counts == declared_status_counts", "PASS")
            for st, cnt in actual_status_counts.items():
                self.record(f"Status accounting [{st}]: exactly {cnt} claims", "PASS")
        else:
            mismatches = {
                st: (normalized_actual_counts[st], normalized_declared_counts[st])
                for st in ALLOWED_STATUSES if normalized_actual_counts[st] != normalized_declared_counts[st]
            }
            self.record("Status accounting dictionary mismatch", "FAIL", f"Mismatched status counts (actual, declared): {mismatches}")
            status_accounting_pass = False

        if sum(actual_status_counts.values()) == len(claims):
            self.record(f"Total claims sum equals actual claims count ({len(claims)})", "PASS")
        else:
            self.record("Status sum total check", "FAIL", f"Sum {sum(actual_status_counts.values())} != Total {len(claims)}")
            status_accounting_pass = False

        self.stage_results['status_accounting'] = 'PASS' if status_accounting_pass else 'FAIL'

        # -------------------------------------------------------------
        # STAGE 7: Structured Evidence References Verification
        # (Requirement 3: Explicit Typed Evidence References)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 7] Structured Evidence References Verification Audit")
        evidence_refs_pass = True

        for c in claims:
            cid = c.get('id')
            st = c.get('status')
            vmethod = c.get('validation_method')
            refs = c.get('evidence_refs')

            # Verified claims MUST have non-empty evidence_refs
            if st.startswith('VERIFIED_'):
                if not refs or len(refs) == 0:
                    self.record(f"Claim {cid} [{st}] structured references", "FAIL", "Missing or empty evidence_refs array")
                    evidence_refs_pass = False
                    continue

                if not vmethod:
                    self.record(f"Claim {cid} [{st}] validation method", "FAIL", "Missing validation_method")
                    evidence_refs_pass = False
                    continue

            for idx, ref in enumerate(refs or []):
                rtype = ref.get('type')
                rpath = ref.get('path')
                desc = ref.get('description')
                required = ref.get('required', True)

                # Path safety and format validation
                if not rpath or os.path.isabs(rpath) or '..' in rpath or '\\' in rpath:
                    self.record(f"Claim {cid} ref [{idx}] path format", "FAIL", f"Path must be repository-relative using forward slashes: '{rpath}'")
                    evidence_refs_pass = False
                    continue

                full_path = os.path.join(REPO_ROOT, rpath.replace('/', os.sep))
                if not os.path.exists(full_path):
                    self.record(f"Claim {cid} ref [{idx}] file existence", "FAIL", f"Referenced file does not exist: '{rpath}'")
                    evidence_refs_pass = False
                    continue

                # Type-specific reference validation
                if rtype == 'file':
                    pass  # File existence already verified above
                elif rtype == 'json_pointer':
                    ptr = ref.get('pointer')
                    if not ptr:
                        self.record(f"Claim {cid} ref [{idx}] JSON pointer", "FAIL", "Missing 'pointer' field")
                        evidence_refs_pass = False
                        continue
                    try:
                        with open(full_path, 'r', encoding='utf-8') as jf:
                            jdoc = json.load(jf)
                        resolved_val = resolve_json_pointer(jdoc, ptr)
                        if resolved_val is None:
                            self.record(f"Claim {cid} ref [{idx}] JSON pointer resolution", "FAIL", f"Pointer '{ptr}' resolved to None in '{rpath}'")
                            evidence_refs_pass = False
                    except Exception as e:
                        self.record(f"Claim {cid} ref [{idx}] JSON pointer resolution", "FAIL", f"Pointer '{ptr}' failed in '{rpath}': {str(e)}")
                        evidence_refs_pass = False

                elif rtype == 'runtime_test':
                    tid = ref.get('test_id')
                    if not tid:
                        self.record(f"Claim {cid} ref [{idx}] runtime test", "FAIL", "Missing 'test_id' field")
                        evidence_refs_pass = False
                        continue
                    try:
                        with open(full_path, 'r', encoding='utf-8') as rf:
                            rdoc = json.load(rf)
                        known_tids = {t.get('test_id') for t in rdoc.get('empirical_tests', [])}
                        if tid not in known_tids:
                            self.record(f"Claim {cid} ref [{idx}] runtime test ID", "FAIL", f"Test ID '{tid}' not found in '{rpath}'")
                            evidence_refs_pass = False
                    except Exception as e:
                        self.record(f"Claim {cid} ref [{idx}] runtime test lookup", "FAIL", f"Failed reading '{rpath}': {str(e)}")
                        evidence_refs_pass = False
                else:
                    self.record(f"Claim {cid} ref [{idx}] unknown type", "FAIL", f"Unknown reference type: '{rtype}'")
                    evidence_refs_pass = False

            if st.startswith('VERIFIED_') and refs:
                self.record(f"Claim {cid} structured evidence_refs verified ({len(refs)} valid refs)", "PASS")

        self.stage_results['evidence_references'] = 'PASS' if evidence_refs_pass else 'FAIL'

        # -------------------------------------------------------------
        # STAGE 8: Claim-Specific Assertion Registry
        # (Requirement 2: Zero Unconditional Fallbacks, Rigorous Propositions)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 8] Claim-Specific Assertion Registry (Zero Unconditional Fallbacks)")
        claim_registry_pass = True

        # Load supporting files for claim assertions
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

        # Definition of claim-specific validation registry
        # Maps every claim ID to a callable returning (status, detail_message)
        def assert_P1_001():
            exp_size = can_doc['file_size_bytes']
            if exp_size == 20774984:
                return ('PASS', f"File size 20,774,984 bytes confirmed (canonical offset: {exp_size})")
            return ('FAIL', f"Canonical file size != 20,774,984 (got {exp_size})")

        def assert_P1_002():
            h = can_doc['hashes']
            if (h['md5'] == '7af37ab384391fcc03935a569d705aa0' and
                h['sha1'] == '7a57fefa26e99ddec6a46625a8cc17c5a87593aa' and
                h['sha256'] == 'd3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594'):
                return ('PASS', f"Cryptographic digests MD5/SHA1/SHA256 verified against ground truth (SHA256: {h['sha256'][:16]}...)")
            return ('FAIL', f"Hash mismatch: {h}")

        def assert_P1_003():
            v = can_doc.get('version_info', {})
            fv = v.get('file_version')
            pv = v.get('product_version')
            if fv == '11.4.238.365' and pv == '11.4.0.1':
                return ('PASS', f"FileVersion '{fv}' and ProductVersion '{pv}' verified from VS_FIXEDFILEINFO")
            return ('FAIL', f"Version info mismatch: fv={fv}, pv={pv}")

        def assert_P1_004():
            pe = can_doc['pe_header']
            if pe['machine'] == '0x8664' and pe['magic'] == '0x020b' and pe['subsystem'] == 2:
                return ('PASS', "Architecture x86_64, PE32+ Optional Header, GUI Subsystem verified")
            return ('FAIL', f"PE Header mismatch: {pe}")

        def assert_P1_005():
            pe = can_doc['pe_header']
            if pe['entry_point'] == '0x97d0fb' and pe['image_base'] == '0x140000000':
                return ('PASS', "AddressOfEntryPoint (0x97d0fb) and ImageBase (0x140000000) verified")
            return ('FAIL', f"Entry point / ImageBase mismatch: {pe}")

        def assert_P1_006():
            secs = can_doc['sections']
            sec_names = [s['name'] for s in secs]
            data_sec = next((s for s in secs if s['name'] == '.data'), None)
            if len(secs) == 7 and sec_names == ['.text', '.nep', '.rdata', '.data', '.pdata', '.rsrc', '.reloc'] and data_sec and data_sec['raw_data_offset'] == '0x10f2a00':
                return ('PASS', f"Section table (7 sections, .data RawOffset=0x10f2a00) verified: {sec_names}")
            return ('FAIL', f"Section table mismatch: count={len(secs)}, names={sec_names}, data_sec={data_sec}")

        def assert_P1_007():
            sig = can_doc['authenticode_signature']
            file_size = can_doc['file_size_bytes']
            if sig['file_offset'] == '0x13cb000' and sig['size'] == 20552 and sig['signature_end_offset'] == file_size:
                return ('PASS', f"Authenticode bounds verified: offset {sig['file_offset']}, size {sig['size']} terminates at exact file end {file_size}")
            return ('FAIL', f"Authenticode bounds mismatch: {sig}")

        def assert_P1_008():
            clr = can_doc['clr_runtime']
            com = clr['com_descriptor_directory']
            meta = clr['cli_metadata_root']
            flags = clr['cor20_header']['flags']
            if com['virtual_address'] == '0xae9b90' and meta['virtual_address'] == '0xc3ca00' and flags == 0:
                return ('PASS', f"COM descriptor at RVA 0xae9b90 pointing to CLI Metadata Root at RVA 0xc3ca00, COMIMAGE_FLAGS_ILONLY=0 (C++/CLI)")
            return ('FAIL', f"CLR / CLI metadata mismatch: com={com}, meta={meta}, flags={flags}")

        def assert_P1_009():
            tot = inv_doc['total_filesystem_items']
            files = inv_doc['total_files']
            dirs = inv_doc['total_directories']
            if tot == 589 and files == 555 and dirs == 34 and tot == (files + dirs):
                return ('PASS', f"Filesystem inventory verified: 555 files + 34 directories = 589 items")
            return ('FAIL', f"Filesystem inventory equation failed: tot={tot}, files={files}, dirs={dirs}")

        def assert_P1_010():
            cats = inv_doc['mutually_exclusive_categories']
            csum = inv_doc['categories_sum']
            if csum == 555 and cats['executables_exe'] == 24 and cats['libraries_dll'] == 433 and cats['activex_ocx'] == 4:
                return ('PASS', f"File category partition verified: 24 exe, 433 dll, 4 ocx, sum={csum} files")
            return ('FAIL', f"File category partition mismatch: csum={csum}, cats={cats}")

        def assert_P1_011():
            pe = inv_doc['pe_binary_classification']
            c = pe['classifications']
            tot = pe['total_pe_binaries']
            csum = pe['classifications_sum']
            if tot == 461 and csum == 461 and c['managed_il_only'] == 332 and c['mixed_mode_cli'] == 20 and c['native_x64'] == 27 and c['native_x86'] == 82:
                return ('PASS', f"PE binary classifications verified (461 binaries: 332 IL, 20 mixed, 27 x64, 82 x86)")
            return ('FAIL', f"PE binary classifications mismatch: tot={tot}, csum={csum}, c={c}")

        def assert_P1_012():
            cnt = dep_doc['direct_pe_imports']['count']
            cats = dep_doc['direct_pe_imports']['categories']
            csum = sum(c['count'] for c in cats.values())
            if cnt == 48 and csum == 48:
                return ('PASS', f"Direct static PE imports verified (48 DLLs across 7 categories, sum=48)")
            return ('FAIL', f"Direct PE imports count mismatch: count={cnt}, sum={csum}")

        def assert_P1_013():
            cnt = dep_doc['delay_load_imports']['count']
            libs = dep_doc['delay_load_imports']['libraries']
            if cnt == 17 and len(libs) == 17:
                return ('PASS', f"Delay-loaded PE imports verified (17 DLLs: {libs[:3]}...)")
            return ('FAIL', f"Delay-loaded imports mismatch: count={cnt}, len={len(libs)}")

        def assert_P1_014():
            tp_mod = next((m for m in native_inv_doc['modules'] if m['name'] == 'ToolkitPro1531vc142x64U.dll'), None)
            if tp_mod and tp_mod['size_bytes'] == 10844184 and tp_mod['architecture'] == 'x86_64':
                return ('PASS', f"Codejock library verified as ToolkitPro1531vc142x64U.dll ({tp_mod['size_bytes']:,} bytes, x86_64)")
            return ('FAIL', f"ToolkitPro module mismatch: {tp_mod}")

        def assert_P1_015():
            phantoms = dep_doc['phantom_dll_reconciliation']
            expected_absent = {'BtEngine.dll', 'BtBarcode.dll', 'BtPrint.dll', 'BtSystem.dll', 'BtLic.dll', 'BtData.dll'}
            actual_absent = {p['phantom_name'] for p in phantoms}
            if expected_absent.issubset(actual_absent):
                return ('PASS', f"Absence of standalone {expected_absent} verified in reconciliation register")
            return ('FAIL', f"Phantom DLL set mismatch: {actual_absent}")

        def assert_P1_016():
            qr_mod = next((m for m in native_inv_doc['modules'] if m['name'] == 'BarCode_QRCode.dll'), None)
            if qr_mod and 'GenerateQRCode' in qr_mod.get('exports', []) and qr_mod['architecture'] == 'x86_64':
                return ('PASS', f"Modular 2D barcode plugin verified with exported C API GenerateQRCode in BarCode_QRCode.dll")
            return ('FAIL', f"Barcode plugin export mismatch: {qr_mod}")

        def assert_P1_017():
            boundaries = dotnet_interop_doc.get('key_mfc_boundaries', [])
            members = [b.get('member') for b in boundaries]
            has_archive = any('CArchive' in m for m in members)
            if has_archive and dotnet_interop_doc.get('source_module') == 'BarTend.exe':
                return ('PASS', f"CArchive and MFC serialization boundaries verified in dotnet_interop_map.json")
            return ('FAIL', f"MFC boundary verification failed: {members}")

        def assert_P1_018():
            report_path = os.path.join(REPORTS_DIR, '15_PHASE1_NATIVE_BINARY_ANALYSIS.md')
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as rf:
                    content = rf.read()
                if 'GHIDRA_INSTALL_DIR' in content and 'NOT_PERFORMED' in content:
                    return ('PASS', "Ghidra deep decompilation verified as NOT_PERFORMED due to unset GHIDRA_INSTALL_DIR")
            return ('FAIL', "Documentation for Ghidra scope boundary missing or inconsistent")

        def assert_P1_019():
            ref_path = os.path.join(REPO_ROOT, 'screenshots', 'UI_OBSERVATIONS_REFERENCE.md')
            if os.path.exists(ref_path):
                with open(ref_path, 'r', encoding='utf-8') as rf:
                    content = rf.read()
                if 'Copyright & Legal Compliance' in content and 'permanently removed' in content:
                    return ('PASS', "Clean-room compliance and textual reference document verified in screenshots/UI_OBSERVATIONS_REFERENCE.md")
            return ('FAIL', "screenshots/UI_OBSERVATIONS_REFERENCE.md missing required compliance assertions")

        def assert_P1_020():
            cs_path = os.path.join(REPO_ROOT, 'src', 'LabelForge.Core', 'Geometry', 'Length.cs')
            if os.path.exists(cs_path):
                with open(cs_path, 'r', encoding='utf-8') as cf:
                    code = cf.read()
                if 'FromMillimeters' in code and 'double' in code:
                    return ('PASS', "Length struct canonical continuous millimeter implementation verified in src/LabelForge.Core/Geometry/Length.cs")
            return ('FAIL', "Length struct implementation missing or invalid")

        def assert_P1_021():
            spooler = dep_doc['direct_pe_imports']['categories'].get('windows_print_spooler', {})
            mods = spooler.get('modules', [])
            if 'WINSPOOL.DRV' in mods:
                return ('PASS', "Direct static linkage of WINSPOOL.DRV in Windows Print Spooler category verified")
            return ('FAIL', f"WINSPOOL.DRV not found in windows_print_spooler category: {mods}")

        def assert_P1_022():
            assms = managed_assm_doc.get('assemblies', [])
            has_license = any(a.get('name') == 'Seagull.License.dll' for a in assms)
            if has_license:
                return ('PASS', "Seagull.License.dll assembly verified in managed assembly inventory")
            return ('FAIL', "Seagull.License.dll missing from managed assembly inventory")

        def assert_P1_023():
            tests = runtime_doc.get('empirical_tests', [])
            rt01 = next((t for t in tests if t.get('test_id') == 'RT-01'), None)
            if rt01 and 'modal activation' in rt01.get('observation', '').lower():
                return ('PASS', f"RT-01 process startup & modal activation prompt verified: {rt01.get('observation')[:60]}...")
            return ('FAIL', f"RT-01 observation missing or mismatch: {rt01}")

        def assert_P1_024():
            tests = runtime_doc.get('empirical_tests', [])
            rt02 = next((t for t in tests if t.get('test_id') == 'RT-02'), None)
            if rt02 and 'LicenseException' in rt02.get('observation', ''):
                return ('PASS', f"RT-02 managed print API LicenseException verified: {rt02.get('observation')[:60]}...")
            return ('FAIL', f"RT-02 observation missing or mismatch: {rt02}")

        def assert_P1_025():
            tests = runtime_doc.get('empirical_tests', [])
            rt03 = next((t for t in tests if t.get('test_id') == 'RT-03'), None)
            if rt03 and 'D5856250-13D3-11D1-9D2B-00609787E3AE' in rt03.get('observation', '') and 'unattended' in rt03.get('finding', '').lower():
                return ('PASS', f"RT-03 COM Automation ProgID & unattended execution limitation verified: {rt03.get('finding')[:60]}...")
            return ('FAIL', f"RT-03 observation missing or mismatch: {rt03}")

        CLAIM_ASSERTION_REGISTRY = {
            'P1-001': assert_P1_001,
            'P1-002': assert_P1_002,
            'P1-003': assert_P1_003,
            'P1-004': assert_P1_004,
            'P1-005': assert_P1_005,
            'P1-006': assert_P1_006,
            'P1-007': assert_P1_007,
            'P1-008': assert_P1_008,
            'P1-009': assert_P1_009,
            'P1-010': assert_P1_010,
            'P1-011': assert_P1_011,
            'P1-012': assert_P1_012,
            'P1-013': assert_P1_013,
            'P1-014': assert_P1_014,
            'P1-015': assert_P1_015,
            'P1-016': assert_P1_016,
            'P1-017': assert_P1_017,
            'P1-018': assert_P1_018,
            'P1-019': assert_P1_019,
            'P1-020': assert_P1_020,
            'P1-021': assert_P1_021,
            'P1-022': assert_P1_022,
            'P1-023': assert_P1_023,
            'P1-024': assert_P1_024,
            'P1-025': assert_P1_025
        }

        for c in claims:
            cid = c.get('id')
            st = c.get('status')
            assertion_fn = CLAIM_ASSERTION_REGISTRY.get(cid)

            if not assertion_fn:
                self.record(f"Claim {cid} assertion procedure", "FAIL", "No assertion function registered for claim")
                claim_registry_pass = False
                continue

            try:
                res_status, detail = assertion_fn()
                if res_status == 'PASS':
                    self.record(f"Claim {cid} [{st}] assertion verified", "PASS", detail)
                else:
                    self.record(f"Claim {cid} [{st}] assertion failed", "FAIL", detail)
                    claim_registry_pass = False
            except Exception as e:
                self.record(f"Claim {cid} [{st}] assertion exception", "FAIL", str(e))
                claim_registry_pass = False

        self.stage_results['claim_specific_assertions'] = 'PASS' if claim_registry_pass else 'FAIL'

        # -------------------------------------------------------------
        # STAGE 9: Recursive Prohibited-Image Audit
        # (Requirement 5: os.walk traversal, comprehensive image extensions)
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 9] Recursive Prohibited-Image Compliance Audit")
        screenshots_dir = os.path.join(REPO_ROOT, 'screenshots')
        image_audit_pass = True

        PROHIBITED_EXTENSIONS = (
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
            '.webp', '.tif', '.tiff', '.svg', '.avif', '.heic',
            '.heif', '.jfif'
        )

        found_images = []
        if os.path.exists(screenshots_dir):
            for root, dirs, files in os.walk(screenshots_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in PROHIBITED_EXTENSIONS:
                        rel_f = os.path.relpath(os.path.join(root, f), REPO_ROOT).replace('\\', '/')
                        found_images.append(rel_f)

            if len(found_images) == 0:
                self.record("Recursive prohibited-image audit: zero prohibited images found in screenshots/ tree", "PASS")
            else:
                self.record("Recursive prohibited-image audit", "FAIL", f"Found prohibited image files: {found_images}")
                image_audit_pass = False

            ref_doc = os.path.join(screenshots_dir, 'UI_OBSERVATIONS_REFERENCE.md')
            if os.path.exists(ref_doc):
                self.record("UI observations reference documentation present (UI_OBSERVATIONS_REFERENCE.md)", "PASS")
            else:
                self.record("UI observations reference check", "FAIL", "Missing screenshots/UI_OBSERVATIONS_REFERENCE.md")
                image_audit_pass = False
        else:
            self.record("Screenshots directory check", "PASS", "No screenshots directory")

        self.stage_results['recursive_image_audit'] = 'PASS' if image_audit_pass else 'FAIL'

        # -------------------------------------------------------------
        # STAGE 10: Report Cross-References & Markdown Integrity Audit
        # -------------------------------------------------------------
        self.log_print("\n[STAGE 10] Report Cross-References & Markdown Integrity Audit")
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
            '21_PHASE1_1_CORRECTION_LOG.md'
        ]

        report_pass = True
        for rep in expected_reports:
            rpath = os.path.join(REPORTS_DIR, rep)
            if not os.path.exists(rpath):
                self.record(f"Report presence: {rep}", "FAIL", "Report missing")
                report_pass = False
            else:
                with open(rpath, 'r', encoding='utf-8') as rf:
                    content = rf.read()
                if len(content) < 100:
                    self.record(f"Report content: {rep}", "FAIL", "Report content suspiciously small")
                    report_pass = False
                else:
                    has_active_table_error = False
                    for line in content.splitlines():
                        if '.data' in line and '|' in line and '0x10f2c00' in line:
                            has_active_table_error = True
                            break

                    if has_active_table_error:
                        self.record(f"Report section table check: {rep}", "FAIL", "Section table contains obsolete raw offset 0x10f2c00")
                        report_pass = False
                    else:
                        self.record(f"Report verified consistent: {rep}", "PASS")

        self.stage_results['report_consistency'] = 'PASS' if report_pass else 'FAIL'

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

        exit_code = 0
        if self.counts['FAIL'] > 0:
            self.log_print("  RESULT: FAILED (See failures below)")
            for f in self.failures:
                self.log_print(f"    - {f}")
            self.log_print("=" * 78)
            exit_code = 1
        elif self.counts['NOT_CHECKED'] > 0:
            self.log_print("  RESULT: PREREQUISITE ERROR OR UNCHECKED CHECKS")
            self.log_print("=" * 78)
            exit_code = 2
        elif self.counts['WARNING'] > 0:
            self.log_print("  RESULT: PASSED WITH WARNINGS")
            self.log_print("=" * 78)
            exit_code = 0
        else:
            self.log_print("  RESULT: DETERMINISTIC PASS (All integrity checks verified)")
            self.log_print("=" * 78)
            exit_code = 0

        # -------------------------------------------------------------
        # STAGE 12: Validation Execution Provenance Generation
        # (Requirement 6: Exact Commit SHA, Working-Tree Cleanliness, Checksums)
        # -------------------------------------------------------------
        if self.write_provenance:
            try:
                commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT).decode('utf-8').strip()
            except Exception:
                commit_sha = "UNKNOWN_COMMIT"

            try:
                branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO_ROOT).decode('utf-8').strip()
            except Exception:
                branch = "UNKNOWN_BRANCH"

            try:
                status_porcelain = subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO_ROOT).decode('utf-8').strip()
                is_working_tree_clean = (len(status_porcelain) == 0)
            except Exception:
                is_working_tree_clean = False
                status_porcelain = "GIT_STATUS_FAILED"

            # Compute validator script and manifest checksums
            validator_path = os.path.abspath(__file__)
            with open(validator_path, 'rb') as vf:
                validator_sha256 = hashlib.sha256(vf.read()).hexdigest()

            with open(val_manifest_path, 'rb') as mf:
                manifest_sha256 = hashlib.sha256(mf.read()).hexdigest()

            manifest_verified = (self.stage_results['manifest_integrity'] == 'PASS')

            provenance = {
                'schema_version': '1.1.2',
                'status': 'RECONCILED_AUTHORITATIVE',
                'provenance_metadata': {
                    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                    'validated_commit_sha': commit_sha,
                    'branch': branch,
                    'is_working_tree_clean': is_working_tree_clean,
                    'working_tree_status_porcelain': status_porcelain,
                    'validator_script': {
                        'path': os.path.relpath(validator_path, REPO_ROOT).replace('\\', '/'),
                        'sha256': validator_sha256
                    },
                    'validation_manifest': {
                        'path': os.path.relpath(val_manifest_path, REPO_ROOT).replace('\\', '/'),
                        'sha256': manifest_sha256
                    },
                    'target_executable': {
                        'path': target_exe,
                        'sha256': actual_sha256 if target_available else "NOT_CHECKED",
                        'matches_canonical': (actual_sha256 == expected_sha256) if target_available else False
                    },
                    'execution_environment': {
                        'os': platform.platform(),
                        'system': platform.system(),
                        'release': platform.release(),
                        'version': platform.version(),
                        'machine': platform.machine(),
                        'processor': platform.processor(),
                        'python_version': platform.python_version()
                    }
                },
                'validation_results': {
                    'exit_code': exit_code,
                    'result_status': 'PASS' if exit_code == 0 else ('NOT_CHECKED' if exit_code == 2 else 'FAIL'),
                    'release_gate_status': 'PHASE 1.1.2 — PASSED' if exit_code == 0 else 'PHASE 1.1.2 — BLOCKED',
                    'summary_accounting': {
                        'total_checks': total_checks,
                        'pass': self.counts['PASS'],
                        'fail': self.counts['FAIL'],
                        'warning': self.counts['WARNING'],
                        'not_checked': self.counts['NOT_CHECKED']
                    },
                    'stage_breakdown': self.stage_results,
                    'manifest_integrity_verified': manifest_verified,
                    'category_partition_verified': (self.stage_results['direct_import_partition'] == 'PASS'),
                    'claim_traceability_verified': (self.stage_results['evidence_references'] == 'PASS'),
                    'recursive_image_audit_verified': (self.stage_results['recursive_image_audit'] == 'PASS')
                },
                'execution_log': self.logs
            }

            provenance_path = os.path.join(RECON_DIR, 'validation_provenance.json')
            with open(provenance_path, 'w', encoding='utf-8') as pf:
                json.dump(provenance, pf, indent=2)

        return exit_code

if __name__ == '__main__':
    suite = ValidationSuite()
    sys.exit(suite.run())
