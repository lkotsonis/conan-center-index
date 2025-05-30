from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.files import get, copy, rmdir, replace_in_file, export_conandata_patches, apply_conandata_patches
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os

required_conan_version = ">=1.54.0"

class TrantorConan(ConanFile):
    name = "trantor"
    description = "a non-blocking I/O tcp network lib based on c++14/17"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/an-tao/trantor"
    topics = ("tcp-server", "asynchronous-programming", "non-blocking-io")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "with_c_ares": [True, False],
        "with_spdlog": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "with_c_ares": True,
        "with_spdlog": False,
        "spdlog/*:header_only": True,
    }

    @property
    def _min_cppstd(self):
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "15",
            "msvc": "191",
            "clang": "5",
            "apple-clang": "10",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "1.5.15":
            del self.options.with_spdlog
            del self.default_options["spdlog/*:header_only"]

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openssl/[>=1.1 <4]")
        if self.options.with_c_ares:
            self.requires("c-ares/1.25.0")
        if self.options.get_safe("with_spdlog"):
            self.requires("spdlog/1.13.0")

    def validate(self):
        if self.info.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)

        minimum_version = self._compilers_minimum_version.get(str(self.info.settings.compiler), False)
        if minimum_version and Version(self.info.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        # TODO: Compilation succeeds, but execution of test_package fails on Visual Studio with MDd
        if is_msvc(self) and self.options.shared and "MDd" in msvc_runtime_flag(self):
            raise ConanInvalidConfiguration(f"{self.ref} does not support the MDd runtime on Visual Studio.")

        if self.options.get_safe("with_spdlog") and not self.dependencies["spdlog"].options.header_only:
            raise ConanInvalidConfiguration(f"{self.ref} requires header_only spdlog.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # TODO: support other tls providers
        tc.variables["TRANTOR_USE_TLS"] = "openssl"
        tc.variables["BUILD_C-ARES"] = self.options.with_c_ares
        tc.variables["USE_SPDLOG"] = self.options.get_safe("with_spdlog")
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        # fix c-ares imported target
        replace_in_file(self, cmakelists, "c-ares_lib", "c-ares::cares")
        # Cleanup rpath in shared lib
        replace_in_file(self, cmakelists, "set(CMAKE_INSTALL_RPATH \"${CMAKE_INSTALL_PREFIX}/${INSTALL_LIB_DIR}\")", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Trantor")
        self.cpp_info.set_property("cmake_target_name", "Trantor::Trantor")
        self.cpp_info.libs = ["trantor"]

        self.cpp_info.requires = ["openssl::ssl", "openssl::crypto"]

        if self.options.with_c_ares:
            self.cpp_info.requires.append("c-ares::cares")
        if self.options.get_safe("with_spdlog"):
            self.cpp_info.requires.append("spdlog::spdlog_header_only")

        if self.settings.os == "Windows":
            self.cpp_info.system_libs.append("ws2_32")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("m")

        #  TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "Trantor"
        self.cpp_info.names["cmake_find_package_multi"] = "Trantor"
