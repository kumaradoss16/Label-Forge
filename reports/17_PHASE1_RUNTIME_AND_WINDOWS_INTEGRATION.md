# Phase 1: Runtime Observations & Windows Integration

**Target:** Seagull Scientific BarTender Designer 11.4  
**Runtime Host:** Microsoft Windows 10 Home Single Language (10.0.19045, 64-bit)  
**Execution Context:** Non-Interactive Background Session (Session ID 22)  
**Classification:** `[VERIFIED_RUNTIME]` & `[VERIFIED_STATIC]`  

---

## 1. Controlled Runtime Observations

Controlled execution tests were performed under non-destructive conditions without bypassing licensing:

### 1.1 Process Startup Lifecycle (`RT-01`)
- **Invocation:** `BarTend.exe` launched with `/Min=SystemTray`.
- **Observable Behavior:**
  - Process spawns under Windows x64 host.
  - Loads CRT (`vcruntime140.dll`, `msvcp140.dll`) and initializes CLR host (`mscoree.dll` -> `clr.dll`).
  - Initializes MFC application thread (`AfxWinMain`).
  - In a headless or unactivated environment, the process displays a modal Win32 activation prompt before entering the main message pump.
  - In headless Session 22, the process halts awaiting user interaction, confirming that activation is checked before document rendering.

### 1.2 Managed Print Engine License Enforcement (`RT-02`)
- **Invocation:** Instantiation of `Seagull.BarTender.Print.Engine` via .NET reflection:
  ```powershell
  $engine = New-Object Seagull.BarTender.Print.Engine
  $engine.Start()
  ```
- **Observed Result:**
  ```
  Seagull.BarTender.Print.LicenseException: You must activate BarTender with a valid product key code to use the BarTender Print Service API. BarTender Automation edition or greater is required.
     at Seagull.BarTender.Print.Engine.Start()
  ```
- **Finding:** Proves that all programmatic printing capabilities are gated by an enterprise license validation check communicating with the Seagull License Server (SLS).

### 1.3 COM Automation Server (`RT-03`)
- **Invocation:** `New-Object -ComObject "BarTender.Application"`
- **Observed Result:** Activates the registered `BarTender.Application` CLSID (`{D5856250-13D3-11D1-9D2B-00609787E3AE}`), launching `BarTend.exe /Automation`.

---

## 2. Windows Operating System Integration

### 2.1 Windows Print Spooler Integration
- **API Interface:** `winspool.drv` (`OpenPrinterW`, `StartDocPrinterW`, `StartPagePrinterW`, `WritePrinter`, `EndPagePrinterW`, `EndDocPrinterW`).
- **Dual-Path Printing Model:**
  1. **Standard GDI Spooling:** When targeting non-thermal printers (office laser, inkjet), BarTender renders via GDI device contexts (`HDC`) into EMF/XPS spool files.
  2. **Raw Thermal Pass-Through:** When targeting thermal barcode printers (Zebra, Datamax, Sato) with Seagull drivers, BarTender bypasses GDI rasterization and emits native ASCII printer control streams (ZPL II, EPL2) directly via `WritePrinter` with `DATATYPE = "RAW"`.

### 2.2 Windows Services
BarTender installs several standing background services:
- **`BarTender System Service` (`BtSysSrv.exe`):** Manages shared printer status, logging, and security auditing.
- **`Seagull License Server` (`SLS.exe`):** Network license manager coordinating concurrent printer licenses across workstations.

### 2.3 Registry Configuration
- **User Settings:** `HKCU\Software\Seagull Scientific\BarTender\11.4\` (Recently opened documents, toolbar state, grid settings, units).
- **System Settings:** `HKLM\Software\Seagull Scientific\BarTender\11.4\` (Installation paths, shared database connections, license server host).

---

## 3. Implications for Label-Forge

- **Zero License Server Overhead:** LabelForge is fully self-contained and operates without complex background licensing services or product key lockouts.
- **Independent Spooler Architecture:** LabelForge implements dual-path printing cleanly:
  - Standard Windows printing via WPF `PrintDialog` and `XpsDocumentWriter`.
  - High-speed direct industrial thermal printing via native C# ZPL II generation over `RawPrinterHelper` (`winspool.drv` RAW mode).
