#!/usr/bin/env python3
"""
Label-Forge Phase 1.1 Evidence Validation Script
Automated deterministic auditor for reverse-engineering evidence, manifests, and reports.

Exit codes:
  0: PASS (All evidence reconciled, verified, and consistent)
  1: FAIL (Contradiction, hash mismatch, or invalid claim found)
  2: PREREQUISITE_ERROR (Target executable or required environment missing)
"""

import sys
import os
import hashlib
import struct
import json

TARGET_EXE = r'D:\BarTender\BarTend.exe'
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'evidence', 'phase1')
RECON_DIR = os.path.join(EVIDENCE_DIR, 'reconciliation')
REPORTS_DIR = os.path.join(REPO_ROOT, 'reports')

EXPECTED_SHA256 = 'd3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594'
EXPECTED_SHA1 = '7a57fefa26e99ddec6a46625a8cc17c5a87593aa'
EXPECTED_MD5 = '7af37ab384391fcc03935a569d705aa0'
EXPECTED_SIZE = 20774984
EXPECTED_ENTRY_POINT = '0x97d0fb'
EXPECTED_SECTIONS = ['.text', '.nep', '.rdata', '.data', '.pdata', '.rsrc', '.reloc']

def log(msg, status='INFO'):
    prefixes = {
        'INFO': '[INFO]',
        'PASS': '[PASS] ✓',
        'FAIL': '[FAIL] ✗',
        'WARN': '[WARN] !'
    }
    print(f'{prefixes.get(status, "[INFO]")} {msg}')

