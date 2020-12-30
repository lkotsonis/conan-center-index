from conans import ConanFile, CMake, tools
import os


class JUCEConan(ConanFile):
    name = "juce"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    generators = "cmake_find_package"

    def source(self):
        git = tools.Git(folder="JUCE")
        git.clone("https://github.com/juce-framework/JUCE.git")
        git.checkout(self.version)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.configure(source_folder="JUCE")
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
