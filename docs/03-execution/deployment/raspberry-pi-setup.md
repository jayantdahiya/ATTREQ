# Raspberry Pi Setup Documentation

## Connection Details

- **Hostname/IP**: 192.168.29.39
- **Username**: jayant
- **SSH Port**: 22 (default)

## System Information

- **Operating System**: Ubuntu 24.04.3 LTS
- **Architecture**: ARM64 (aarch64)
- **Kernel**: Linux 6.8.0-1031-raspi
- **Model**: Raspberry Pi (ARM-based)

## Network Configuration

- **IPv4 Address**: 192.168.29.39
- **IPv6 Address**: 2405:201:5801:904b:2ecf:67ff:fe5f:6289
- **Interface**: wlan0 (WiFi)

## System Status (Last Check: October 14, 2025)

- **System Load**: 0.16 (very low)
- **Disk Usage**: 4.2% of 58.00GB
- **Memory Usage**: 4%
- **Swap Usage**: 0%
- **Temperature**: 61.3°C
- **Active Processes**: 139
- **Logged-in Users**: 0

## Maintenance Notes

- **Available Updates**: 58 updates can be applied immediately
- **System Restart**: Required
- **ESM Apps**: Not enabled (consider enabling for additional security updates)

## SSH Configuration

### Initial Setup Issue
When first connecting, encountered SSH host key verification error due to changed host key.

### Resolution Steps
1. Removed old host key: `ssh-keygen -R 192.168.29.39`
2. Added new host key: `ssh-keyscan -H 192.168.29.39 >> ~/.ssh/known_hosts`
3. Verified connection successful

### Connection Command
```bash
ssh jayant@192.168.29.39
```

## Security Recommendations

1. **Enable ESM Apps** for additional security updates:
   ```bash
   sudo pro status
   ```

2. **Apply pending updates**:
   ```bash
   sudo apt update && sudo apt upgrade
   ```

3. **Restart system** after updates:
   ```bash
   sudo reboot
   ```

## Troubleshooting

### SSH Host Key Issues
If you encounter "REMOTE HOST IDENTIFICATION HAS CHANGED" error:
1. Remove old key: `ssh-keygen -R [IP_ADDRESS]`
2. Add new key: `ssh-keyscan -H [IP_ADDRESS] >> ~/.ssh/known_hosts`
3. Reconnect: `ssh [username]@[IP_ADDRESS]`

### Connection Issues
- Verify Raspberry Pi is powered on and connected to network
- Check IP address hasn't changed (DHCP)
- Ensure SSH service is running: `sudo systemctl status ssh`

## Project Integration

This Raspberry Pi can be used for:
- Development server hosting
- IoT device management
- Remote development environment
- Testing and staging deployments

---

*Last Updated: October 14, 2025*
*Documentation created after resolving SSH connection issues*