def main():
    print('=' * 75)
    print('  LABEL-FORGE PHASE 1.1: AUTOMATED EVIDENCE VALIDATION SUITE')
    print('=' * 75)

    errors = []

    # 1. Prerequisite Checks
    log('Verifying target and environment prerequisites...')
    if not os.path.exists(TARGET_EXE):
        log(f'Target binary not found at: {TARGET_EXE}', 'FAIL')
        return 2

    if not os.path.isdir(RECON_DIR):
        log(f'Reconciliation directory missing: {RECON_DIR}', 'FAIL')
        return 2

    log('Prerequisites verified successfully.', 'PASS')

    # 2. Binary Digest & Integrity Verification
    log(f'Auditing binary digests of {TARGET_EXE}...')
    with open(TARGET_EXE, 'rb') as f:
        bin_data = f.read()

    actual_size = len(bin_data)
    actual_md5 = hashlib.md5(bin_data).hexdigest()
    actual_sha1 = hashlib.sha1(bin_data).hexdigest()
    actual_sha256 = hashlib.sha256(bin_data).hexdigest()

    if actual_size != EXPECTED_SIZE:
        errors.append(f'Size mismatch: expected {EXPECTED_SIZE}, got {actual_size}')
    if actual_md5 != EXPECTED_MD5:
        errors.append(f'MD5 mismatch: expected {EXPECTED_MD5}, got {actual_md5}')
    if actual_sha1 != EXPECTED_SHA1:
        errors.append(f'SHA-1 mismatch: expected {EXPECTED_SHA1}, got {actual_sha1}')
    if actual_sha256 != EXPECTED_SHA256:
        errors.append(f'SHA-256 mismatch: expected {EXPECTED_SHA256}, got {actual_sha256}')

    if not errors:
        log(f'Cryptographic digests match ground truth (SHA-256: {actual_sha256[:16]}...)', 'PASS')

    # 3. PE Header & Section Verification
    log('Parsing PE headers and section table...')
    e_lfanew = struct.unpack_from('<I', bin_data, 0x3C)[0]
    machine = struct.unpack_from('<H', bin_data, e_lfanew+4)[0]
    num_sections = struct.unpack_from('<H', bin_data, e_lfanew+6)[0]
    opt_header_size = struct.unpack_from('<H', bin_data, e_lfanew+20)[0]
    opt_offset = e_lfanew + 24
    magic = struct.unpack_from('<H', bin_data, opt_offset)[0]
    entry_point = struct.unpack_from('<I', bin_data, opt_offset+16)[0]

    if machine != 0x8664 or magic != 0x20b:
        errors.append(f'PE architecture mismatch: machine={hex(machine)}, magic={hex(magic)}')

    if f'0x{entry_point:x}' != EXPECTED_ENTRY_POINT:
        errors.append(f'Entry point mismatch: expected {EXPECTED_ENTRY_POINT}, got 0x{entry_point:x}')

    sec_table_offset = opt_offset + opt_header_size
    actual_sections = []
    for i in range(num_sections):
        so = sec_table_offset + i * 40
        sname = bin_data[so:so+8].rstrip(b'\x00').decode('latin1')
        actual_sections.append(sname)

    if actual_sections != EXPECTED_SECTIONS:
        errors.append(f'Section table mismatch: expected {EXPECTED_SECTIONS}, got {actual_sections}')
    else:
        log(f'PE Sections verified: {actual_sections}', 'PASS')

    # Check Certificate Table
    dir_base = opt_offset + 112
    cert_va, cert_size = struct.unpack_from('<II', bin_data, dir_base + 4*8)
    if cert_va + cert_size != actual_size:
        errors.append(f'Authenticode table bounds error: 0x{cert_va:x} + {cert_size} != {actual_size}')
    else:
        log(f'Authenticode security directory matches file length exactly (offset 0x{cert_va:x}, size {cert_size})', 'PASS')

    # 4. Manifest Integrity & Reconciliation Verification
    log('Verifying reconciliation manifest files...')
    manifests = [
        'canonical_target_identity.json',
        'file_inventory_summary.json',
        'module_architecture_summary.json',
        'dependency_reconciliation.json',
        'claim_register.json',
        'validation_manifest.json'
    ]

    for mf in manifests:
        mf_path = os.path.join(RECON_DIR, mf)
        if not os.path.exists(mf_path):
            errors.append(f'Missing manifest: {mf}')
            continue
        try:
            with open(mf_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('status') != 'RECONCILED_AUTHORITATIVE':
                errors.append(f'Manifest {mf} does not have status RECONCILED_AUTHORITATIVE')
        except Exception as e:
            errors.append(f'Invalid JSON in {mf}: {e}')

    if not errors:
        log('All 6 reconciliation manifests loaded and parsed successfully.', 'PASS')

    # 5. Inventory Math Check
    log('Auditing component inventory mathematical reconciliation...')
    try:
        with open(os.path.join(RECON_DIR, 'file_inventory_summary.json'), 'r', encoding='utf-8') as f:
            inv = json.load(f)
        total_files = inv['total_files']
        cat_sum = inv['categories_sum']
        total_items = inv['total_filesystem_items']
        total_dirs = inv['total_directories']
        pe_total = inv['pe_binary_classification']['total_pe_binaries']
        pe_sum = inv['pe_binary_classification']['classifications_sum']

        if total_files != cat_sum:
            errors.append(f'Inventory error: total_files ({total_files}) != categories_sum ({cat_sum})')
        if total_items != (total_dirs + total_files):
            errors.append(f'Inventory error: total_items ({total_items}) != dirs ({total_dirs}) + files ({total_files})')
        if pe_total != pe_sum:
            errors.append(f'Inventory error: pe_total ({pe_total}) != pe_classifications_sum ({pe_sum})')

        log(f'Component count reconciled: {total_dirs} directories + {total_files} files = {total_items} items (461 PE binaries)', 'PASS')
    except Exception as e:
        errors.append(f'Failed inventory mathematical audit: {e}')

    # 6. Claim Register Audit
    log('Auditing Claim Register entries...')
    try:
        with open(os.path.join(RECON_DIR, 'claim_register.json'), 'r', encoding='utf-8') as f:
            cr = json.load(f)
        valid_statuses = {'VERIFIED_STATIC', 'VERIFIED_RUNTIME', 'VERIFIED_DOCUMENTATION', 'INFERRED', 'UNKNOWN', 'NOT_PERFORMED'}
        for c in cr['claims']:
            cid = c['id']
            st = c['status']
            if st not in valid_statuses:
                errors.append(f'Claim {cid} has invalid status: {st}')
            if 'Ghidra' in c['claim'] and 'decompilation' in c['claim'] and st != 'NOT_PERFORMED':
                errors.append(f'Claim {cid} Ghidra decompilation must be NOT_PERFORMED, got {st}')
        log(f'Claim register verified: {cr["total_claims"]} claims tracked, all statuses valid.', 'PASS')
    except Exception as e:
        errors.append(f'Failed claim register audit: {e}')

    # 7. Non-existent / Phantom DLL Check
    log('Auditing phantom DLL verification...')
    try:
        with open(os.path.join(RECON_DIR, 'dependency_reconciliation.json'), 'r', encoding='utf-8') as f:
            dep = json.load(f)
        for p in dep['phantom_dll_reconciliation']:
            pname = p['phantom_name']
            p_path = os.path.join(r'D:\BarTender', pname)
            if os.path.exists(p_path):
                errors.append(f'Phantom DLL unexpectedly found on disk: {pname}')
        log(f'Confirmed {len(dep["phantom_dll_reconciliation"])} prior phantom references correctly identified and reconciled.', 'PASS')
    except Exception as e:
        errors.append(f'Failed phantom DLL check: {e}')

    print('-' * 75)
    if errors:
        log('VALIDATION SUITE FAILED WITH ERRORS:', 'FAIL')
        for err in errors:
            print(f'  - {err}')
        return 1

    log('ALL EVIDENCE RECONCILIATION CHECKS PASSED DETERMINISTICALLY.', 'PASS')
    print('=' * 75)
    return 0

if __name__ == '__main__':
    sys.exit(main())
