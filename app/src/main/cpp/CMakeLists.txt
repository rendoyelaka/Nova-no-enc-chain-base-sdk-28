cmake_minimum_required(VERSION 3.22.1)
project("companionguard")

# OPENSSL_ANDROID_ROOT is resolved per-ABI automatically using ANDROID_ABI
# which is set by the Android CMake toolchain before this file runs.
# Layout expected under app/:
#   third_party/openssl/<ABI>/include/
#   third_party/openssl/<ABI>/lib/libcrypto.a

set(OPENSSL_ABI_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../third_party/openssl/${ANDROID_ABI}")
set(OPENSSL_INCLUDE  "${OPENSSL_ABI_ROOT}/include")
set(OPENSSL_CRYPTO   "${OPENSSL_ABI_ROOT}/lib/libcrypto.a")

if(NOT EXISTS "${OPENSSL_CRYPTO}")
    message(FATAL_ERROR "libcrypto.a not found at ${OPENSSL_CRYPTO}")
endif()

add_library(companionguard SHARED companion_decrypt.cpp)

target_include_directories(companionguard PRIVATE "${OPENSSL_INCLUDE}")

find_library(log-lib log)

target_link_libraries(companionguard "${OPENSSL_CRYPTO}" ${log-lib})

target_compile_options(companionguard PRIVATE
    -O2
    -fstack-protector-strong
    -fvisibility=hidden
    -ffunction-sections
    -fdata-sections
)

target_link_options(companionguard PRIVATE
    -Wl,--gc-sections
    -Wl,-s
    -Wl,--exclude-libs,ALL
)
