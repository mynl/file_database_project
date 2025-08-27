# disk_info.py
"""
Get information about physical storage devices.
"""

from __future__ import annotations

from collections import namedtuple
from typing import Tuple

import pandas as pd
import wmi


class DriveInfo():
    """Class to extract and maintain drive information."""

    trimmed_fields = [
        "LogicalDrive-VolumeSerialNumber",  # filesystem-level ID
        "Drive-SerialNumber",               # most unique ID
        "Drive-Model",                      # helps in debugging duplicates
        "Drive-InterfaceType",              # removable vs fixed
        "Drive-Size",                       # good for sanity checking

    ]

    def __init__(self):
        """Logical drive to partition to drive with extra information."""
        self.c = wmi.WMI()
        rows = []
        for ld in self.c.Win32_LogicalDisk():
            for part in ld.associators("Win32_LogicalDiskToPartition"):
                for disk in part.associators("Win32_DiskDriveToDiskPartition"):
                    rows.append(
                        {
                            "Drive-Caption": disk.Caption,
                            "Drive-Description": disk.Description,
                            "Drive-DeviceID": disk.DeviceID,
                            "Drive-InterfaceType": disk.InterfaceType,
                            "Drive-MediaType": disk.MediaType,
                            "Drive-Model": disk.Model,
                            "Drive-Name": disk.Name,
                            "Drive-Partitions": disk.Partitions,
                            "Drive-SerialNumber": disk.SerialNumber,
                            "Drive-Signature": disk.Signature,
                            "Drive-Size": disk.Size,
                            "Partition-DeviceID": part.DeviceID,
                            "Partition-Description": part.Description,
                            "LogicalDrive-DeviceID": ld.DeviceID,
                            "LogicalDrive-Description": ld.Description,
                            "LogicalDrive-FileSystem": ld.FileSystem,
                            "LogicalDrive-VolumeName": ld.VolumeName,
                            "LogicalDrive-VolumeSerialNumber": ld.VolumeSerialNumber,
                        }
                    )
        self._data = pd.DataFrame(rows).set_index("LogicalDrive-DeviceID")

    @property
    def data(self):
        """Return full dataframe."""
        return self._data

    @property
    def trim_data(self):
        """Return trimmed dataframe."""
        return self._data[self.trimmed_fields]

    def drive_letter_id(self, letter: str) -> Tuple[str, str, str]:
        """
        Return (VolumeSerialNumber, Drive-Model, Drive-SerialNumber) for a drive letter.

        Safe: returns ('','','') if the letter isn't present.
        """
        try:
            ser, model, drvser = self._data.loc[
                letter, ["LogicalDrive-VolumeSerialNumber", "Drive-Model", "Drive-SerialNumber"]
            ]
            return str(ser), str(model), str(drvser)
        except Exception:
            return "", "", ""


def _all_properties(obj):
    """Get all the properties of object in a dict."""
    return {p: getattr(obj, p) for p in obj._properties}


def get_all_drives_info(subset: bool = False):
    """Database of attached drives."""
    c = wmi.WMI()

    drive_fields = [
        "Caption",
        "Description",
        "DeviceID",
        "InterfaceType",
        "MediaType",
        "Model",
        "Name",
        "Partitions",
        "SerialNumber",
        "Signature",
        "Size",
    ]

    drives = []
    partitions = []
    logical_disks = []

    for disk in c.Win32_DiskDrive():
        drives.append(_all_properties(disk))
        for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
            partitions.append(_all_properties(partition))
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                logical_disks.append(_all_properties(logical_disk))

    drives = pd.DataFrame(drives)
    partitions = pd.DataFrame(partitions)
    logical_disks = pd.DataFrame(logical_disks)

    if subset:
        drives = drives[drive_fields]

    DiskInfo = namedtuple("DiskInfo", "drives, partitions, logical_disks")
    ans = DiskInfo(drives, partitions, logical_disks)
    return ans
