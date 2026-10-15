# ADR 0002: Linux containers on the inspected Windows laptop

Status: accepted, 2026-10-14.

The Windows host has Python and Node but no detected CMake/compiler. Docker Desktop
and WSL2 are installed. Start the installed Docker engine and build C++20 inside a
Debian-based image instead of modifying the host compiler/driver installation.

Pin base image digests, direct compiler/build dependencies, uv and pnpm. Verify the
same C++ binary in CTest, Python integration tests, and the runtime container.
Docker is the tested Windows and portable Linux golden path. A native MSVC/Linux
build is structurally supported by CMake but is not a verified host pathway yet.

Debian transitive package repositories still evolve; image/lock pins do not imply
a fully hermetic OS rebuild. A snapshot package mirror/SBOM gate is a later hardening
task. GNU builds statically link the standard C++/GCC runtime so the final Python
image does not need the compiler libraries installed.
