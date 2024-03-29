#!/usr/bin/env python
# ##### BEGIN GPL LICENSE BLOCK #####
#
# Copyright (C) 2021  Patrick Baus
#
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####
"""
The lab temperature controller uses a PID controller and the Tinkerforge sensors to regulate
the room temperature.
"""
from __future__ import annotations

import asyncio
import logging
import signal
import warnings
from contextlib import AsyncExitStack
from decimal import Decimal
from typing import TypedDict, cast

from aiostream import pipe, stream
from decouple import UndefinedValueError, config
from labnode_async import FeedbackDirection
from labnode_async import IPConnection as LabnodeIPConnection
from labnode_async import PidController
from tinkerforge_async import IPConnectionAsync
from tinkerforge_async.bricklet_temperature import BrickletTemperature
from tinkerforge_async.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge_async.ip_connection_helper import base58decode, base58encode

from _version import __version__


class PidParameters(TypedDict):
    """The PID controller parameters for each of the integrated PID controllers."""

    kp: float
    ki: float
    kd: float
    setpoint: float


class PidConfig(TypedDict):
    """The PID controller configuration as read from the os environment."""

    primary_pid: PidParameters
    secondary_pid: PidParameters
    timeout: float
    enable_gain: bool
    enable_autoresume: bool
    update_interval: float  # in s


