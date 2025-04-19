#!/bin/bash

SERVICE_NAME="guiService"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
PROJECT_DIR="/home/vanya/pythonKivy_template"
PYTHON_EXEC="/usr/bin/python3"
MAIN_SCRIPT="main.py"

function create_service {
    echo "Creating service file..."
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=My Python Project Service
After=network.target

[Service]
ExecStartPre=/bin/sleep 10
ExecStart=$PYTHON_EXEC $PROJECT_DIR/$MAIN_SCRIPT
WorkingDirectory=$PROJECT_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOL
    echo "Service file created at $SERVICE_FILE"
}

function enable_service {
    echo "Enabling and starting service..."
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    echo "Service enabled and started."
}

function disable_service {
    echo "Disabling and stopping service..."
    sudo systemctl stop $SERVICE_NAME
    sudo systemctl disable $SERVICE_NAME
    sudo rm -f $SERVICE_FILE
    sudo systemctl daemon-reload
    echo "Service disabled and removed."
}

function show_help {
    echo "Usage: install.sh [OPTIONS]"
    echo "Options:"
    echo "  -f       Remove if previously created and install again"
    echo "  -r       Disable autostart and remove service"
    echo "  -? or -help  Show this help message"
}

if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

while getopts "fr?-help" opt; do
    case $opt in
        f)
            disable_service
            create_service
            enable_service
            ;;
        r)
            disable_service
            ;;
        \?|-help)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
done