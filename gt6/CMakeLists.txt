cmake_minimum_required(VERSION 3.20)
project(gt6_recompiled
    VERSION 0.1.0
    DESCRIPTION "Gran Turismo 6 - Static Recompilation for PC"
    LANGUAGES C CXX
)

set(CMAKE_C_STANDARD 17)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ps3recomp's Windows code calls GetCurrentThreadStackLimits (Windows 8+);
# MinGW headers only declare it when _WIN32_WINNT is new enough.
if(WIN32)
    add_compile_definitions(_WIN32_WINNT=0x0A00)
endif()

# =============================================================================
# ps3recomp runtime
# =============================================================================
set(PS3RECOMP_DIR "${CMAKE_SOURCE_DIR}/../third_party/ps3recomp-v020" CACHE PATH "Path to ps3recomp")

if(NOT EXISTS "${PS3RECOMP_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "ps3recomp not found at ${PS3RECOMP_DIR}\n"
        "Clone it from https://github.com/sp00nznet/ps3recomp\n"
        "Or set -DPS3RECOMP_DIR=/path/to/ps3recomp")
endif()

add_subdirectory(${PS3RECOMP_DIR} ps3recomp EXCLUDE_FROM_ALL)

# =============================================================================
# Lifted PPU code
# =============================================================================
# RECOMP_DIR: lifter output (ppu_recomp.h + chunks), same name as templates/project.
set(RECOMP_DIR "${CMAKE_SOURCE_DIR}/generated" CACHE PATH "Directory holding the lifter output")
get_filename_component(RECOMP_DIR "${RECOMP_DIR}" ABSOLUTE)
set(GENERATED_DIR "${RECOMP_DIR}")

file(GLOB GENERATED_SOURCES CONFIGURE_DEPENDS "${GENERATED_DIR}/ppu_recomp_*.cpp")
if(NOT GENERATED_SOURCES)
    message(FATAL_ERROR
        "No lifted sources in ${GENERATED_DIR}/.\n"
        "Run the pipeline first -- see the Building section of README.md.")
endif()
list(LENGTH GENERATED_SOURCES N_CHUNKS)
message(STATUS "lifted PPU chunks: ${N_CHUNKS}")

# The runtime library does not bundle the PPU loader/HLE/VFS translation units;
# each title compiles them so it can supply its own function_table and boot
# harness.
set(PS3RECOMP_PPU_SOURCES
    "${PS3RECOMP_DIR}/runtime/ppu/ppu_loader.cpp"   # vm + guest dispatch + traps
    "${PS3RECOMP_DIR}/runtime/ppu/ppu_hle.cpp"      # NID -> handler dispatch
    "${PS3RECOMP_DIR}/runtime/ppu/ppu_sysprx.cpp"   # boot-critical CRT
    "${PS3RECOMP_DIR}/runtime/ppu/ppu_fs.cpp"       # cellFs VFS
)

# Lifted SPU images. The four embedded SPU ELFs are ancillary cores; the WWS
# workloads themselves all pass one raw 0x2F80-byte job-manager policy module
# at guest EA 0x013FFE00 (`spu_workloads_pm.c`, image id 5). See
# docs/analysis/spu-spurs.md.
set(GT6_SPU_GEN "${CMAKE_SOURCE_DIR}/src/gen")
set(GT6_SPU_LIFT "${RECOMP_DIR}/spu_lifted")
set(GT6_SPU_SOURCES)
if(TRUE) # SPU always on
    list(APPEND GT6_SPU_SOURCES
        "${GT6_SPU_GEN}/spu_workloads.c"
        "${GT6_SPU_GEN}/spu_workloads_pm.c"
        "${GT6_SPU_GEN}/spu_workloads_jobs.c"
        "${GT6_SPU_GEN}/spu_workloads_wwsjobs.c")
    file(GLOB GT6_SPU_LIFTED CONFIGURE_DEPENDS
        "${GT6_SPU_LIFT}/*/spu_recomp.c")
    file(GLOB GT6_SPU_JOB_LIFTED CONFIGURE_DEPENDS
        "${GT6_SPU_LIFT}/jobs/*/spu_recomp.c")
    # WWS job modules (scripts/lift-spu-wwsjobs.py).
    file(GLOB GT6_SPU_WWS_LIFTED CONFIGURE_DEPENDS
        "${GT6_SPU_LIFT}/wwsjobs/*/spu_recomp.c")
    list(APPEND GT6_SPU_SOURCES ${GT6_SPU_WWS_LIFTED})
    list(LENGTH GT6_SPU_LIFTED N_SPU)
    list(LENGTH GT6_SPU_JOB_LIFTED N_SPU_JOBS)
    message(STATUS "lifted SPU images: ${N_SPU} + ${N_SPU_JOBS} runtime jobs")
    list(APPEND GT6_SPU_SOURCES ${GT6_SPU_LIFTED} ${GT6_SPU_JOB_LIFTED})
    # The lifted sources include "spu_context.h" relative to the runtime; scope
    # the include to these TUs so the huge PPU chunks keep their cached command.
    set_source_files_properties(${GT6_SPU_SOURCES} PROPERTIES
        INCLUDE_DIRECTORIES "${PS3RECOMP_DIR}/runtime/spu")
