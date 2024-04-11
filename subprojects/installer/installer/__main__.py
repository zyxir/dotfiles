from installer import main


main()

# def install_fonts(dry: bool):
#     """Install fonts from font_zip, a zip file containing all fonts wanted.

#     If dry is True, perform a dry run.
#     """
#     font_zip_path = first_existing_path(
#         "~/Zyspace/pcsetup/ZyFonts.zip",
#         "/mnt/c/Users/zyxir/Zyspace/pcsetup/ZyFonts.zip",
#         "~/Downloads/ZyFonts.zip",
#         "/media/zyxir/Zydisk/pcsetup/ZyFonts.zip",
#     )
#     if font_zip_path is None:
#         print("Skip font installation as no ZyFonts.zip is found.")
#         return
#     print(f"Installing fonts in {cyan(font_zip_path)}.")
#     if not dry:
#         font_zip = zipfile.ZipFile(normalize_path(font_zip_path), "r")
#         with tempfile.TemporaryDirectory() as tempdirname:
#             tempdir = Path(tempdirname)
#             font_zip.extractall(tempdir)
#             fonts = []
#             for suffix in ["ttc", "ttf", "otc", "otf"]:
#                 fonts += list(tempdir.rglob(f"*.{suffix}"))
#             if LINUX:
#                 _install_fonts_linux(fonts)
#             elif WINDOWS:
#                 _install_fonts_windows(fonts)


# def _install_fonts_linux(fonts: List[Path]):
#     """Install a list of fonts on Linux."""
#     # Move all fonts to "~/.fonts".
#     fontdir = Path("~/.local/share/fonts").expanduser()
#     fontdir.mkdir(exist_ok=True)
#     for font in fonts:
#         shutil.copy(font, fontdir)
#     run_command("fc-cache -f", "Refreshing font cache.", False)
#     print(f"{len(fonts)} fonts installed.")


# def _install_fonts_windows(fonts: List[Path]):
#     """Install a list of fonts on Windows."""
#     fontdir = Path("~/Desktop/FONTS_TO_INSTALL").expanduser()
#     for font in fonts:
#         shutil.copy(font, fontdir)
#     print(f"{len(fonts)} fonts copied to desktop.")
#     print(red("You should install the fonts manually."))
