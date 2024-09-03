import logging
from bleak import BleakClient, BleakScanner
from typing import Tuple, List
from bitstring import BitArray

from pydglab.model import *
from pydglab.uuid import *

logger = logging.getLogger(__name__)


async def scan():
    """
    Scan for DGLAB v2.0 devices and return a list of tuples with the address and the RSSI of the devices found.

    Returns:
        List[Tuple[str, int]]: (address, RSSI)
    """
    devices = await BleakScanner().discover(return_adv=True)
    dglab_v2: List[Tuple[str, int]] = []
    for i, j in devices.values():
        if j.local_name == CoyoteV2.name and i.address is not None:
            logger.info(f"Found DGLAB v2.0 {i.address}")
            dglab_v2.append((i.address, j.rssi))
    if not dglab_v2:
        logger.error("No DGLAB v2.0 found")
    return dglab_v2


async def scan_():
    dglab_v2 = await scan()
    if not dglab_v2:
        raise Exception("No DGLAB v2.0 found")
    if len(dglab_v2) > 1:
        logger.warning("Multiple DGLAB v2.0 found, chosing the closest one")
    elif len(dglab_v2) == 0:
        raise Exception("No DGLAB v2.0 found")
    return sorted(dglab_v2, key=lambda device: device[1])[0][0]


async def get_batterylevel_(client: BleakClient, characteristics: CoyoteV2 | CoyoteV3):
    r = await client.read_gatt_char(characteristics.characteristicBattery)
    return r


async def get_strength_(client: BleakClient, characteristics: CoyoteV2 | CoyoteV3):
    r = await client.read_gatt_char(characteristics.characteristicEStimPower)
    # logger.debug(f"Received strenth bytes: {r.hex()} , which is {r}")
    r.reverse()
    r = BitArray(r).bin
    # logger.debug(f"Received strenth bytes after decoding: {r}")
    return int(r[-22:-11], 2) / 11, int(r[-11:], 2) / 11


async def set_strength_(
    client: BleakClient, value: Coyote, characteristics: CoyoteV2 | CoyoteV3
):
    # Create a byte array with the strength values.
    # The values are multiplied by 11 to convert them to the correct range.
    strengthA = int(value.ChannelA.strength) * 11
    strengthB = int(value.ChannelB.strength) * 11
    if (
        value.ChannelA.strength is None
        or value.ChannelA.strength < 0
        or value.ChannelA.strength > 2047
    ):
        value.ChannelA.strength = 0
    if (
        value.ChannelB.strength is None
        or value.ChannelB.strength < 0
        or value.ChannelB.strength > 2047
    ):
        value.ChannelB.strength = 0

    array = ((strengthA << 11) + strengthB).to_bytes(3, byteorder="little")

    # logger.debug(f"Sending bytes: {array.hex()} , which is {array}")

    r = await client.write_gatt_char(
        characteristics.characteristicEStimPower, bytearray(array), response=False
    )
    return value.ChannelA.strength, value.ChannelB.strength


async def set_wave_(
    client: BleakClient,
    value: ChannelA | ChannelB,
    characteristics: CoyoteV2 | CoyoteV3,
):
    # Create a byte array with the wave values.
    array = ((value.waveZ << 15) + (value.waveY << 5) + value.waveX).to_bytes(
        3, byteorder="little"
    )

    # logger.debug(f"Sending bytes: {array.hex()} , which is {array}")

    r = await client.write_gatt_char(
        (
            characteristics.characteristicEStimA
            if type(value) is ChannelA
            else characteristics.characteristicEStimB
        ),
        bytearray(array),
        response=False,
    )
    return value.waveX, value.waveY, value.waveZ


async def set_wave_sync_(
    client: BleakClient, value: Coyote, characteristics: CoyoteV2 | CoyoteV3
):
    # Create a byte array with the wave values.
    binArrayA = (
        "0b0000"
        + "{0:05b}".format(value.ChannelA.waveZ)
        + "{0:010b}".format(value.ChannelA.waveY)
        + "{0:05b}".format(value.ChannelA.waveX)
    )
    arrayA = bytearray(BitArray(bin=binArrayA).tobytes())

    binArrayB = (
        "0b0000"
        + "{0:05b}".format(value.ChannelB.waveZ)
        + "{0:010b}".format(value.ChannelB.waveY)
        + "{0:05b}".format(value.ChannelB.waveX)
    )
    arrayB = bytearray(BitArray(bin=binArrayB).tobytes())

    r = await client.write_gatt_char(
        characteristics.characteristicEStimA, arrayA
    ), await client.write_gatt_char(characteristics.characteristicEStimB, arrayB)
    return (value.ChannelA.waveX, value.ChannelA.waveY, value.ChannelA.waveZ), (
        value.ChannelB.waveX,
        value.ChannelB.waveY,
        value.ChannelB.waveZ,
    )
