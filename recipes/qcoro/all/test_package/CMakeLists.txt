cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

find_package(QCoro6 REQUIRED COMPONENTS Core)
qcoro_enable_coroutines()

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} QCoro::Core
    Qt6::Core
    Qt6::Concurrent)
set_target_properties(${PROJECT_NAME} PROPERTIES CXX_STANDARD 20)
