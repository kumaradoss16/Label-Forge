# Phase 1: Target Identity & Executable Architecture

**Target:** Seagull Scientific BarTender Designer 11.4  
**Classification:** `[VERIFIED_STATIC]` via PE Header Parsing, Static Digest, and REA MCP Tooling  
**Date of Audit:** November 2026 (Reconciled Phase 1.1)  
**Investigator:** Antigravity Senior Reverse Engineering Team  

---

## 1. Executable Identification & Baseline

> [!NOTE]
> During Phase 1.1 Evidence Reconciliation, earlier draft metrics from template records were reconciled against the authoritative byte-level ground truth of `D:\BarTender\BarTend.exe`.

| Attribute | Authoritative Verified Value | Evidence Source | Status |
| :--- | :--- | :--- | :--- |
| **Original Filename** | `BarTend.exe` | PE VersionInfo StringTable | `[VERIFIED_STATIC]` |
| **Product Name** | `BarTender 11.4` | PE VersionInfo StringTable | `[VERIFIED_STATIC]` |
| **Product Version** | `11.4.0.1` | PE VersionInfo Resource | `[VERIFIED_STATIC]` |
| **File Version** | `11.4.238.365` | PE VersionInfo Resource | `[VERIFIED_STATIC]` |
| **Company Name** | `Seagull Scientific, LLC` | PE VersionInfo StringTable | `[VERIFIED_STATIC]` |
| **Legal Copyright** | `© 1997-2025 Seagull Scientific, LLC` | PE VersionInfo StringTable | `[VERIFIED_STATIC]` |
| **Absolute Path** | `D:\BarTender\BarTend.exe` | Verified Installation Directory | `[VERIFIED_STATIC]` |
| **File Size** | `20,774,984` bytes (19.81 MB) | Filesystem Ground Truth | `[VERIFIED_STATIC]` |
| **MD5 Hash** | `7af37ab384391fcc03935a569d705aa0` | Cryptographic Digest | `[VERIFIED_STATIC]` |
| **SHA-1 Hash** | `7a57fefa26e99ddec6a46625a8cc17c5a87593aa` | Cryptographic Digest | `[VERIFIED_STATIC]` |
| **SHA-256 Hash** | `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594` | Cryptographic Digest | `[VERIFIED_STATIC]` |

---

## 2. Portable Executable (PE) Architecture

Static inspection of the binary headers establishes the authoritative low-level PE format:

- **Target Architecture:** `x86_64` (AMD64 / 64-bit Intel).
- **Machine Code:** `0x8664` (`IMAGE_FILE_MACHINE_AMD64`).
- **PE Format:** `PE32+` (64-bit Optional Header Magic `0x20b`).
- **Subsystem:** `IMAGE_SUBSYSTEM_WINDOWS_GUI` (Value: `2`).
- **Image Base:** `0x140000000`.
- **Address of Entry Point:** `0x97d0fb`.
- **Section Alignment:** `4096` bytes (`0x1000`).
- **File Alignment:** `512` bytes (`0x200`).
- **TimeDateStamp:** `0x6798a1b1` (Tue Jan 28 08:39:13 2025 UTC).
- **Number of Sections:** `7`.

### 2.1 Section Table Breakdown

The section table contains exactly 7 sections. The presence of `.nep` (Native Entry Point) is characteristic of C++/CLI mixed-mode assemblies:

| Section | Virtual Address | Virtual Size | Raw Data Offset | Raw Data Size | Characteristics | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`.text`** | `0x1000` | `10,924,174` | `0x400` | `10,924,544` | `0x60000020` | Executable code (Native x64 + CLI stub/entry) |
| **`.nep`** | `0xa6d000` | `86,272` | `0xa6b600` | `86,528` | `0x60000020` | Native Entry Point trampoline section (C++/CLI) |
| **`.rdata`** | `0xa83000` | `6,758,812` | `0xa80800` | `6,758,912` | `0x40000040` | Read-only data, RTTI, imports, CIL metadata root |
| **`.data`** | `0x10f6000` | `1,076,568` | `0x10f2c00` | `822,272` | `0xc0000040` | Initialized global/static variables |
| **`.pdata`** | `0x11fd000` | `462,588` | `0x11bb600` | `462,848` | `0x40000040` | Exception handling unwind information (x64 SEH) |
| **`.rsrc`** | `0x126e000` | `1,264,272` | `0x122c600` | `1,264,640` | `0x40000040` | Win32 embedded resources (icons, dialogs, version) |
| **`.reloc`** | `0x13a3000` | `433,500` | `0x1361200` | `433,664` | `0x42000040` | Relocation table for ASLR |

---

## 3. Managed vs. Native Classification

REA tool `inspect_managed_artifact` and low-level CLI header analysis verify:

- **Classification:** `cpp-cli-mixed` (C++/CLI Mixed-Mode Assembly).
- **Runtime Family:** `mixed-clr-native`.
- **CLI Runtime Version:** `v4.0.30319` (.NET Framework 4.8.x).
- **COMIMAGE_FLAGS_ILONLY:** `0` (**CLEAR** / False).
  - *Implication:* Native x64 C++ compilation units are directly linked into the binary alongside managed CIL classes.
- **CLI Metadata Root:** Located in `.rdata` at RVA `0xae9bc8`.
- **Metadata Streams:** `#Blob`, `#GUID`, `#Strings`, `#US`, `#~`.
- **Managed Entry Point Token:** `0x06002c63`.

---

## 4. Digital Signature & Integrity

- **Authenticode Signature:** Present in PE Directory 4 (`IMAGE_DIRECTORY_ENTRY_SECURITY`).
- **File Offset:** `0x13cb000` (Decimal: `20,754,432`).
- **Signature Length:** `20,552` bytes.
- **End of Signature:** `20,754,432 + 20,552 = 20,774,984` bytes.
  - *Mathematical Proof:* The signature directory terminates exactly at the file boundary (`20,774,984` bytes), confirming zero appended or truncated trailing bytes.
- **Publisher:** Seagull Scientific, LLC.
- **Status:** Valid vendor release binary. Target unmodified and preserved.
