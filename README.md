# UE4 Packaged Build Disk Utilisation Visualisation

![](Docs/Images/sunburstdiagram.png)

Use this simple script as a step in your CI tool of choice. The tool will generate a sunburst diagram of the disk utilization of packaged UE4 builds for either Win64 or Android platforms.

# Synopsis

    ./pak-viz.py --help

    ./pak-viz.py ExampleBuild my-dest-dir

    ./pak-viz.py ExampleBuild my-dest-dir --unreal_pak U:/bin/UnrealPak.exe

# Example diagram in CI

![](Docs/Images/SunBurstImageExample.png)
