# 01. Target Identity Report: BarTender Designer 11.4

## Executive Summary
This document provides the foundational identity, cryptographic hashes, PE architecture classification, runtime evidence, security mitigations, and digital signature verification for the primary executable of BarTender Designer 11.4 (`BarTend.exe`).

---

## 1. Environment & REA Tool Catalog Inspection
In accordance with Mandatory Operating Rules 1–3:
* **REA Tool Catalog Status:** Inspected MCP server environment and tool definitions. No active REA (Reverse Engineering Assistant) MCP server or native REA provider daemon was connected or available in the runtime environment (only `gemini-api_gemini-api-docs` was registered).
* **Adherence to Operating Rules:** In compliance with Rule 2 ("Do not invent REA tool names, arguments or CLI commands") and Rule 3 ("Check REA readiness and provider availability before analysis"), standard Windows diagnostic tooling, Python (`pefile`), and .NET Reflection APIs were employed for verifiable static binary and metadata inspection.
* **Workspace Paths:**
  * Target Executable: `D:\ReverseEngineering\bartender-investigation\target\BarTend.exe` (mapped via junction to `E:\ReverseEngineering\bartender-investigation\target\BarTend.exe`)
  * Target Installation Root: `D:\BarTender\`
  * Evidence Directory: `D:\ReverseEngineering\bartender-investigation\evidence\`
  * Reports Directory: `D:\ReverseEngineering\bartender-investigation\reports\`

---

## 2. File Metadata & Version Information
* **File Name:** `BarTend.exe`
* **Internal Name:** `BarTender`
* **Original Filename:** `BarTend.exe`
* **File Version:** `11.4.238.365`
* **Product Name:** `BarTender 11.4`
* **Product Version:** `11.4.0`
* **Display Version (Registry):** `11.4.0.238365`
* **File Size:** `20,774,984 bytes` (19.81 MB)
* **Creation Timestamp:** 2026-11-09 15:55:10 UTC
* **Last Modified Timestamp:** 2025-01-28 09:15:25 UTC
* **Language:** Language Neutral (`0x0000`)
* **Legal Copyright:** Seagull Scientific, Inc.

---

## 3. Cryptographic Hashes
* **MD5:** `7af37ab384391fcc03935a569d705aa0`
* **SHA-1:** `7a57fefa26e99ddec6a46625a8cc17c5a87593aa`
* **SHA-256:** `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594`
* **SHA-512:** `501ccc356dc177d1c7337f2489c9e87abf3843a63cd88769d130d989413c3d60ee10935d189638e2e0c44483a9357bc221e17c1430a301a87b615bda8838cc27`

---

## 4. PE Header & Architecture Classification
* **Machine Type:** `0x8664` (`IMAGE_FILE_MACHINE_AMD64` — 64-bit x86-64 / AMD64)
* **Subsystem:** `2` (`IMAGE_SUBSYSTEM_WINDOWS_GUI`)
* **Image Base:** `0x140000000`
* **Entry Point RVA:** `0x97d0fb`
* **Linker Version:** `14.29` (Microsoft Visual Studio 2019 / MSVC v142 toolset)
* **OS / Subsystem Version:** `6.0` (Windows Vista / Windows Server 2008 minimum requirement)
* **PE File Characteristics:** `0x0022`
  * `IMAGE_FILE_EXECUTABLE_IMAGE` (File is executable)
  * `IMAGE_FILE_LARGE_ADDRESS_AWARE` (Application can handle > 2GB addresses)
* **DLL Characteristics:** `0x8120`
  * `DYNAMIC_BASE (ASLR):` Disabled (`false`)
  * `NX_COMPAT (DEP):` Enabled (`true`)
  * `GUARD_CF (Control Flow Guard):` Disabled (`false`)
  * `HIGH_ENTROPY_VA:` Enabled (`true`)
  * `TERMINAL_SERVER_AWARE:` Enabled (`true`)

---

## 5. Binary Classification: Managed vs Native
Analysis of the Data Directory confirms that `BarTend.exe` is a **Mixed-Mode (C++/CLI) PE Executable**:

| Metric | Value | Architectural Significance |
| :--- | :--- | :--- |
| **CLR Header Directory (`COM_DESCRIPTOR`)** | RVA `0xae9b90`, Size `72 bytes` | CLR 2.0/4.0 descriptor present |
| **CLR Runtime Version** | `2.5` | Microsoft Visual C++ Managed Runtime Header |
| **Metadata Directory** | RVA `0xc3ca00`, Size `3,111,676 bytes` (~3.1 MB) | Substantial embedded .NET Type Metadata |
| **CLR Flags** | `0x00000000` | Neither `COMIMAGE_FLAGS_ILONLY` nor `32BITREQUIRED` |
| **IL_ONLY Flag** | `False` | Contains native x64 machine instructions |
| **Native Entry Point Section (`.nep`)** | Present (`0xa6d000`, 86,272 bytes) | MSVC mixed-mode native bootstrap thunks |
| **Managed Runtime Interop Import** | `mscoree.dll` (`_CorExeMain`) & `MFCM140U.dll` | C++/CLI MFC Managed Extensions integration |

### Architectural Conclusion
`BarTend.exe` is **not** a pure managed .NET assembly, nor is it a pure native Win32 application. It is a large-scale **hybrid C++/CLI mixed-mode executable**. The native core hosts the document layout canvas, MFC / Codejock UI ribbon controls, and native barcode rendering engines, while directly binding via C++/CLI to managed .NET Framework 4.8 business logic, database connectors, and WCF service endpoints.

---

## 6. PE Section Analysis

| Section | Virtual Address | Virtual Size | Raw Size | Entropy | Characteristics | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `.text` | `0x00001000` | 10,924,174 | 10,924,544 | 6.3922 | `0x60000020` | Native compiled machine code & CIL method bodies |
| `.nep` | `0x00a6d000` | 86,272 | 86,528 | 5.0435 | `0x60000020` | Native Entry Point / C++/CLI thunk tables |
| `.rdata` | `0x00a83000` | 6,758,812 | 6,758,912 | 5.9269 | `0x40000040` | Read-only constants, imports, CLR metadata |
| `.data` | `0x010f6000` | 1,076,568 | 822,272 | 4.3546 | `0xc0000040` | Initialized global/static variables |
| `.pdata` | `0x011fd000` | 462,588 | 462,848 | 6.5111 | `0x40000040` | x64 Structured Exception Handling (SEH) unwind tables |
| `.rsrc` | `0x0126e000` | 1,264,272 | 1,264,640 | 5.6780 | `0x40000040` | Win32 Resources (Icons, Version, Manifest) |
| `.reloc` | `0x013a3000` | 433,500 | 433,664 | 5.4458 | `0x42000040` | Base relocation fixup table |

---

## 7. Embedded Resources & Application Manifest
PE Resource Directory contains:
* `RT_ICON` (8 instances)
* `RT_GROUP_ICON` (2 instances)
* `RT_STRING` (1 table)
* `RT_RCDATA` (12 instances)
* `RT_VERSION` (1 block)
* `RT_MANIFEST` (1 instance)

### Embedded Manifest Summary (`BarTend.exe.manifest`)
* **Identity Name:** `MyApplication.app` (version `1.0.0.0`)
* **Common Controls:** Uses Microsoft.Windows.Common-Controls version `6.0.0.0` (`amd64`, public key `6595b64144ccf1df`)
* **UAC Level:** `asInvoker` (`uiAccess="false"`)
* **DPI Awareness:** `<ms_windowsSettings:dpiAware>false</ms_windowsSettings:dpiAware>` (Relies on OS scaling / internal MFC GDI scaling)
* **Supported OS GUIDs:**
  * Windows Vista: `{e2011457-1546-43c5-a5fe-008deee3d3f0}`
  * Windows 7: `{35138b9a-5d96-4fbd-8e2d-a2440225f93a}`
  * Windows 8: `{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}`
  * Windows 8.1: `{1f676c76-80e1-4239-95bb-83d0f6d0da78}`
  * Windows 10/11: `{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}`

---

## 8. Publisher & Digital Signature Verification
* **Signature Status:** Valid (`Signature verified`)
* **Signature Type:** Authenticode (PKCS #7)
* **Signer Subject:** `CN="Seagull Software, LLC", O="Seagull Software, LLC", L=Bellevue, S=Washington, C=US`
* **Signer Issuer:** `CN=DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1, O="DigiCert, Inc.", C=US`
* **Serial Number:** `0E416223563E6A83A68983C5675548C6`
* **Certificate Validity:** 2024-08-01 to 2027-09-17
* **Signer Thumbprint:** `8192FE53409F737333B100502A0880C6062E7EE7`
* **Timestamp Service:** DigiCert Timestamp 2024 (`DBD385EE62DBD23E7BE4F67148508724D5865B45`)
* **Timestamp Validity:** Valid through 2035-11-26

---

## 9. Key Findings for Clean-Room Replacement
1. **64-bit Architecture:** The target is purely 64-bit (`AMD64`). The independent replacement must target Windows x64 (`win-x64`) or `.NET 8 / 9`.
2. **Hybrid Heritage:** BarTender 11.4 evolved from a legacy C++ Win32/MFC application into a hybrid mixed-mode application.
3. **Clean-Room Opportunity:** Rather than reproducing legacy C++/CLI complexity or MFC/Codejock windowing, an independent replacement can be implemented using modern C# / WPF / MVVM, achieving cleaner architecture, true per-monitor DPI awareness, and native asynchronous execution.
