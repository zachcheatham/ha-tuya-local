# Home Assistant Tuya Local Integration
Control your [TuyaCloud](https://www.home-assistant.io/) devices via Local Push in [Home Assistant](https://www.home-assistant.io/). This integration was thrown together fairly quickly in response to receiving some cheap Wi-Fi bulbs with the [latest version of Tuya's firmware](https://github.com/ct-Open-Source/tuya-convert/wiki/Collaboration-document-for-PSK-Identity-02) that cannot yet be flashed with Tasmota OTA.

> Notice: This component currently only supports lights as I only have Tuya lights available to test with. I will be writing the integrations for these soon, but will be unable to test.

> Notice: This component has only been tested with Tuya devices running firmware version 3.3. If you have devices you can test with, I encourage you to open an issue containing error logs or contribute directly with code 😁!

This integration makes use of my [AIO Tuya library](https://pypi.org/project/aiotuyalan/) for communicating with these devices.
I want to thank the following projects for their existing work at reverse engineering Tuya's protocols to make that library possible:
- [python-tuya](https://github.com/clach04/python-tuya) - [clach04](https://github.com/clach04)
- [tuyapi](https://github.com/codetheweb/tuyapi) - [codetheweb](https://github.com/codetheweb)

I also realize now there are some other custom components floating around that serve a similar purpose and have more devices tested and supported.


## Installation
### Requirements
This integration requires your devices' device id and local key. You can read about retrieving that information [here](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md). I personally was able to retrieve this information by connecting the bulbs with an [older version of the Smart Life app](https://www.apkmirror.com/apk/tuya-inc/smart-life-smart-living/) and pulling its preferences.xml using a rooted android phone.

### HACS
1. Add `https://github.com/zachcheatham/ha-tuya-local` as a custom integration repository to HACS.
2. Click install under "Tuya Local Component."
3. Configure your devices and restart.

### Manual
1. Download the latest release as a ZIP
2. Copy `/custom_components/tuya_local` to your Home Assistant `<config_dir>/custom_components/` directory.
3. Configure your devices and restart.

## Configuration
#### Example
``` yaml
light:
  - platform: tuya_local
    host: 192.168.1.43
    device_id: 4324357afb43243
    local_key: 587902facde43
    version: 3.3
    name: Front Porch Light
  - platform: tuya_local
    host: 192.168.1.44
    device_id: 2311bdf24ac43e
    local_key: 432901939458544ac
    version: 3.3
    name: Bath Light
```

## TO-DO
- Support additional device types.
- Support light effect patterns.
- Test support of older firmware versions (I currently don't own any devices running < 3.3.)
- Support Home Assistant's config UI.

## Reporting Issues
1. Setup the logger component of Home Assistant to log debug messages from this component and related libraries:
``` yaml
logger:
  default: info
  logs:
    custom_components.tuya_local: debug
    aiotuyalan: debug
```
2. Restart HA
3. Retrieve your logs containing the related errors and open a issue in this repository.
 - You can include logs using [pastebin](https://pastebin.com/) and include the link in your issue.
 - Please include details of your Home Assistant enviornment.