else()
    list(APPEND GT6_SPU_SOURCES
        "${CMAKE_SOURCE_DIR}/src/gen/spu_workloads_disabled.c")
endif()

add_executable(gt6
    src/main.cpp
    src/stubs.cpp
    src/gt6_present.cpp
    src/gt6_allocwatch.cpp
    src/gt6_bbcount.cpp
    src/gt6_gprof.cpp
    src/gt6_longjmp.cpp
    src/gt6_ctxfiber.cpp
    ${GT6_SPU_SOURCES}
    src/gen/ppu_hle_nids.cpp    # generated: NID -> ps3recomp lib handler
    ${PS3RECOMP_PPU_SOURCES}
    ${GENERATED_SOURCES}
)

target_include_directories(gt6 PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/src/compat      # <dirent.h>/<unistd.h> shims for ppu_fs.cpp
    ${RECOMP_DIR}                       # ppu_recomp.h
    ${PS3RECOMP_DIR}/include
    ${PS3RECOMP_DIR}/runtime/ppu
    ${PS3RECOMP_DIR}/runtime/memory
    ${PS3RECOMP_DIR}/runtime/syscalls
    ${PS3RECOMP_DIR}/runtime/spu
)

target_link_libraries(gt6 PRIVATE ps3recomp_runtime)

# LLVM-MinGW defaults to dynamic libc++/libunwind. A double-clicked gt6.exe
# then fails before main with "libc++.dll was not found" unless the toolchain
# bin directory is on PATH. Link the C++ runtime statically so the executable
# is self-contained; Windows system DLLs (D3D12, kernel32, ...) stay dynamic.
if(MINGW)
    target_link_options(gt6 PRIVATE -static)
endif()

# gt6.map resolves host addresses from [hostfault]/crash lines to symbols.
# The guest main thread runs on the process main thread. The default 1 MiB host
# stack overflows (0xC00000FD) in the 1.22 boot script: lifted calls and guest
# tail calls through ps3_indirect_call_impl nest several hundred host frames.
if(MSVC)
    target_link_options(gt6 PRIVATE /MAP /STACK:0x4000000)
endif()

if(WIN32)
    target_link_libraries(gt6 PRIVATE
        ws2_32 xinput ole32 bcrypt
        dbghelp user32 gdi32 winmm
        d3d12 dxgi dxguid d3dcompiler)
else()
    target_link_libraries(gt6 PRIVATE pthread m)
endif()

# =============================================================================
# Compiler settings
# =============================================================================
if(MSVC)
    target_compile_options(gt6 PRIVATE
        /W3
        /MP          # parallel compilation -- the lifted chunks are ~35 MB each
        /bigobj
        /utf-8
        # noise from generated code
        /wd4244 /wd4267 /wd4146 /wd4305 /wd4018)
    target_compile_definitions(gt6 PRIVATE _CRT_SECURE_NO_WARNINGS)
else()
    target_compile_options(gt6 PRIVATE
        -Wall
        -Wno-unused-variable -Wno-unused-function -Wno-unused-label
        -Wno-sign-compare -Wno-parentheses -Wno-unused-but-set-variable)
endif()

# Codegen flags the ps3recomp template sets for Clang/GCC (clang-cl included):
# the lift spells PPC arithmetic as signed C arithmetic that must wrap.
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(gt6 PRIVATE -fno-strict-aliasing -fwrapv)
endif()

# Lifted translation units: machine-generated, huge. Warnings off, no FP
# contraction (a PPC fmadd is spelt as one where the lifter means one),
# /bigobj for the 65,536-section limit on COFF.
if(MSVC)
    set_source_files_properties(${GENERATED_SOURCES} PROPERTIES COMPILE_OPTIONS "/w;/bigobj")
else()
    set_source_files_properties(${GENERATED_SOURCES} PROPERTIES COMPILE_OPTIONS "-w;-ffp-contract=off")
endif()

install(TARGETS gt6 RUNTIME DESTINATION bin)
