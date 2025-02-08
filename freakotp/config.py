#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2019 Andrea Bonomi <andrea.bonomi@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from pathlib import Path

import tomlkit

__all__ = ["Config"]


class Config:
    config_path: Path  # Path to the configuration file
    copy_to_clipboard: bool = True  # Copy OTPs to clipboard
    show_codes: bool = False  # Show all OTPs
    show_time_left: bool = False  # Show OTP expiration time
    spinner_style: str = ""  # Spinner style

    def __init__(self, path: Path):
        self.config_path = path

    @classmethod
    def load(cls, path: Path) -> "Config":
        """
        Loads the config file
        """
        self = Config(path)
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as f:
                config_data = tomlkit.parse(f.read())
                self.copy_to_clipboard = config_data.get("copy_to_clipboard", self.copy_to_clipboard)
                self.show_codes = config_data.get("show_codes", self.show_codes)
                self.show_time_left = config_data.get("show_time_left", self.show_time_left)
                self.spinner_style = config_data.get("spinner_style", self.spinner_style)
        return self

    def save(self) -> None:
        """
        Save the current configuration to the file
        """
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as f:
                config_data = tomlkit.parse(f.read())
        else:
            config_data = tomlkit.document()
        config_data["copy_to_clipboard"] = self.copy_to_clipboard
        config_data["show_codes"] = self.show_codes
        config_data["show_time_left"] = self.show_time_left
        config_data["spinner_style"] = self.spinner_style
        with self.config_path.open("w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(config_data))

    def __str__(self) -> str:
        return f"path: ({self.config_path}) copy_to_clipboard: {self.copy_to_clipboard} show_codes: {self.show_codes} show_time_left: {self.show_time_left} spinner_style: {self.spinner_style}"
