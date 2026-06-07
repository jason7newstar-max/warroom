cmake_minimum_required(VERSION 3.22)
project(PhantomNative VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG        8.0.13
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(JUCE)

juce_add_console_app(PhantomNative PRODUCT_NAME "PhantomNative")
target_sources(PhantomNative PRIVATE Source/Main.cpp)

target_compile_definitions(PhantomNative PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_STANDALONE_APPLICATION=1)

target_link_libraries(PhantomNative PRIVATE
    juce::juce_audio_devices
    juce::juce_audio_formats
    juce::juce_dsp
    juce::juce_recommended_config_flags
    juce::juce_recommended_warning_flags)

# Embed an Info.plist into the CLI Mach-O so macOS sees NSMicrophoneUsageDescription
# (without it the mic is silently blocked and the input IOProc never fires).
target_link_options(PhantomNative PRIVATE
    "-Wl,-sectcreate,__TEXT,__info_plist,${CMAKE_CURRENT_SOURCE_DIR}/Info.plist")
