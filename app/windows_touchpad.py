import ctypes
import os
from ctypes import wintypes


PT_TOUCHPAD = 5
WM_INPUT = 0x00FF
WM_POINTERUPDATE = 0x0245
WM_POINTERDOWN = 0x0246
WM_POINTERUP = 0x0247
WM_POINTERCAPTURECHANGED = 0x024C

RIDI_PREPARSEDDATA = 0x20000005
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000B
RID_INPUT = 0x10000003
RIM_TYPEHID = 2
HIDP_STATUS_SUCCESS = 0x00110000

_user32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None
_hid = ctypes.WinDLL("hid", use_last_error=True) if os.name == "nt" else None


class _Point(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _PointerInfo(ctypes.Structure):
    _fields_ = [
        ("pointerType", ctypes.c_int),
        ("pointerId", wintypes.UINT),
        ("frameId", wintypes.UINT),
        ("pointerFlags", wintypes.DWORD),
        ("sourceDevice", wintypes.HANDLE),
        ("hwndTarget", wintypes.HWND),
        ("ptPixelLocation", _Point),
        ("ptHimetricLocation", _Point),
        ("ptPixelLocationRaw", _Point),
        ("ptHimetricLocationRaw", _Point),
        ("dwTime", wintypes.DWORD),
        ("historyCount", wintypes.UINT),
        ("InputData", wintypes.INT),
        ("dwKeyStates", wintypes.DWORD),
        ("PerformanceCount", ctypes.c_ulonglong),
        ("ButtonChangeType", ctypes.c_int),
    ]


class _Message(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", _Point),
    ]


class _RawInputHeader(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class _RawInputDeviceList(ctypes.Structure):
    _fields_ = [
        ("hDevice", wintypes.HANDLE),
        ("dwType", wintypes.DWORD),
    ]


class _RawInputDevice(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class _RawDeviceHidInfo(ctypes.Structure):
    _fields_ = [
        ("dwVendorId", wintypes.DWORD),
        ("dwProductId", wintypes.DWORD),
        ("dwVersionNumber", wintypes.DWORD),
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
    ]


class _RawDeviceInfoUnion(ctypes.Union):
    _fields_ = [
        ("hid", _RawDeviceHidInfo),
        ("padding", ctypes.c_byte * 24),
    ]


class _RawDeviceInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("data", _RawDeviceInfoUnion),
    ]


class _HidCaps(ctypes.Structure):
    _fields_ = [
        ("Usage", wintypes.USHORT),
        ("UsagePage", wintypes.USHORT),
        ("InputReportByteLength", wintypes.USHORT),
        ("OutputReportByteLength", wintypes.USHORT),
        ("FeatureReportByteLength", wintypes.USHORT),
        ("Reserved", wintypes.USHORT * 17),
        ("NumberLinkCollectionNodes", wintypes.USHORT),
        ("NumberInputButtonCaps", wintypes.USHORT),
        ("NumberInputValueCaps", wintypes.USHORT),
        ("NumberInputDataIndices", wintypes.USHORT),
        ("NumberOutputButtonCaps", wintypes.USHORT),
        ("NumberOutputValueCaps", wintypes.USHORT),
        ("NumberOutputDataIndices", wintypes.USHORT),
        ("NumberFeatureButtonCaps", wintypes.USHORT),
        ("NumberFeatureValueCaps", wintypes.USHORT),
        ("NumberFeatureDataIndices", wintypes.USHORT),
    ]


class _HidValueRange(ctypes.Structure):
    _fields_ = [
        ("UsageMin", wintypes.USHORT),
        ("UsageMax", wintypes.USHORT),
        ("StringMin", wintypes.USHORT),
        ("StringMax", wintypes.USHORT),
        ("DesignatorMin", wintypes.USHORT),
        ("DesignatorMax", wintypes.USHORT),
        ("DataIndexMin", wintypes.USHORT),
        ("DataIndexMax", wintypes.USHORT),
    ]


class _HidValueNotRange(ctypes.Structure):
    _fields_ = [
        ("Usage", wintypes.USHORT),
        ("Reserved1", wintypes.USHORT),
        ("StringIndex", wintypes.USHORT),
        ("Reserved2", wintypes.USHORT),
        ("DesignatorIndex", wintypes.USHORT),
        ("Reserved3", wintypes.USHORT),
        ("DataIndex", wintypes.USHORT),
        ("Reserved4", wintypes.USHORT),
    ]


class _HidValueUsage(ctypes.Union):
    _fields_ = [
        ("Range", _HidValueRange),
        ("NotRange", _HidValueNotRange),
    ]


class _HidValueCaps(ctypes.Structure):
    _fields_ = [
        ("UsagePage", wintypes.USHORT),
        ("ReportID", ctypes.c_ubyte),
        ("IsAlias", ctypes.c_ubyte),
        ("BitField", wintypes.USHORT),
        ("LinkCollection", wintypes.USHORT),
        ("LinkUsage", wintypes.USHORT),
        ("LinkUsagePage", wintypes.USHORT),
        ("IsRange", ctypes.c_ubyte),
        ("IsStringRange", ctypes.c_ubyte),
        ("IsDesignatorRange", ctypes.c_ubyte),
        ("IsAbsolute", ctypes.c_ubyte),
        ("HasNull", ctypes.c_ubyte),
        ("Reserved", ctypes.c_ubyte),
        ("BitSize", wintypes.USHORT),
        ("ReportCount", wintypes.USHORT),
        ("Reserved2", wintypes.USHORT * 5),
        ("UnitsExp", wintypes.ULONG),
        ("Units", wintypes.ULONG),
        ("LogicalMin", wintypes.LONG),
        ("LogicalMax", wintypes.LONG),
        ("PhysicalMin", wintypes.LONG),
        ("PhysicalMax", wintypes.LONG),
        ("u", _HidValueUsage),
    ]


if _user32 is not None:
    _user32.GetPointerType.argtypes = [wintypes.UINT, ctypes.POINTER(ctypes.c_int)]
    _user32.GetPointerType.restype = wintypes.BOOL
    _user32.GetPointerInfo.argtypes = [wintypes.UINT, ctypes.POINTER(_PointerInfo)]
    _user32.GetPointerInfo.restype = wintypes.BOOL
    _user32.RegisterRawInputDevices.argtypes = [
        ctypes.POINTER(_RawInputDevice),
        wintypes.UINT,
        wintypes.UINT,
    ]
    _user32.RegisterRawInputDevices.restype = wintypes.BOOL
    _user32.GetRawInputDeviceList.argtypes = [
        ctypes.POINTER(_RawInputDeviceList),
        ctypes.POINTER(wintypes.UINT),
        wintypes.UINT,
    ]
    _user32.GetRawInputDeviceList.restype = wintypes.UINT
    _user32.GetRawInputData.argtypes = [
        wintypes.HANDLE,
        wintypes.UINT,
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.UINT),
        wintypes.UINT,
    ]
    _user32.GetRawInputData.restype = wintypes.UINT
    _user32.GetRawInputDeviceInfoW.argtypes = [
        wintypes.HANDLE,
        wintypes.UINT,
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.UINT),
    ]
    _user32.GetRawInputDeviceInfoW.restype = wintypes.UINT

