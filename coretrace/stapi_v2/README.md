# Directory for building second version of SolTrace API, stapi_v2.

### Build

In `~/stapi_v2`, run `python -m build --wheel`. The `Microsoft.CppBuild.targets(548,5): warning MSB8029` seems to be harmless.

Note:
View wheel contents on Windows: `Add-Type -A "System.IO.Compression.FileSystem"; [IO.Compression.ZipFile]::OpenRead("C:\abs\path\to\SolTrace\coretrace\stapi_v2\dist\pysoltrace-0.1.0-cp314-cp314-win_amd64.whl").Entries.FullName`
Linux: unzip -l pysoltrace-0.1.0-cp314-cp314-win_amd64.whl

View dll contents on Windows in Developer PowerShell: `dumpbin /exports stapi_v2.dll`

[WinError -529697949] Windows Error 0xe06d7363 usually means rebuild and recompile. Hunch is that its a loading thing with Optix stuff.
