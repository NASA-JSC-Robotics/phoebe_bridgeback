builtin_interfaces/Time timestamp

# Computed current values based on voltages from the STM board. Changes here must be
# coordinated with the firmware and the RawVoltages message.
# The currents and is_valid values are computed from the raw voltages.
int8 NUM_FIRMWARE_VALUES=10
bool[10] is_valid
string[10] names
float32[10] currents
float32[10] raw_voltages
