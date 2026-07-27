# LocalVoice Linux packaging fix

Corrected version: 2.1.1

Fixed:
- Added missing `installer/linux/localvoice.desktop`
- Added missing `installer/linux/AppRun`
- Aligned package version across Python, Inno Setup and DEB packaging
- Made the DEB output name match `Build-Linux.sh`
- Added explicit missing-file checks before packaging
- Kept helper scripts invoked through `bash`
- Verified Bash syntax for all Linux build scripts

Bash syntax checks:
{
  "scripts/Build-Linux.sh": 0,
  "scripts/Setup-Linux.sh": 0,
  "installer/linux/build-deb.sh": 0,
  "installer/linux/AppRun": 0
}
