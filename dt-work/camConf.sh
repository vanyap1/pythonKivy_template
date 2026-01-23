#!/bin/sh
media-ctl -d /dev/media1 -V "'ov5640 0-003c':0 [fmt:UYVY8_2X8/1920x1080 field:none]"
media-ctl -d /dev/media1 -V "'sun6i-csi-bridge':0 [fmt:UYVY8_2X8/1920x1080 field:none]"
media-ctl -d /dev/media1 -V "'sun6i-csi-bridge':1 [fmt:UYVY8_2X8/1920x1080 field:none]"
