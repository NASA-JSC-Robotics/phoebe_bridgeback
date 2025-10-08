#!/bin/bash -e

desired_main_loop_priority=50
original_control_loop_priority=50
desired_control_loop_priority=99

ros2_control_node_pid=$(pgrep -f ros2_control_node)
if [[ -z "$ros2_control_node_pid" ]]; then
	echo "Unable to find ros2 control node process"
	exit 1
fi

# Look for a thread with the default ros controller real-time prioritization of 50
main_loop_priority=$(ps -p "$ros2_control_node_pid" -T -o tid,rtprio | grep "$ros2_control_node_pid" | awk '{print $2}')
if [[ -z "$main_loop_priority" ]]; then
	echo "I'm confused ... unable to find main thread in the ros2 control node"
	exit 1
fi

control_loop_tid=$(ps -p "$ros2_control_node_pid" -T -o tid,rtprio | awk -v prio=$original_control_loop_priority '{ if ($2 == prio) { print $1 }}' | head -1)

if [[ "$main_loop_priority" == "$desired_main_loop_priority" ]]; then
	echo "Main loop has already been re-prioritized"
else
	echo "Changing main loop priority to $desired_main_loop_priority"
	sudo chrt -f -p $desired_main_loop_priority "$ros2_control_node_pid"
fi

if [[ -z "$control_loop_tid" ]]; then
	echo "Unable to find control loop thread. Has it already been re-prioritized?"
else
	echo "Changing control loop priority thread $control_loop_tid to $desired_control_loop_priority"
	sudo chrt -f -p $desired_control_loop_priority "$control_loop_tid"
fi
