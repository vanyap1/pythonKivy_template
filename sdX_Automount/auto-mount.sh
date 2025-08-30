#!/bin/bash

MOUNT_ROOT="/home/vanya/mnt"
DEVNAME="$1"
ACTION="$2"
BASENAME=$(basename "$DEVNAME")
MOUNT_POINT="$MOUNT_ROOT/$BASENAME"
LOGFILE="/home/vanya/mnt/auto-mount.log"

# пропускаємо системні диски
if [[ "$BASENAME" == sda* || "$BASENAME" == sdb* ]]; then
    echo "$(date) Skipping system disk $DEVNAME (ACTION=$ACTION)" >> "$LOGFILE"
    exit 0
fi

echo "$(date) ACTION=$ACTION DEV=$DEVNAME" >> "$LOGFILE"

case "$ACTION" in
    add)
        mkdir -p "$MOUNT_POINT"
        sleep 1
        if systemd-mount --no-block --automount=yes --collect "$DEVNAME" "$MOUNT_POINT" >>"$LOGFILE" 2>&1; then
            echo "$(date) Mounted $DEVNAME at $MOUNT_POINT" >> "$LOGFILE"
        else
            echo "$(date) Failed to mount $DEVNAME" >> "$LOGFILE"
            rmdir "$MOUNT_POINT" 2>/dev/null
        fi
        ;;
    remove)
        # формуємо ім'я юнітки для systemd
        MOUNT_UNIT=$(systemd-escape -p --suffix=mount "$MOUNT_POINT")

        # якщо юнітка активна – зупиняємо та відключаємо
        if systemctl is-active --quiet "$MOUNT_UNIT"; then
            systemctl stop "$MOUNT_UNIT" >>"$LOGFILE" 2>&1
            systemctl disable "$MOUNT_UNIT" >>"$LOGFILE" 2>&1
            echo "$(date) Unmounted $DEVNAME via systemd unit $MOUNT_UNIT" >> "$LOGFILE"
        else
            # fallback на класичне umount
            if mountpoint -q "$MOUNT_POINT"; then
                umount -l "$MOUNT_POINT" >>"$LOGFILE" 2>&1
                echo "$(date) Unmounted $DEVNAME from $MOUNT_POINT" >> "$LOGFILE"
            fi
        fi

        # видаляємо директорію
        rmdir "$MOUNT_POINT" 2>/dev/null
        ;;
esac
