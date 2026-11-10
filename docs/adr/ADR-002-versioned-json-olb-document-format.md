# ADR-002: Versioned JSON Open Label (.olb) Document Format

## Status
Accepted

## Context
BarTender uses a proprietary binary format (`.btw`) rooted in OLE Structured Storage, compounded by legacy MFC serialization and proprietary payload compression. This format is opaque, prone to backwards incompatibility across BarTender releases, and completely unsuited for an open, maintainable architecture.

LabelForge requires an independent, robust, human-inspectable, and forward-compatible document format.

## Decision
1. **Extension**: Adopt `.olb` (Open Label) as the canonical file extension.
2. **Payload Serialization**: Use UTF-8 JSON via `System.Text.Json`.
3. **Explicit Format Versioning**: Every document root must contain a mandatory `formatVersion` string property (currently `"1.0"`). Deserializers must validate this version before processing.
4. **Unsupported Version Policy**: Loading a file whose major version exceeds the supported runtime version fails immediately with an explicit `UnsupportedSchemaVersionException` rather than silent partial deserialization or data loss.
5. **Polymorphic Object Hierarchy**: Use standard System.Text.Json polymorphic type discriminators (`$type`) mapped to clean type names (`TextObject`, `BarcodeObject`, `ShapeObject`, `PictureObject`).
6. **Atomic File Write Strategy**: File saves are executed atomically via temporary file buffering (`.filename.tmp.guid`) followed by atomic OS replace operations (`File.Replace`). Existing files are never overwritten in-place, eliminating corrupt truncated files on crashes.

## Consequences
- **Positive**: Complete transparency, easy version control (git diffable), and forward-compatibility checks.
- **Positive**: Zero risk of partial document corruption during save interruptions.
- **Trade-off**: Text-based JSON has larger file sizes than compressed binary blobs; however, typical label documents are under 100 KB, making the readability and safety advantages overwhelming.
