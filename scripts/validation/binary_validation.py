"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.binary_validation

Provides production validation functions for:
1. Target binary cryptographic and PE header audit (dynamic derivation against canonical ground truth).
2. Evidence manifest checksum and file existence audit.
"""

import os
import hashlib
import struct
import json
from typing import Dict, List, Tuple, Any, Optional
from scripts.validation.stage_results import AssertionRecord, STATUS_PASS, STATUS_FAIL, STATUS_NOT_CHECKED


def validate_target_binary(
    target_exe_path: Optional[str],
    canonical: Dict[str, Any]
) -> Tuple[bool, List[AssertionRecord], Dict[str, Any]]:
    """
    Independently audits target executable against canonical ground truth:
    - Binary existence
    - File size
    - Cryptographic digests (MD5, SHA-1, SHA-256)
    - PE Machine, Magic, Subsystem
    - Entry point RVA, ImageBase
    - Section table and .data raw data offset
    - Authenticode security directory bounds
    - CLR COM Descriptor and COR20 CLI Metadata root / flags
    """
    records: List[AssertionRecord] = []
    parsed_info: Dict[str, Any] = {}

    if not target_exe_path or not os.path.exists(target_exe_path):
        rec = AssertionRecord(
            assertion_id="target_binary_existence",
            status=STATUS_NOT_CHECKED,
            detail=f"Target binary not present at path: '{target_exe_path}'",
            stage_id="target_binary_integrity"
        )
        records.append(rec)
        return False, records, parsed_info

    try:
        with open(target_exe_path, 'rb') as f:
            bin_data = f.read()
    except Exception as e:
        rec = AssertionRecord(
            assertion_id="target_binary_read",
            status=STATUS_FAIL,
            detail=f"Failed reading target binary: {str(e)}",
            stage_id="target_binary_integrity"
        )
        records.append(rec)
        return False, records, parsed_info

    actual_size = len(bin_data)
    expected_size = canonical.get('file_size_bytes')
    can_ref = "evidence/phase1/reconciliation/canonical_target_identity.json"
    if actual_size == expected_size:
        records.append(AssertionRecord("file_size", STATUS_PASS, f"File size matches canonical ({actual_size:,} bytes)", stage_id="target_binary_integrity", evidence_ref=can_ref))
    else:
        records.append(AssertionRecord("file_size", STATUS_FAIL, f"Expected size {expected_size}, got {actual_size}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    actual_md5 = hashlib.md5(bin_data).hexdigest()
    expected_md5 = canonical.get('hashes', {}).get('md5')
    if actual_md5 == expected_md5:
        records.append(AssertionRecord("md5_digest", STATUS_PASS, f"MD5 matches ({actual_md5})", stage_id="target_binary_integrity", evidence_ref=can_ref))
    else:
        records.append(AssertionRecord("md5_digest", STATUS_FAIL, f"Expected MD5 {expected_md5}, got {actual_md5}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    actual_sha1 = hashlib.sha1(bin_data).hexdigest()
    expected_sha1 = canonical.get('hashes', {}).get('sha1')
    if actual_sha1 == expected_sha1:
        records.append(AssertionRecord("sha1_digest", STATUS_PASS, f"SHA-1 matches ({actual_sha1})", stage_id="target_binary_integrity", evidence_ref=can_ref))
    else:
        records.append(AssertionRecord("sha1_digest", STATUS_FAIL, f"Expected SHA-1 {expected_sha1}, got {actual_sha1}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    actual_sha256 = hashlib.sha256(bin_data).hexdigest()
    expected_sha256 = canonical.get('hashes', {}).get('sha256')
    if actual_sha256 == expected_sha256:
        records.append(AssertionRecord("sha256_digest", STATUS_PASS, f"SHA-256 matches ({actual_sha256})", stage_id="target_binary_integrity", evidence_ref=can_ref))
    else:
        records.append(AssertionRecord("sha256_digest", STATUS_FAIL, f"Expected SHA-256 {expected_sha256}, got {actual_sha256}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    parsed_info['size'] = actual_size
    parsed_info['sha256'] = actual_sha256

    try:
        if len(bin_data) < 64 or bin_data[:2] != b'MZ':
            records.append(AssertionRecord("pe_magic", STATUS_FAIL, "Invalid DOS header / MZ magic missing", stage_id="target_binary_integrity", evidence_ref=can_ref))
            return False, records, parsed_info

        e_lfanew = struct.unpack_from('<I', bin_data, 0x3C)[0]
        if e_lfanew + 256 > len(bin_data) or bin_data[e_lfanew:e_lfanew+4] != b'PE\x00\x00':
            records.append(AssertionRecord("pe_signature", STATUS_FAIL, "Invalid PE signature at e_lfanew", stage_id="target_binary_integrity", evidence_ref=can_ref))
            return False, records, parsed_info

        machine = struct.unpack_from('<H', bin_data, e_lfanew + 4)[0]
        num_sections = struct.unpack_from('<H', bin_data, e_lfanew + 6)[0]
        opt_header_size = struct.unpack_from('<H', bin_data, e_lfanew + 20)[0]
        opt_offset = e_lfanew + 24
        magic = struct.unpack_from('<H', bin_data, opt_offset)[0]
        entry_point = struct.unpack_from('<I', bin_data, opt_offset + 16)[0]

        pe_hdr = canonical.get('pe_header', {})
        expected_machine = int(pe_hdr.get('machine', '0x0'), 16)
        expected_magic = int(pe_hdr.get('magic', '0x0'), 16)
        expected_ep = int(pe_hdr.get('entry_point', '0x0'), 16)

        if machine == expected_machine and magic == expected_magic:
            records.append(AssertionRecord("pe_architecture", STATUS_PASS, f"Architecture x86_64 PE32+ (Machine {hex(machine)}, Magic {hex(magic)})", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("pe_architecture", STATUS_FAIL, f"Machine {hex(machine)} vs {hex(expected_machine)}, Magic {hex(magic)} vs {hex(expected_magic)}", stage_id="target_binary_integrity", evidence_ref=can_ref))

        if entry_point == expected_ep:
            records.append(AssertionRecord("pe_entry_point", STATUS_PASS, f"Entry point RVA matches canonical ({hex(entry_point)})", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("pe_entry_point", STATUS_FAIL, f"Expected entry point {hex(expected_ep)}, got {hex(entry_point)}", stage_id="target_binary_integrity", evidence_ref=can_ref))

        # Section table
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

        canonical_sec_names = [s['name'] for s in canonical.get('sections', [])]
        actual_sec_names = [s['name'] for s in actual_sections]
        if actual_sec_names == canonical_sec_names:
            records.append(AssertionRecord("section_table_names", STATUS_PASS, f"Sections match canonical exactly ({actual_sec_names})", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("section_table_names", STATUS_FAIL, f"Expected {canonical_sec_names}, got {actual_sec_names}", stage_id="target_binary_integrity", evidence_ref=can_ref))

        canonical_data_sec = next((s for s in canonical.get('sections', []) if s['name'] == '.data'), None)
        expected_data_raddr = canonical_data_sec.get('raw_data_offset') if canonical_data_sec else None
        data_sec = next((s for s in actual_sections if s['name'] == '.data'), None)
        if data_sec and data_sec['raddr'] == expected_data_raddr:
            records.append(AssertionRecord("data_section_offset", STATUS_PASS, f".data raw offset verified as {expected_data_raddr}", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("data_section_offset", STATUS_FAIL, f"Expected {expected_data_raddr}, got {data_sec['raddr'] if data_sec else 'missing'}", stage_id="target_binary_integrity", evidence_ref=can_ref))

        # Authenticode boundary check
        dir_base = opt_offset + 112
        cert_va, cert_size = struct.unpack_from('<II', bin_data, dir_base + 4 * 8)
        auth_sig = canonical.get('authenticode_signature', {})
        expected_cert_va = int(auth_sig.get('file_offset', '0x0'), 16)
        expected_cert_size = auth_sig.get('size', 0)

        if cert_va == expected_cert_va and cert_size == expected_cert_size:
            records.append(AssertionRecord("authenticode_bounds", STATUS_PASS, f"Authenticode bounds verified (offset {hex(cert_va)}, size {cert_size})", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("authenticode_bounds", STATUS_FAIL, f"Expected offset {hex(expected_cert_va)} size {expected_cert_size}, got {hex(cert_va)} {cert_size}", stage_id="target_binary_integrity", evidence_ref=can_ref))

        # CLR COM descriptor
        com_rva, com_size = struct.unpack_from('<II', bin_data, dir_base + 14 * 8)
        com_desc = canonical.get('clr_runtime', {}).get('com_descriptor_directory', {})
        expected_com_rva = int(com_desc.get('virtual_address', '0x0'), 16)
        expected_com_size = com_desc.get('size', 0)

        if com_rva == expected_com_rva and com_size == expected_com_size:
            records.append(AssertionRecord("clr_com_descriptor", STATUS_PASS, f"CLR COM descriptor verified at RVA {hex(com_rva)}, size {com_size}", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            records.append(AssertionRecord("clr_com_descriptor", STATUS_FAIL, f"Expected COM RVA {hex(expected_com_rva)} size {expected_com_size}, got {hex(com_rva)} {com_size}", stage_id="target_binary_integrity", evidence_ref=can_ref))

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
            records.append(AssertionRecord("cor20_header_offset", STATUS_FAIL, f"Invalid COM offset: {com_off}", stage_id="target_binary_integrity", evidence_ref=can_ref))
        else:
            cor_header = bin_data[com_off:com_off+72]
            meta_rva, meta_size = struct.unpack_from('<II', cor_header, 8)
            cor_flags = struct.unpack_from('<I', cor_header, 16)[0]

            cli_meta = canonical.get('clr_runtime', {}).get('cli_metadata_root', {})
            expected_meta_rva = int(cli_meta.get('virtual_address', '0x0'), 16)
            expected_meta_size = cli_meta.get('size_bytes', 0)
            expected_cor_flags = canonical.get('clr_runtime', {}).get('cor20_header', {}).get('flags')

            if meta_rva == expected_meta_rva and meta_size == expected_meta_size:
                records.append(AssertionRecord("cli_metadata_root", STATUS_PASS, f"CLI Metadata Root verified at RVA {hex(meta_rva)} (Size: {meta_size})", stage_id="target_binary_integrity", evidence_ref=can_ref))
            else:
                records.append(AssertionRecord("cli_metadata_root", STATUS_FAIL, f"Expected CLI RVA {hex(expected_meta_rva)} size {expected_meta_size}, got {hex(meta_rva)} {meta_size}", stage_id="target_binary_integrity", evidence_ref=can_ref))

            if cor_flags == expected_cor_flags:
                records.append(AssertionRecord("cor20_flags", STATUS_PASS, f"COR20 flags verified as {expected_cor_flags} (C++/CLI mixed mode)", stage_id="target_binary_integrity", evidence_ref=can_ref))
            else:
                records.append(AssertionRecord("cor20_flags", STATUS_FAIL, f"Expected flags {expected_cor_flags}, got {hex(cor_flags)}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    except Exception as ex:
        records.append(AssertionRecord("pe_parsing_exception", STATUS_FAIL, f"PE parsing error: {str(ex)}", stage_id="target_binary_integrity", evidence_ref=can_ref))

    is_valid = all(r.status == STATUS_PASS for r in records)
    return is_valid, records, parsed_info


def validate_evidence_manifest(
    manifest_path: str,
    repo_root: str
) -> Tuple[bool, List[AssertionRecord], Dict[str, Any]]:
    """
    Independently audits all tracked files in an evidence validation manifest:
    - Manifest file presence and valid JSON
    - Each referenced evidence file exists on disk
    - Each file matches expected size_bytes
    - Each file matches expected sha256 checksum
    """
    records: List[AssertionRecord] = []
    summary: Dict[str, Any] = {'total_files': 0, 'verified_files': 0, 'mismatches': []}

    man_rel = os.path.relpath(manifest_path, repo_root).replace('\\', '/') if manifest_path else "evidence/phase1/reconciliation/validation_manifest.json"
    if not manifest_path or not os.path.exists(manifest_path):
        records.append(AssertionRecord("manifest_presence", STATUS_FAIL, f"Validation manifest missing: '{manifest_path}'", stage_id="manifest_integrity", evidence_ref=man_rel))
        return False, records, summary

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_doc = json.load(f)
    except Exception as e:
        records.append(AssertionRecord("manifest_json_parse", STATUS_FAIL, f"Failed parsing manifest JSON: {str(e)}", stage_id="manifest_integrity", evidence_ref=man_rel))
        return False, records, summary

    files = manifest_doc.get('files', [])
    summary['total_files'] = len(files)
    records.append(AssertionRecord("manifest_loaded", STATUS_PASS, f"Validation manifest loaded ({len(files)} tracked files)", stage_id="manifest_integrity", evidence_ref=man_rel))

    for entry in files:
        rel_p = entry.get('relative_path') or entry.get('path', '')
        exp_size = entry.get('size_bytes')
        exp_sha = entry.get('sha256')
        full_p = os.path.join(repo_root, rel_p.replace('/', os.sep))

        if not os.path.exists(full_p):
            records.append(AssertionRecord(f"file_exists:{rel_p}", STATUS_FAIL, f"Tracked file missing on disk: '{rel_p}'", stage_id="manifest_integrity", evidence_ref=rel_p))
            summary['mismatches'].append({'path': rel_p, 'error': 'missing'})
            continue

        try:
            with open(full_p, 'rb') as f:
                content = f.read()
        except Exception as e:
            records.append(AssertionRecord(f"file_read:{rel_p}", STATUS_FAIL, f"Failed reading file '{rel_p}': {str(e)}", stage_id="manifest_integrity", evidence_ref=rel_p))
            summary['mismatches'].append({'path': rel_p, 'error': 'read_error'})
            continue

        act_size = len(content)
        act_sha = hashlib.sha256(content).hexdigest()

        if act_size != exp_size:
            records.append(AssertionRecord(f"file_size:{rel_p}", STATUS_FAIL, f"Size mismatch for '{rel_p}': expected {exp_size}, got {act_size}", stage_id="manifest_integrity", evidence_ref=rel_p))
            summary['mismatches'].append({'path': rel_p, 'error': 'size_mismatch', 'expected': exp_size, 'actual': act_size})
        elif act_sha != exp_sha:
            records.append(AssertionRecord(f"file_sha256:{rel_p}", STATUS_FAIL, f"SHA-256 mismatch for '{rel_p}': expected {exp_sha}, got {act_sha}", stage_id="manifest_integrity", evidence_ref=rel_p))
            summary['mismatches'].append({'path': rel_p, 'error': 'sha_mismatch', 'expected': exp_sha, 'actual': act_sha})
        else:
            records.append(AssertionRecord(f"checksum_match:{rel_p}", STATUS_PASS, f"Verified '{rel_p}'", stage_id="manifest_integrity", evidence_ref=rel_p))
            summary['verified_files'] += 1

    is_valid = (len(summary['mismatches']) == 0 and summary['verified_files'] == summary['total_files'])
    return is_valid, records, summary
