# conan-flatdeploy - Deployment to $HOME/.local or a single directory

This Conan package adds two new custom generators: `flatdeploy` and `persistent`.
They are very similar to the [`deploy`](https://docs.conan.io/en/latest/reference/generators/deploy.html) generator that is part of Conan already but has some limitations in practice:

* When deploying a single application with its libraries, the directories have to be merged manually
* File collisions are therefore undetected until *after* Conan is run. On Unix the seemingly straightforward way of just calling `mv` silently overwrites
	* Note: As of now the generator only warns. This is because of a sizable number of packages not properly namespacing the license files. In the future this will probably turn into an exception
* It's a very generic way of integrating with other scripts and tools. But they usually expect everything to be present in the same prefix. An example of this would be CMake unable to understand that the headers and ICD loader live in two different directories unless the global search path is polluted with `CMAKE_PREFIX_PATH`.
* Sometimes you can only make a set of packages really useful by joining them. An example would be a rootfs of a Linux system, a statically linked QEMU and a script for launching the rootfs as a container
* It's not clean, but useful: Installing tools directly to `$HOME/.local`, similar to `pip install --user`.

Both `flatdeploy` and `persistent` traverse the graph of public runtime dependencies and 

## Example

```python
from conans import ConanFile

class OpenCLSDKConan(ConanFile):
    name = "opencl-sdk"
    version = "1.0"
    build_requires = "flatdeploy/0.1@"
    requires = (
    	"khronos-opencl-icd-loader/20190730@bincrafters/stable",
		"clinfo/2.2.18.04.06@mmha/stable",
	)
    generators = "flatdeploy"
```

Output:

```
$ conan install ../oclsdk
... SNIP ...
conanfile.py (opencl-sdk/1.0): Applying build-requirement: flatdeploy/0.1
Packages will be deployed to opencl-sdk-1.0
Deploying runtime dependency khronos-opencl-headers
Deploying runtime dependency khronos-opencl-icd-loader
File conflict: licenses/LICENSE is installed by both khronos-opencl-icd-loader and khronos-opencl-headers
Deploying runtime dependency clinfo
conanfile.py (opencl-sdk/1.0): Generator flatdeploy created conan_flatdeploy.txt
conanfile.py (opencl-sdk/1.0): Generator txt created conanbuildinfo.txt
conanfile.py (opencl-sdk/1.0): Generated conaninfo.txt
conanfile.py (opencl-sdk/1.0): Generated graphinfo
```

Resulting tree:

```
$ tree opencl-sdk-1.0/
opencl-sdk-1.0/
├── bin
│   └── clinfo
├── include
│   └── CL
│       ├── cl_d3d10.h
│       ├── cl_d3d11.h
│       ├── cl_dx9_media_sharing.h
│       ├── cl_dx9_media_sharing_intel.h
│       ├── cl_egl.h
│       ├── cl_ext.h
│       ├── cl_ext_intel.h
│       ├── cl_gl_ext.h
│       ├── cl_gl.h
│       ├── cl.h
│       ├── cl_platform.h
│       ├── cl_va_api_media_sharing_intel.h
│       ├── cl_version.h
│       └── opencl.h
├── lib
│   ├── libOpenCL.so -> libOpenCL.so.1
│   ├── libOpenCL.so.1 -> libOpenCL.so.1.2
│   └── libOpenCL.so.1.2
└── licenses
    ├── clinfo
    │   └── LICENSE
    └── LICENSE

6 directories, 20 files
```

The packages will be deployed to `<name>-<version>` or just `<name>` if no version is set or `conan_flatdeploy` if neither are set.
Additionally, `conan_flatdeploy.txt` contains a list of all files that were installed.

Note that `build_requirements` (typically `cmake_installer` and friends) and private `requirements` are not copied.

File permissions and extended attributes are kept. Symlinks are not followed, but copied. Make sure they are relative and relocatable!

## `persistent` Generator

`-g persistent` works exactly the same way, except that it always installs to `$HOME/.local`. The usual warnings apply: Be careful what you put in there, it's globally shared, take good care of your `conan_flatdeploy.txt` to keep the ability to uninstall the packages again.

```
[requires]
flatdeploy/0.1@
cmake_installer/3.15.2@conan/stable
ninja_installer/1.9.0@bincrafters/stable

[generators]
persistent
```

```
conan install .
```
