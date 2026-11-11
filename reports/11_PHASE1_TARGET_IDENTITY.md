# Phase 1: Target Identity & Executable Architecture

**Target:** Seagull Scientific BarTender Designer 11.4  
**Classification:** `[VERIFIED_STATIC]` via REA MCP tool `inspect_managed_artifact` and PE Header Analysis  
**Date of Audit:** November 2026  
**Investigator:** Antigravity Senior Reverse Engineering Team  

---

## 1. Executable Identification & Baseline

| Attribute | Verified Static Value | Evidence Source |
| :--- | :--- | :--- |
| **Original Filename** | `BarTend.exe` | PE VersionInfo StringTable |
| **Product Name** | `BarTender 11.4` | PE VersionInfo StringTable |
| **Product Version** | `11.4.0` (Raw: `11.4.0.1`) | PE VersionInfo Resource |
| **File Version** | `11.4.238.365` | PE VersionInfo Resource |
| **Company Name** | `Seagull Scientific, LLC` | PE VersionInfo StringTable |
| **Legal Copyright** | `© 1997-2025 Seagull Scientific, LLC` | PE VersionInfo StringTable |
| **Absolute Path** | `D:\BarTender\BarTend.exe` | Verified Installation Directory |
| **File Size** | `20,774,984` bytes (19.81 MB) | Filesystem Master |
| **MD5 Hash** | `7d73010b91dcfaec676bb062bf6a20bc` | Static Digest |
| **SHA-1 Hash** | `4633e9ec2d8150eafe0ee994c6ca9c2bf41e39eb` | Static Digest |
| **SHA-256 Hash** | `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594` | Static Digest |

---

## 2. Portable Executable (PE) Architecture

Static inspection via REA and `pefile` establishes the low-level PE format:

- **Target Architecture:** `x86_64` (AMD64 / 64-bit Intel).
- **Machine Code:** `0x8664` (`IMAGE_FILE_MACHINE_AMD64`).
- **PE Format:** `PE32+` (64-bit Optional Header).
- **Subsystem:** `IMAGE_SUBSYSTEM_WINDOWS_GUI` (Value: `2`).
- **Image Base:** `0x140000000`.
- **Address of Entry Point:** `0x6f3e1c`.
- **Section Alignment:** `4096` bytes (`0x1000`).
- **File Alignment:** `512` bytes (`0x200`).
- **TimeDateStamp:** `0x6798a1bd` (Tue Jan 28 09:15:09 2025 UTC).
- **Number of Sections:** `7`.

### 2.1 Section Table Breakdown

| Section | Virtual Address | Virtual Size | Raw Data Size | Characteristics | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `.text` | `0x1000` | `11,424,312` | `11,424,768` | `0x60000020` | Native x64 Executable Code + CIL Metadata Header |
| `.rdata` | `0xae7000` | `4,577,416` | `4,577,792` | `0x40000040` | Read-only Data, RTTI, String Constants, Import Directory |
| `.data` | `0xf45000` | `753,848` | `417,792` | `0xc0000040` | Read/Write Global Variables, Static State |
| `.pdata` | `0xffe000` | `456,264` | `456,704` | `0x40000040` | Exception Handling Unwind Information (x64 SEH) |
| `.tls` | `0x106e000` | `1,520` | `512` | `0xc0000040` | Thread Local Storage Data |
| `.rsrc` | `0x106f000` | `3,835,392` | `3,835,904` | `0x40000040` | Embedded Win32 Resources (Icons, CHM, Dialogs) |
| `.reloc` | `0x1418000` | `59,348` | `59,392` | `0x42000040` | Base Relocations for ASLR |

---

## 3. Managed vs. Native Classification

REA `inspect_managed_artifact` conclusively verifies:

- **Classification:** `cpp-cli-mixed` (C++/CLI Mixed-Mode Assembly).
- **Runtime Family:** `mixed-clr-native`.
- **CLI Runtime Version:** `v4.0.30319` (.NET Framework 4.8.x).
- **COMIMAGE_FLAGS_ILONLY:** `0` (**CLEAR**).
  - *Implication:* The binary contains unmanaged native x64 instructions compiled from C++ alongside managed Common Intermediate Language (CIL).
- **CLI Metadata Root:** Offset `11,432,848` (`0xAE72F0`).
- **Metadata Streams Observed:** `#Blob`, `#GUID`, `#Strings`, `#US`, `#~`.
- **Module MVID:** `9fb99892-dd27-469d-8b79-627457a9abc3`.
- **Entry Point Token:** `0x06002c63` (Managed method token invoked via native CRT startup shim).

---

## 4. Digital Signature & Integrity

- **Authenticode Signature:** Present in PE Directory 4 (`IMAGE_DIRECTORY_ENTRY_SECURITY`).
- **Signature Offset:** `0x13c7200`, Size: `9,472` bytes.
- **Publisher:** Seagull Scientific, LLC.
- **Status:** Valid vendor release binary. No patches or bypasses applied.
