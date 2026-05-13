builtin_interfaces/Time timestamp

# Computed current values based on voltages from the STM board. Changes here must be 
# coordinated with the firmware and the SafetyRawVoltages message.
# The currents and is_valid values are computed from the raw voltages.
bool[10] is_valid
float32[10] currents