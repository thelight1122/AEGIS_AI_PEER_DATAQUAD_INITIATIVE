# Verus Desktop MCP first install pause — Python 3.10 compatibility

Observed UTC: 2026-08-15T11:43:21Z

Status: `INSTALL_ATTEMPT_PAUSED / NO ACTIVATION / SOURCE CORRECTION REQUIRED`

## Accepted authority

- Independent Claude source-audit ACCEPT SHA-256:
  `5102E03C1A1E085F8B3613DCA7B3EC7E78953A69227B54D96098E4D21E8B72F9`
- Attempted source commit:
  `de67e93fe9d44e1b79f96dc3531d11d401e41e32`
- Attempted release manifest SHA-256:
  `D7CE63B2459F2A625A9A1943AA3643993EC5BE711515190AE1C3D6627BD38DC2`

## Fresh preflight result

- Hostname and machine ID remained `AEGISGabePeer` and
  `8690ad3d73a2d2ed9c38d680b792db6e60264010d8e16919a665cc748a7df45e`.
- Ubuntu 22.04, Python 3.10.12, systemd running, 4 CPUs, more than 18 GB
  available memory, and more than 68 GB available root disk.
- Port 8791 was free; no Verus account, root, or service existed.
- Gabe container ID/image/state/restart count remained
  `96c126a21af2bae5536eae01a1211dc0f3d2c173160c8394801ff8bae7119c14`,
  `sha256:ba712c40ab67d272b3edfd56bd3bc236555955614ea6484969588fd5b251e125`,
  running, zero restarts.
- Protected local Gabe status remained HTTP 200 with 1,412 bytes.

## Transfer and install result

- The 29-file release was transferred to the unique temporary path
  `/tmp/aegis-verus-upload-de67e93fe9d4`.
- Remote manifest and receipt hashes exactly matched the accepted local hashes.
- The Windows transfer did not preserve the installer executable bit, so the
  first invocation was refused before installer execution. The installer was
  then explicitly invoked with `bash`; this did not alter its contents.
- The installer created only the accepted Verus account, roots, release,
  environment, and unit, then service start failed before activation.
- Transactional recovery stopped and disabled `aegis-verus-lab.service` and
  preserved the isolated Verus state. No listener opened and no turn committed.

## Exact failure and correction

The target host runs Python 3.10.12. The shared runtime imported
`enum.StrEnum`, introduced in Python 3.11, so command startup failed with:

`ImportError: cannot import name 'StrEnum' from 'enum'`

Inspection also found that copied directory modes inherited Windows transfer
metadata such as `0707`. The corrective source change therefore:

1. supplies a standard-library Python 3.10-compatible `StrEnum` fallback;
2. declares the verified minimum Python version as 3.10; and
3. deterministically normalizes installed directories to `0755`, regular files
   to `0644`, and command/shell entrypoints to `0755` before service start.

Focused tests were added first and failed on both absent corrections, then
passed after implementation. A new exact-commit release and independent audit
are required before retrying installation.

## Preservation proof

Before and after the paused attempt, the same bounded Gabe metadata inventory
reported 74 files, 30 descendant directories, 0 symlinks, 6,564,249,382 bytes,
and SHA-256
`e23de84ba7836e534280229acbdbc8d74e17768b9cd567dce346087011d3308a`.
The protected local status remained HTTP 200/1,412 bytes. Gabe container ID,
image, running state, and restart count were unchanged.

No Gabe service, container, DataQuad, prompt, credential, file, listener,
tunnel, or history was modified.
