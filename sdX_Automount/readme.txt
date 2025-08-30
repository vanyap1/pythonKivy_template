add script  -> sudo cp auto-mount.sh /usr/local/bin/auto-mount.sh
            -> sudo chmod 755 /usr/local/bin/auto-mount.sh
            -> sudo chown root:root /usr/local/bin/auto-mount.sh

add mountpoit to user dir
            -> mkdir /home/vanya/mnt
            -> touch /home/vanya/mnt/auto-mount.log
            -> sudo chmod 666 /home/vanya/mnt/auto-mount.log

add devrules
            -> sudo cp 99-automount.rules /etc/udev/rules.d/99-automount.rules
            -> sudo udevadm control --reload-rules
            -> sudo udevadm trigger