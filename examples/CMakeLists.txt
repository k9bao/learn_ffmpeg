cmake_minimum_required(VERSION 3.10)

# set the project name
project(helloword)

add_definitions(-DCMAKE_OSX_ARCHITECTURES=i386) 

SET(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g -ggdb -Wl,-rpath=./:./lib:./lib/build/lib") #-Wl,-rpath=./
SET(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O3 -Wl,-rpath=./:./lib") #-Wall

set(FF_PATH /Users/tianwenhui/.conan/data/ffmpeg/4.2.1/demo/testing/package/06b344da6911e66ea61bf801110358f17e58e82e)
# add the executable
add_executable(${PROJECT_NAME} decode_video.c)
set(FFMPEG_LIBS avdevice avformat avfilter avcodec swresample swscale avutil)
target_include_directories(${PROJECT_NAME} PRIVATE ${FF_PATH}/include)
target_link_directories(${PROJECT_NAME} PRIVATE ${FF_PATH}/lib)
target_link_libraries(${PROJECT_NAME} ${FFMPEG_LIBS})
