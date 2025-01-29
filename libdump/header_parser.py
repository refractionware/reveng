# SPDX-License-Identifier: MIT

class HeaderParser:
    """
    Turns a header into a dictionary.

    (Note: currently very rudimentary.)
    """

    def __init__(self, path: str, flags: dict[str, str] | None = None):
        if flags:
            raise NotImplementedError(
                "TODO - shell out to a compiler to handle ifdefs"
            )

        with open(path) as header_file:
            self._raw = header_file.read()

        self.data = {}
        for line in self._raw.split("\n"):
            line = line.strip().replace("\t", " ")
            if line.startswith("#define"):
                split = line.split()
                self.data[split[1]] = ' '.join(split[2:])

    def __getitem__(self, index: str):
        return self.data[index]


