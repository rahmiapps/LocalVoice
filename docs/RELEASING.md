# Publishing a GitHub Release

## Recommended first release

- Tag: `v2.1.1`
- Release title: `LocalVoice 2.1.1`
- Target branch: `main`

## Files to upload

```text
LocalVoice-Setup-Windows-x64.exe
LocalVoice-Windows-x64-Portable.zip
LocalVoice-Linux-x86_64.AppImage
LocalVoice-Linux-amd64.deb
LocalVoice-Linux-x64.tar.gz
SHA256SUMS.txt
```

## Release procedure

1. Build and test the packages on real Windows and Linux systems.
2. Generate SHA-256 checksums.
3. Push the final source and create the version tag.
4. Open **Releases → Draft a new release**.
5. Select or create tag `v2.1.1`.
6. Use the text from `docs/RELEASE_NOTES_TEMPLATE.md`.
7. Upload the installer and package files.
8. Mark as a pre-release until the clean-install tests are complete.
9. Publish the final release.

Do not commit the EXE installer directly into the Git history. GitHub Releases is the correct place for binary packages.
