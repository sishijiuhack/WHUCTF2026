cmake_minimum_required(VERSION 3.22.1)

project(nativevm)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)
set(ANDROID_STL c++_static)

add_library(
    nativevm
    SHARED
    native_vm.cpp
)

find_library(log-lib log)

target_compile_options(
    nativevm
    PRIVATE
    -fno-exceptions
    -fno-rtti
    -fdata-sections
    -ffunction-sections
)

target_link_options(
    nativevm
    PRIVATE
    -static-libstdc++
    -Wl,--exclude-libs,ALL
    -Wl,--gc-sections
    -Wl,--strip-all
)

target_link_libraries(
    nativevm
    ${log-lib}
)
