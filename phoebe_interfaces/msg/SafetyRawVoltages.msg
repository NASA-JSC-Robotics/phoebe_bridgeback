builtin_interfaces/Time timestamp

# Raw values from the STM board. Changes here must be coordinated with the firmware.
# The firmware provides NUM_FIRMWARE_VALUES over the wire, corresponding to the number
# of physical sensors. However, some physical sensors may not currently be connected,
# or may have failed, and these values should be reported as zeroes with their 
# is_valid[] entry set to false.
int8 NUM_FIRMWARE_VALUES=10
bool[10] is_valid [true, true, true, true, true, true, true, true, true, false]
float32[10] voltages
