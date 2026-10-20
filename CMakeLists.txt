# This file is the Zephyr module entry point. `make setup` passes the repo
# root as ZMK_EXTRA_MODULES, so the ZMK app compiles the instant-hold behavior
# in alongside the shields.
target_sources(app PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/behaviors/behavior_instant_hold.c)
