# Android IP Webcam integration

> **Status: user-verified over Wi-Fi.**
>
> **TL;DR** — The Nothing Phone hosts an authenticated MJPEG stream. OpenCV reads the direct
> `/video` endpoint without installing a vendor camera client or virtual-camera driver on Windows.

## Why this transport exists

The Nothing Phone (3a) build did not expose Android's native USB `Webcam` mode. The user also
rejected third-party camera software on Windows. A phone-hosted network stream therefore provides
the cleanest bridge:

```mermaid
flowchart LR
    Camera["Phone camera"] --> App["IP Webcam app<br/>phone only"]
    App --> MJPEG["Authenticated MJPEG"]
    MJPEG --> Network["Wi-Fi now<br/>USB tethering optional"]
    Network --> Python["This Python application"]
    Python --> OBS["Preview captured by OBS"]
```

## Phone setup

1. Select the front camera in IP Webcam.
2. Configure a dedicated username and password.
3. Start the server.
4. Keep the phone and PC on the same private network.
5. Use the direct `/video` endpoint, not only the HTML control page.

## Application command

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror
```

The current physical phone orientation requires `--rotate left`. `--mirror` produces the expected
selfie behavior.

## Verified observations

| Observation | Result |
|---|---|
| Direct endpoint | `/video` returned multipart MJPEG |
| Source format reported | 1920x1080 at 25 FPS |
| Post-restart measured throughput | Approximately 28-30 FPS |
| Final orientation | 1080x1920 portrait |
| Read failures/reconnects during probe | None |
| Visual confirmation | User confirmed preview looked correct |

An initial 3-5 FPS measurement disappeared after restarting the phone server. This demonstrates why
one short benchmark should not be treated as a permanent transport limit.

## Security

Real credentials and the private address are intentionally absent from this book. The application
redacts credentials in diagnostics, but command-line history remains an external risk. Use a
camera-specific password and stop the server when finished.

## Troubleshooting

| Symptom | Check |
|---|---|
| `could not open camera source` | Replace placeholders; confirm server is running |
| Browser works, OpenCV fails | Use direct `/video`; try `--backend ffmpeg` |
| Sideways output | Use `--rotate left` |
| Motion feels reversed | Add or remove `--mirror` |
| Low FPS | Restart server, lower resolution/quality, improve network |
| Reconnect loop | Keep app active and disable battery optimization |

---

⬅️ [Runtime flow](runtime-flow.md) · ➡️
[Diagnostics](diagnostics-and-performance.md)
