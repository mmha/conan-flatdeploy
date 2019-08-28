import os
import shutil
from distutils import dir_util, file_util
from conans import ConanFile, tools
from conans.model import Generator
from colorama import Fore, Style


class abstract_flatdeploy(Generator):
    @property
    def installation_prefix(self):
        raise NotImplementedError

    @property
    def filename(self):
        return "conan_flatdeploy.txt"

    def remove_prefix(self, prefix):
        dir_util.remove_tree(prefix)

    @property
    def content(self):
        copied_files = {}
        seen_deps = []

        deploybase = os.path.join(self.output_path, self.installation_prefix)
        deploymanifest = os.path.join(self.output_path, self.filename)

        print(
            f"{Fore.GREEN}Packages will be deployed to {self.installation_prefix}{Style.RESET_ALL}"
        )

        if os.path.exists(deploybase):
            self.remove_prefix(deploybase)
        deploymanifest = os.path.join(self.output_path, self.filename)
        if os.path.exists(deploymanifest):
            os.remove(deploymanifest)

        for req in self.conanfile.requires:
            if req in seen_deps:
                continue
            seen_deps.append(req)
            self._deploy_dependency(req, self.conanfile.deps_cpp_info[req],
                                    copied_files, deploybase, deploymanifest,
                                    seen_deps)

        return "\n".join(copied_files.keys()) + '\n'

    def _deploy_dependency(self, depname, cpp_info, copied_files, deploybase,
                           deploymanifest, seen_deps):
        for dep in cpp_info.public_deps:
            if dep in seen_deps:
                continue
            seen_deps.append(dep)
            self._deploy_dependency(dep, self.conanfile.deps_cpp_info[dep],
                                    copied_files, deploybase, deploymanifest,
                                    seen_deps)

        print(
            f"{Fore.GREEN}Deploying runtime dependency {depname}{Style.RESET_ALL}"
        )

        try:
            rootpath = self.conanfile.deps_cpp_info[depname].rootpath
            for root, _, files in os.walk(os.path.normpath(rootpath)):
                for f in files:
                    if f in [
                            "conaninfo.txt", "conanmanifest.txt",
                            "conan_package.tgz"
                    ]:
                        continue
                    src = os.path.normpath(os.path.join(root, f))
                    dstbase = os.path.join(deploybase,
                                           os.path.relpath(root, rootpath))
                    dst = os.path.normpath(os.path.join(dstbase, f))
                    dir_util.mkpath(dstbase)
                    if os.path.exists(dst):
                        conflict = os.path.relpath(src, rootpath)
                        if dst in copied_files:
                            print(
                                f"{Fore.YELLOW}File conflict: {conflict} is installed by both {depname} and {copied_files[dst]}{Style.RESET_ALL}"
                            )
                        else:
                            print(
                                f"{Fore.YELLOW}File conflict: {conflict} exists already"
                            )
                    shutil.copy2(src, dst, follow_symlinks=False)
                    copied_files[dst] = depname
        except:
            self.remove_prefix(deploybase)
            raise


class flatdeploy(abstract_flatdeploy):
    @property
    def installation_prefix(self):
        dirname = self.conanfile.name
        if dirname is None:
            return "conan_flatdeploy"
        if self.conanfile.version is not None:
            dirname += "-" + self.conanfile.version
        return dirname


class persistent(abstract_flatdeploy):
    @property
    def installation_prefix(self):
        return os.path.join(tools.get_env("HOME"), ".local")

    def remove_prefix(self, prefix):
        pass


class FlatdeployGeneratorPackageConan(ConanFile):
    name = "flatdeploy"
    version = "0.1"
    description = "Deploy generator that puts runtime dependencies in a single directory"
    url = "https://github.com/mmha/conan-flatdeploy"
    license = "MIT"
    author = "Morris Hafner"