class Controller:
    """
    Main daemon, that runs in the background and monitors all sensors. It will
    configure them according to options set in the database and then place the
    returned data in the database as well.
    """

    def __init__(self):
        """
        Creates a sensorDaemon object.
        """
        self.__logger = logging.getLogger(__name__)

    async def tinkerforge_producer(
        self, ipcon: IPConnectionAsync, sensor_uid: int, interval: float, output_queue: asyncio.Queue[Decimal]
    ) -> None:
        """
        Enumerate the brick, search for our sensor and query its data.

        Parameters
        ----------
        ipcon: IPConnectionAsync
            The ip connection used by the brick
        sensor_uid: int
            The id of the temperature sensor
        interval: float
            The number of seconds to wait in between queries
        output_queue: Queue of Decimal
            A queue that hold the temperature values in Kelvin
        """
        await ipcon.enumerate()
        sensor: BrickletTemperature | BrickletTemperatureV2 | None = None
        async for _, device in ipcon.read_enumeration():
            if device.uid == sensor_uid:
                sensor = device
                self.__logger.info(
                    "Found Tinkerforge sensor %i (%s) at '%s:%i",
                    sensor_uid,
                    base58encode(sensor_uid),
                    ipcon.hostname,
                    ipcon.port,
                )
                break
        # Once we have the sensor, read it at the configured interval
        if sensor:
            data_stream = stream.call(sensor.get_temperature) | pipe.cycle() | pipe.spaceout(interval)
            async with data_stream.stream() as streamer:
                async for item in streamer:
                    output_queue.put_nowait(item)

    @staticmethod
    async def labnode_consumer(
        controller: PidController, pid_config: PidConfig, input_queue: asyncio.Queue[Decimal]
    ) -> None:
        """
        Configures the PID controller and feeds it new input values using the input queue.

        Parameters
        ----------
        controller: PidController
            The PID controller to feed
        pid_config: PidConfig
            A dict containing the controller config
        input_queue: Queue of Decimal
            The input queue containing new input values for the PID controller
        """
        # configure the PID controller
        await asyncio.gather(
            controller.set_lower_output_limit(0),
            controller.set_upper_output_limit(0xFFF),  # 12-bit DAC
            controller.set_dac_gain(pid_config["enable_gain"]),  # Enable 10 V output (Gain x2)
            controller.set_timeout(pid_config["timeout"]),  # time in seconds
            controller.set_pid_feedback_direction(FeedbackDirection.NEGATIVE),
            controller.set_auto_resume(pid_config["enable_autoresume"]),
            controller.set_secondary_pid_update_interval(pid_config["update_interval"]),  # time in seconds
            # Those values need some explanation:
            # The target is an unsigned Qm.n 32-bit number, which is positive (>=0) See this link
            # for details: https://en.wikipedia.org/wiki/Q_%28number_format%29
            # To determine m and n, we need to look at the desired output. The output is a 12 bit DAC.
            # The PID basically does input * kp -> output, which should be a 12 bit number (Q12.20)
            # The source sensor (Tinkerforge) has a temperature range of -40 °C to 125 °C
            # (Temperature Bricklet v1), so this makes 165 K, we normalize this to 1 (/165).
            # The input sensor (e.g. STS3x, Temperature Bricklet v2) has 16 bits of resolution (/2**16)
            # and must be scaled to fit the output (*2**20).
            # The whole calculation with units:
            # K is Kelvin, s is seconds
            # conversion:
            # kp: dac_bit_values / K * 165 / 2**16 (adc_bit_values / K) in Q12.20 notation
            # ki: dac_bit_values / (K s) * 165 / 2**16 (adc_bit_values / K) in Q12.20 notation
            # kd: dac_bit_values * s / K * 165 / 2**16 (adc_bit_values / K) in Q12.20 notation
            controller.set_kp(pid_config["primary_pid"]["kp"] * 165 / 2**16 * 2**20, config_id=0),
            controller.set_ki(pid_config["primary_pid"]["ki"] * 165 / 2**16 * 2**20, config_id=0),
            controller.set_kd(pid_config["primary_pid"]["kd"] * 165 / 2**16 * 2**20, config_id=0),
            # To ensure the input is always positive, we add 40 K
            controller.set_setpoint(
                max(int((pid_config["primary_pid"]["setpoint"] + 40) / 165 * 2**16), 0), config_id=0
            ),
            # And the configuration for the secondary PID
            controller.set_kp(pid_config["secondary_pid"]["kp"] * 165 / 2**16 * 2**20, config_id=1),
            controller.set_ki(pid_config["secondary_pid"]["ki"] * 165 / 2**16 * 2**20, config_id=1),
            controller.set_kd(pid_config["secondary_pid"]["kd"] * 165 / 2**16 * 2**20, config_id=1),
            controller.set_setpoint(
                max(int((pid_config["secondary_pid"]["setpoint"] + 40) / 165 * 2**16), 0), config_id=1
            ),
            controller.set_enabled(True),
            controller.set_secondary_config(1),  # Set the secondary PID controller to use config #1
        )
        # Now pull the data from the input queue and feed it to the PID controller
        data_stream = stream.call(input_queue.get) | pipe.cycle()
        async with data_stream.stream() as streamer:
            async for item in streamer:
                # The queued items are temperature values in K,
                # so we need to convert them to the units of the PID as detailed above
                await controller.set_input(int((item - Decimal("273.15") + 40) / 165 * 2**16), return_output=False)

    async def run(self) -> None:  # pylint: disable=too-many-locals
        """
        Start the daemon and keep it running through the while (True)
        loop. Execute shutdown() to kill it.
        """
        self.__logger.warning("#################################################")
        self.__logger.warning("Starting Daemon v%s...", __version__)
        self.__logger.warning("#################################################")

        # Catch signals and shutdown
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for sig in signals:
            asyncio.get_running_loop().add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # Read either environment variable, settings.ini or .env file
        try:
            controller_host = config("CONTROLLER_IP")
            controller_port = config("CONTROLLER_PORT", cast=int, default=4223)
            sensor_host = config("SENSOR_IP")
            sensor_port = config("SENSOR_PORT", cast=int, default=4223)
            sensor_uid = config("SENSOR_UID")
            try:
                sensor_uid = int(sensor_uid)
            except ValueError:
                # We need to convert the value from base58 encoding to an integer
                sensor_uid = base58decode(sensor_uid)

            pid_config: PidConfig = {
                "primary_pid": {
                    "kp": config("PRIMARY_PID_KP", cast=float),
                    "ki": config("PRIMARY_PID_KI", cast=float),
                    "kd": config("PRIMARY_PID_KD", cast=float),
                    "setpoint": config("PRIMARY_PID_SETPOINT", cast=float),
                },
                "secondary_pid": {
                    "kp": config("SECONDARY_PID_KP", cast=float),
                    "ki": config("SECONDARY_PID_KI", cast=float),
                    "kd": config("SECONDARY_PID_KD", cast=float),
                    "setpoint": config("SECONDARY_PID_SETPOINT", cast=float),
                },
                "update_interval": config("PID_INTERVAL", cast=float),
                "timeout": config("PID_TIMEOUT", cast=float),
                "enable_gain": config("OUTPUT_ENABLE_GAIN", cast=bool, default=True),
                "enable_autoresume": config("AUTO_RESUME", cast=bool, default=True),
            }
        except UndefinedValueError as exc:
            self.__logger.error("Environment variable undefined: %s", exc)
            return

        async with AsyncExitStack() as stack:
            tasks: set[asyncio.Task] = set()
            stack.push_async_callback(self.cancel_tasks, tasks)
            message_queue: asyncio.Queue[Decimal] = asyncio.Queue()

            self.__logger.info("Connecting consumer to Labnode at '%s:%i", controller_host, controller_port)
            controller = await stack.enter_async_context(
                LabnodeIPConnection(hostname=controller_host, port=controller_port)
            )
            self.__logger.info("Connected to Labnode at '%s:%i", controller_host, controller_port)
            consumer = asyncio.create_task(
                self.labnode_consumer(cast(PidController, controller), pid_config, message_queue)
            )
            tasks.add(consumer)

            # Start the Tinkerforge data producer
            self.__logger.info("Connecting producer to Tinkerforge brick at '%s:%i", sensor_host, sensor_port)
            ipcon = await stack.enter_async_context(IPConnectionAsync(host=sensor_host, port=sensor_port))
            self.__logger.info("Connected to Tinkerforge brick at '%s:%i", sensor_host, sensor_port)
            task = asyncio.create_task(
                self.tinkerforge_producer(ipcon, sensor_uid, pid_config["update_interval"], message_queue)
            )
            tasks.add(task)

            await asyncio.gather(*tasks)

    async def shutdown(self) -> None:
        """
        Stops the daemon and gracefully disconnect from all clients.
        """
        self.__logger.warning("#################################################")
        self.__logger.warning("Stopping Daemon...")
        self.__logger.warning("#################################################")

        # Get all running tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        # and stop them
        [task.cancel() for task in tasks]  # pylint: disable=expression-not-assigned
        # finally wait for them to terminate
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        except Exception:  # pylint: disable=broad-except
            # We want to catch all exceptions on shutdown, except the asyncio.CancelledError
            # The exception will then be printed using the logger
            self.__logger.exception("Error while reaping tasks during shutdown")

    @staticmethod
    async def cancel_tasks(tasks) -> None:
        """Cancel all remaining tasks and wait for their completion."""
        for task in tasks:
            if task.done():
                continue
            task.cancel()
        for task in tasks:
            if task.done():
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass


async def main() -> None:
    """
    The main (infinite) loop, that runs until the controller has shut down.
    """
    daemon = Controller()
    try:
        await daemon.run()
    except asyncio.CancelledError:
        # Swallow that error, because this is the root task, there is nothing
        # cancel above it.
        pass


# Report all mistakes managing asynchronous resources.
warnings.simplefilter("always", ResourceWarning)
logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,  # Enable logs from the ip connection. Set to debug for even more info
    datefmt="%Y-%m-%d %H:%M:%S",
)

asyncio.run(main(), debug=True)
