# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
# Copyright (C) 2015  Patrick Baus
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# aint with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

from enum import IntEnum, unique

# PID controller commands
@unique
class MessageType(IntEnum):
    set_input = 0
    set_kp = 1
    set_ki = 2
    set_kd = 3
    set_lower_output_limit = 4
    set_upper_output_limit = 5
    set_enable = 6
    set_timeout = 7
    set_direction = 8
    set_setpoint = 9
    set_output = 10
    get_version = 11
    get_serial = 12
    get_device_type = 13
    set_gain = 14
    callback_update_value = 15
    sequence_number = 23
    error_invalid_format = 251

@unique
class MessageCode(IntEnum):
    messageAck = 249
    error_invalid_mode = 250
    error_invalid_command = 252
    warning_deprecated = 255

@unique
class DeviceType(IntEnum):
    pid_controller = 0