if _hid is not None:
    _hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HidCaps)]
    _hid.HidP_GetCaps.restype = wintypes.LONG
    _hid.HidP_GetValueCaps.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(_HidValueCaps),
        ctypes.POINTER(wintypes.USHORT),
        ctypes.c_void_p,
    ]
    _hid.HidP_GetValueCaps.restype = wintypes.LONG
    _hid.HidP_GetUsageValue.argtypes = [
        ctypes.c_int,
        wintypes.USHORT,
        wintypes.USHORT,
        wintypes.USHORT,
        ctypes.POINTER(wintypes.ULONG),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.ULONG,
    ]
    _hid.HidP_GetUsageValue.restype = wintypes.LONG
    _hid.HidP_GetUsages.argtypes = [
        ctypes.c_int,
        wintypes.USHORT,
        wintypes.USHORT,
        ctypes.POINTER(wintypes.USHORT),
        ctypes.POINTER(wintypes.ULONG),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.ULONG,
    ]
    _hid.HidP_GetUsages.restype = wintypes.LONG


class _TouchpadReportReader:
    def __init__(self, device, preparsed_data):
        self.device = device
        self.preparsed_data = preparsed_data
        self.caps = _HidCaps()
        status = _hid.HidP_GetCaps(preparsed_data, ctypes.byref(self.caps))
        if status != HIDP_STATUS_SUCCESS:
            raise OSError(f"HidP_GetCaps failed: 0x{status & 0xFFFFFFFF:08X}")
        values = (_HidValueCaps * self.caps.NumberInputValueCaps)()
        count = wintypes.USHORT(self.caps.NumberInputValueCaps)
        status = _hid.HidP_GetValueCaps(0, values, ctypes.byref(count), preparsed_data)
        if status != HIDP_STATUS_SUCCESS:
            raise OSError(f"HidP_GetValueCaps failed: 0x{status & 0xFFFFFFFF:08X}")
        self.fields = {}
        for item in values[:count.value]:
            usage = item.u.Range.UsageMin if item.IsRange else item.u.NotRange.Usage
            key = (item.UsagePage, usage)
            self.fields[key] = (
                item.LinkCollection,
                item.LogicalMin,
                item.LogicalMax,
            )
        self.x = self.fields.get((0x01, 0x30))
        self.y = self.fields.get((0x01, 0x31))
        self.contact_id = self.fields.get((0x0D, 0x51))
        self.contact_count = self.fields.get((0x0D, 0x54))
        if not (self.x and self.y and self.contact_id and self.contact_count):
            raise OSError("Touchpad report is missing X/Y/contact-ID/count fields.")
        self.report_length = self.caps.InputReportByteLength

    def _value(self, report, field, usage_page, usage):
        link, _, _ = field
        value = wintypes.ULONG()
        status = _hid.HidP_GetUsageValue(
            0,
            usage_page,
            link,
            usage,
            ctypes.byref(value),
            self.preparsed_data,
            report,
            self.report_length,
        )
        if status != HIDP_STATUS_SUCCESS:
            return None
        return value.value

    def decode(self, report):
        if len(report) < self.report_length:
            return None
        report_buffer = ctypes.create_string_buffer(report)
        x = self._value(report_buffer, self.x, 0x01, 0x30)
        y = self._value(report_buffer, self.y, 0x01, 0x31)
        contact_id = self._value(report_buffer, self.contact_id, 0x0D, 0x51)
        count = self._value(report_buffer, self.contact_count, 0x0D, 0x54)
        if None in (x, y, contact_id):
            return None
        active_usages = (wintypes.USHORT * 32)()
        usage_count = wintypes.ULONG(len(active_usages))
        status = _hid.HidP_GetUsages(
            0,
            0x0D,
            self.contact_id[0],
            active_usages,
            ctypes.byref(usage_count),
            self.preparsed_data,
            report_buffer,
            len(report),
        )
        if status != HIDP_STATUS_SUCCESS:
            return None
        usages = set(active_usages[:usage_count.value])
        tip_switch = 0x42 in usages
        confidence = 0x47 in usages
        return {
            "contact_id": contact_id,
            "x": x,
            "y": y,
            "tip": tip_switch,
            "confidence": confidence,
            "contact_count": count if count is not None else int(tip_switch),
        }


