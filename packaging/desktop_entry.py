"""PyInstaller entry point, also used by the isolated sample child process."""
import multiprocessing


if __name__ == "__main__":
    multiprocessing.freeze_support()
    from backend.desktop import main

    main()
