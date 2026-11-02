"""List camera metadata only; never open a camera or read frames."""

from kardboard_vtuber.camera.devices import main

if __name__ == "__main__":
    raise SystemExit(main())
