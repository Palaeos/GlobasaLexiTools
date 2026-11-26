# One multicall WebAssembly binary with the Apertium *runtime* processors used by
# the Globasa modes: lt-proc, cg-proc, apertium-tagger, apertium-pretransfer,
# lrx-proc, lsx-proc, apertium-anaphora, rtx-proc, and the plain-text path of the
# apertium command around them: apertium-destxt/-retxt, apertium-normalize,
# apertium-wblank-attach/-detach. One binary keeps one copy of
# ICU (Emscripten's icu port) instead of eight. Each tool's main() is renamed
# (-Dmain=<tool>_main) and multicall.cc dispatches on the first argument.
# Built by web/build_wasm.sh; sources are checked out at the commits of the
# Debian packages the pairs were compiled with, so the .bin formats match.
cmake_minimum_required(VERSION 3.16)
project(apertium_multicall CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SRC "" CACHE PATH "folder holding the checked-out sources")
set(PREFIX "" CACHE PATH "install prefix of the wasm libxml2")
set(WASM_ASSERTIONS 0 CACHE STRING "1 = runtime assertions (debugging)")

set(PORTS "--use-port=icu --use-port=boost_headers")
set(EH "-fwasm-exceptions")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${PORTS} ${EH} -O2 -w")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${EH} -O2 -w")

add_definitions(-D_GNU_SOURCE -DSIZET_NOT_CSTDINT)
# autotools-style defines for the Apertium projects only (cg3 has an enum VERSION)
set(AP_DEFS HAVE_GETOPT_LONG HAVE_DECL_GETOPT=1 HAVE_DECL_GETOPT_LONG=1 HAVE_GETOPT HAVE_SNPRINTF
    HAVE_STRING_H HAVE_UNISTD_H HAVE_ALLOCA_H HAVE_STRING_VIEW HAVE_FILESYSTEM
    PACKAGE_VERSION="wasm" PACKAGE_NAME="apertium"
    PACKAGE_STRING="apertium wasm" PACKAGE_BUGREPORT="" PACKAGE_TARNAME="apertium" VERSION="wasm")

include_directories(
  ${CMAKE_CURRENT_BINARY_DIR}/gen
  ${SRC}/lttoolbox ${SRC}/apertium ${SRC}/apertium-lex-tools/src
  ${SRC}/apertium-separable/src ${SRC}/apertium-anaphora/src ${SRC}/apertium-recursive/src
  ${SRC}/cg3/src ${SRC}/cg3/include ${SRC}/cg3/include/posix ${SRC}/cg3/include/wordexp
  ${SRC}/utfcpp/source ${SRC}/rapidjson/include ${PREFIX}/include/libxml2
  # last, so a project's own pool.h etc. wins over lttoolbox's (angled self-includes)
  ${SRC}/lttoolbox/lttoolbox ${SRC}/apertium/apertium)

# Generated config headers (autotools would write these)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium/apertium_config.h "#pragma once\n")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium_config.h "#pragma once\n")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gen/rtx_config.h "#pragma once\n")

