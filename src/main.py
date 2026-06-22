import importlib.util
import os
import time


VERSION = "1.0"
AUTHOR = "Isax82"
MOD_FOLDER = "mods"


class Loader:

    def __init__(self):

        self.loaded = []

    def log(self, category, message):

        print(
            f"[PyEx - {category}] : {message}"
        )

    def load_mod(self, file):

        path = os.path.join(
            MOD_FOLDER,
            file
        )

        name = os.path.splitext(
            file
        )[0]

        try:

            spec = (
                importlib.util
                .spec_from_file_location(
                    name,
                    path
                )
            )

            if spec is None:
                raise Exception(
                    "Invalid spec"
                )

            module = (
                importlib.util
                .module_from_spec(
                    spec
                )
            )

            spec.loader.exec_module(
                module
            )

            self.loaded.append(
                name
            )

            self.log(
                "Loader",
                f"Mod loaded : {name}"
            )

        except Exception as e:

            self.log(
                "Error",
                f"{name} -> {e}"
            )

    def load(self):

        self.log(
            "Loader",
            "Loading mods..."
        )

        if not os.path.exists(
            MOD_FOLDER
        ):

            os.mkdir(
                MOD_FOLDER
            )

            self.log(
                "Loader",
                "mods folder created"
            )

            return

        files = [
            f
            for f in os.listdir(
                MOD_FOLDER
            )
            if (
                f.endswith(".py")
                and
                not f.startswith("__")
            )
        ]

        if not files:

            self.log(
                "Loader",
                "No mods found"
            )

            return

        for file in files:

            self.load_mod(
                file
            )

        self.log(
            "Loader",
            f"{len(self.loaded)} mod(s) loaded"
        )


def main():

    print()

    print(
        f"[PyEx - System] : PyEx - v{VERSION}"
    )

    print(
        "[PyEx - System] : Windows x64"
    )

    print(
        f"[PyEx - Info] : Author : {AUTHOR}"
    )

    print()

    time.sleep(1)

    loader = Loader()

    loader.load()


if __name__ == "__main__":
    main()