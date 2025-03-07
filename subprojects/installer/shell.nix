{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    pyright
    (python311.withPackages (python-pkgs: with python-pkgs; [
      fonttools
      isort
    ]))
    shiv
  ];
}