# Library sources: every .cc/.cpp in the library folder except files with a main().
function(lib_sources out dir)
  file(GLOB files ${dir}/*.cc ${dir}/*.cpp)
  set(keep "")
  foreach(f ${files})
    file(READ ${f} body)
    string(REGEX MATCH "int[ \t\n]+main[ \t]*\\(" has_main "${body}")
    get_filename_component(name ${f} NAME)
    if(NOT has_main AND NOT name IN_LIST ARGN)
      list(APPEND keep ${f})
    endif()
  endforeach()
  set(${out} ${keep} PARENT_SCOPE)
endfunction()

lib_sources(LT ${SRC}/lttoolbox/lttoolbox check-cstdint.cc)
# tmx_* and the deformatter helpers are not used at run time by any mode
lib_sources(AP ${SRC}/apertium/apertium adapt_docx.cc wblank-mode.cc)
set(LRX ${SRC}/apertium-lex-tools/src/lrx_processor.cc)
set(LSX ${SRC}/apertium-separable/src/lsx_processor.cc)
set(ANA ${SRC}/apertium-anaphora/src/parse_arx.cc ${SRC}/apertium-anaphora/src/parse_biltrans.cc
        ${SRC}/apertium-anaphora/src/pattern_arx.cc ${SRC}/apertium-anaphora/src/score.cc)
set(RTX ${SRC}/apertium-recursive/src/rtx_processor.cc ${SRC}/apertium-recursive/src/chunk.cc)
set(CG_NAMES ApertiumApplicator BinaryApplicator BinaryGrammar BinaryGrammar_read BinaryGrammar_read_10043
  BinaryGrammar_write Cohort CohortIterator ContextualTest FSTApplicator FormatConverter Grammar
  GrammarApplicator GrammarApplicator_context GrammarApplicator_matchSet GrammarApplicator_reflow
  GrammarApplicator_runContextualTest GrammarApplicator_runGrammar GrammarApplicator_runRules
  GrammarWriter JsonlApplicator MatxinApplicator MweSplitApplicator NicelineApplicator
  PlaintextApplicator Profiler Reading Relabeller Rule Set SingleWindow Strings Tag TextualParser
  Window options uextras)
set(CG ${SRC}/cg3/include/wordexp/wordexp.cpp ${SRC}/cg3/include/posix/popen_plus.cpp)
foreach(n ${CG_NAMES})
  list(APPEND CG ${SRC}/cg3/src/${n}.cpp)
endforeach()

# Plain-text deformatter/reformatter, generated as Apertium's own Makefile does
# (xsltproc deformat.xsl / reformat.xsl txt-format.xml, then flex -Cfer).
find_program(XSLTPROC xsltproc REQUIRED)
find_program(FLEX flex REQUIRED)
foreach(pair "destxt;deformat" "retxt;reformat")
  list(GET pair 0 name)
  list(GET pair 1 xsl)
  set(l ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium_${name}.l)
  set(cc ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium_${name}.cc)
  add_custom_command(OUTPUT ${cc}
    COMMAND ${XSLTPROC} ${SRC}/apertium/apertium/${xsl}.xsl ${SRC}/apertium/apertium/txt-format.xml > ${l}
    COMMAND ${FLEX} -Cfer -P${name}_yy -o${cc} ${l}   # own prefix: two scanners in one binary
    DEPENDS ${SRC}/apertium/apertium/${xsl}.xsl ${SRC}/apertium/apertium/txt-format.xml)
endforeach()

set(MAINS
  apertium_destxt ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium_destxt.cc
  apertium_retxt ${CMAKE_CURRENT_BINARY_DIR}/gen/apertium_retxt.cc
  apertium_normalize ${SRC}/apertium/apertium/apertium_normalize.cc
  apertium_wblank_attach ${SRC}/apertium/apertium/wblank-attach.cc
  apertium_wblank_detach ${SRC}/apertium/apertium/wblank-detach.cc
  lt_proc ${SRC}/lttoolbox/lttoolbox/lt_proc.cc
  cg_proc ${SRC}/cg3/src/cg-proc.cpp
  apertium_tagger ${SRC}/apertium/apertium/apertium_tagger.cc
  apertium_pretransfer ${SRC}/apertium/apertium/apertium_pretransfer.cc
  lrx_proc ${SRC}/apertium-lex-tools/src/lrx_proc.cc
  lsx_proc ${SRC}/apertium-separable/src/lsx_proc.cc
  apertium_anaphora ${SRC}/apertium-anaphora/src/anaphora.cc
  rtx_proc ${SRC}/apertium-recursive/src/rtx_proc.cc)
# Each main() is copied to the build tree as <tool>_main() with an explicit
# "return 0;" (rename_main.py): a renamed main loses C++'s implicit return 0.
find_package(Python3 REQUIRED COMPONENTS Interpreter)
list(LENGTH MAINS n)
math(EXPR last "${n} - 1")
foreach(i RANGE 0 ${last} 2)
  math(EXPR j "${i} + 1")
  list(GET MAINS ${i} tool)
  list(GET MAINS ${j} file)
  get_filename_component(ext ${file} EXT)
  set(out ${CMAKE_CURRENT_BINARY_DIR}/gen/${tool}_main${ext})
  set(iso "")
  if(tool STREQUAL "apertium_destxt" OR tool STREQUAL "apertium_retxt")
    set(iso --isolate)     # the two flex scanners share non-static globals
  endif()
  add_custom_command(OUTPUT ${out}
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/rename_main.py ${file} ${out} ${tool}_main ${iso}
    DEPENDS ${file} ${CMAKE_CURRENT_SOURCE_DIR}/rename_main.py)
  set(MAIN_${tool} ${out})
endforeach()

# libstdc++'s std::sort where values with ties are sorted (gnu_sort.hpp): the order of
# equal elements must be the native one, or later first-reading choices change.
set_source_files_properties(${SRC}/lttoolbox/lttoolbox/state.cc ${LRX}
  PROPERTIES COMPILE_OPTIONS "-include;${CMAKE_CURRENT_SOURCE_DIR}/gnu_sort.hpp")

add_library(lt STATIC ${LT} ${MAIN_lt_proc})
add_library(ap STATIC ${AP} ${MAIN_apertium_tagger} ${MAIN_apertium_pretransfer}
  ${MAIN_apertium_destxt} ${MAIN_apertium_retxt} ${MAIN_apertium_normalize}
  ${MAIN_apertium_wblank_attach} ${MAIN_apertium_wblank_detach})
add_library(extra STATIC ${LRX} ${LSX} ${ANA} ${RTX}
  ${MAIN_lrx_proc} ${MAIN_lsx_proc} ${MAIN_apertium_anaphora} ${MAIN_rtx_proc})
add_library(cg STATIC ${CG} ${MAIN_cg_proc})
# profiling writes SQLite; not needed in the browser
target_compile_definitions(cg PRIVATE DISABLE_PROFILING)
foreach(t lt ap extra)
  target_compile_definitions(${t} PRIVATE ${AP_DEFS})
endforeach()

add_executable(apertium ${CMAKE_CURRENT_SOURCE_DIR}/multicall.cc)
set_target_properties(apertium PROPERTIES SUFFIX ".mjs")
target_link_libraries(apertium extra ap lt cg ${PREFIX}/lib/libxml2.a)
separate_arguments(PORTS_LIST UNIX_COMMAND "${PORTS}")
target_link_options(apertium PRIVATE ${PORTS_LIST} ${EH}
  -sMODULARIZE=1 -sEXPORT_ES6=1 -sEXPORT_NAME=createApertium
  -sENVIRONMENT=web,worker -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=8388608
  -sINVOKE_RUN=0 -sEXIT_RUNTIME=1 -sFORCE_FILESYSTEM=1 -sWASM_ASYNC_COMPILATION=0
  -sEXPORT_EXCEPTION_HANDLING_HELPERS=1 -sASSERTIONS=${WASM_ASSERTIONS}
  -sEXPORTED_RUNTIME_METHODS=callMain,FS,ENV,getExceptionMessage -O2)
