cmake_minimum_required(VERSION 3.1)
project(test_package)

include(${CMAKE_SOURCE_DIR}/3rd/conanbuildinfo.cmake)
conan_basic_setup()

function(add_option option)
    if(${option})
        add_executable(${option} ${option}.c)
        target_link_libraries(${option} ${CONAN_LIBS})
    endif()
endfunction()

set(TEMP_NAME file_pic)
add_executable(${TEMP_NAME} file_pic.c)
target_link_libraries(${TEMP_NAME} ${CONAN_LIBS})

set(TEMP_NAME decode_audio)
add_executable(${TEMP_NAME} decode_audio.c)
target_link_libraries(${TEMP_NAME} ${CONAN_LIBS})