class WindowsTouchpad:
    """Reads native pointer input and raw HID contact reports for Precision Touchpads."""

    def __init__(self):
        self._readers = {}
        self._registered_hwnd = None

    @property
    def available(self):
        return _user32 is not None and _hid is not None

    def register_raw_input(self, hwnd):
        if not self.available:
            return False, "Raw Windows HID input is available on Windows only."
        device = _RawInputDevice(
            0x0D, 0x05, 0, wintypes.HWND(hwnd)
        )
        ctypes.set_last_error(0)
        registered = _user32.RegisterRawInputDevices(
            ctypes.byref(device), 1, ctypes.sizeof(_RawInputDevice)
        )
        if not registered:
            error = ctypes.get_last_error()
            return False, f"Could not register touchpad HID input (Windows error {error})."
        self._registered_hwnd = hwnd
        return True, "Registered Raw Input for HID Digitizer/Touchpad (0x0D/0x05)."

    def enumerate_touchpads(self):
        if not self.available:
            return []
        count = wintypes.UINT(0)
        result = _user32.GetRawInputDeviceList(
            None, ctypes.byref(count), ctypes.sizeof(_RawInputDeviceList)
        )
        if result == 0xFFFFFFFF:
            raise OSError(ctypes.get_last_error(), "GetRawInputDeviceList failed")
        devices = (_RawInputDeviceList * count.value)()
        result = _user32.GetRawInputDeviceList(
            devices, ctypes.byref(count), ctypes.sizeof(_RawInputDeviceList)
        )
        if result == 0xFFFFFFFF:
            raise OSError(ctypes.get_last_error(), "GetRawInputDeviceList failed")
        found = []
        for item in devices[:count.value]:
            reader = self._get_touchpad_reader(item.hDevice)
            if reader is None:
                continue
            name_size = wintypes.UINT(0)
            _user32.GetRawInputDeviceInfoW(
                item.hDevice,
                RIDI_DEVICENAME,
                None,
                ctypes.byref(name_size),
            )
            name = ctypes.create_unicode_buffer(name_size.value + 1)
            _user32.GetRawInputDeviceInfoW(
                item.hDevice,
                RIDI_DEVICENAME,
                name,
                ctypes.byref(name_size),
            )
            info = _RawDeviceInfo()
            info.cbSize = ctypes.sizeof(_RawDeviceInfo)
            info_size = wintypes.UINT(info.cbSize)
            _user32.GetRawInputDeviceInfoW(
                item.hDevice,
                RIDI_DEVICEINFO,
                ctypes.byref(info),
                ctypes.byref(info_size),
            )
            found.append(
                {
                    "name": name.value,
                    "vendor_id": info.data.hid.dwVendorId,
                    "product_id": info.data.hid.dwProductId,
                    "report_bytes": reader.report_length,
                    "fields": tuple(sorted(reader.fields)),
                }
            )
        return found

    def _get_touchpad_reader(self, device):
        key = int(device)
        if key in self._readers:
            return self._readers[key]
        info = _RawDeviceInfo()
        info.cbSize = ctypes.sizeof(_RawDeviceInfo)
        size = wintypes.UINT(info.cbSize)
        result = _user32.GetRawInputDeviceInfoW(
            device,
            RIDI_DEVICEINFO,
            ctypes.byref(info),
            ctypes.byref(size),
        )
        if result == 0xFFFFFFFF:
            raise OSError(
                ctypes.get_last_error(), "GetRawInputDeviceInfo(RIDI_DEVICEINFO) failed"
            )
        if info.dwType != RIM_TYPEHID:
            return None
        if (info.data.hid.usUsagePage, info.data.hid.usUsage) != (0x0D, 0x05):
            return None

        data_size = wintypes.UINT(0)
        result = _user32.GetRawInputDeviceInfoW(
            device, RIDI_PREPARSEDDATA, None, ctypes.byref(data_size)
        )
        if result == 0xFFFFFFFF:
            raise OSError(
                ctypes.get_last_error(), "Could not read touchpad HID descriptor size"
            )
        if not data_size.value:
            return None
        preparsed_data = ctypes.create_string_buffer(data_size.value)
        result = _user32.GetRawInputDeviceInfoW(
            device,
            RIDI_PREPARSEDDATA,
            preparsed_data,
            ctypes.byref(data_size),
        )
        if result == 0xFFFFFFFF:
            raise OSError(
                ctypes.get_last_error(), "Could not read touchpad HID descriptor"
            )
        reader = _TouchpadReportReader(device, preparsed_data)
        self._readers[key] = reader
        return reader

    def _read_raw_reports(self, raw_handle):
        size = wintypes.UINT(0)
        header_size = ctypes.sizeof(_RawInputHeader)
        result = _user32.GetRawInputData(
            raw_handle, RID_INPUT, None, ctypes.byref(size), header_size
        )
        if result == 0xFFFFFFFF:
            raise OSError(ctypes.get_last_error(), "GetRawInputData size query failed")
        if not size.value:
            raise OSError("GetRawInputData returned an empty packet")
        data = ctypes.create_string_buffer(size.value)
        result = _user32.GetRawInputData(
            raw_handle, RID_INPUT, data, ctypes.byref(size), header_size
        )
        if result == 0xFFFFFFFF or result < header_size:
            raise OSError(ctypes.get_last_error(), "GetRawInputData packet read failed")
        header = ctypes.cast(data, ctypes.POINTER(_RawInputHeader)).contents
        if header.dwType != RIM_TYPEHID:
            return None
        reader = self._get_touchpad_reader(header.hDevice)
        if reader is None:
            return None
        hid_offset = header_size
        report_size = ctypes.c_uint.from_buffer(data, hid_offset).value
        report_count = ctypes.c_uint.from_buffer(data, hid_offset + 4).value
        reports_offset = hid_offset + 8
        if not report_size or report_size < reader.report_length:
            return []
        events = []
        for index in range(report_count):
            offset = reports_offset + index * report_size
            if offset + report_size > result:
                break
            report = ctypes.string_at(ctypes.addressof(data) + offset, report_size)
            decoded = reader.decode(report)
            if decoded is not None:
                decoded["device_id"] = int(header.hDevice)
                decoded["x_min"] = reader.x[1]
                decoded["x_max"] = reader.x[2]
                decoded["y_min"] = reader.y[1]
                decoded["y_max"] = reader.y[2]
                events.append(decoded)
        return events

    def decode_message(self, message_address):
        if not self.available:
            return None
        message = ctypes.cast(
            int(message_address), ctypes.POINTER(_Message)
        ).contents
        if message.message == WM_INPUT:
            reports = self._read_raw_reports(message.lParam)
            return ("raw", reports) if reports is not None else None
        if message.message not in (
            WM_POINTERDOWN,
            WM_POINTERUPDATE,
            WM_POINTERUP,
            WM_POINTERCAPTURECHANGED,
        ):
            return None
        pointer_id = int(message.wParam) & 0xFFFF
        pointer_type = ctypes.c_int()
        if not _user32.GetPointerType(pointer_id, ctypes.byref(pointer_type)):
            return None
        if pointer_type.value != PT_TOUCHPAD:
            return None
        info = _PointerInfo()
        if not _user32.GetPointerInfo(pointer_id, ctypes.byref(info)):
            return None
        return (
            "pointer",
            message.message,
            pointer_id,
            info.ptPixelLocation.x,
            info.ptPixelLocation.y,
        )
