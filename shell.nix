{ pkgs? import <nixpkgs> {}, ... }:
with pkgs;

let
  pygamegui = python38Packages.buildPythonPackage rec {
    pname = "pygame_gui";
    version = "0.5.7";

    src = python38Packages.fetchPypi {
      inherit pname version;

      sha256 = "0nhlq6w0apwjxiggxqwsnivqpi6qsks3pxd1amww707hqg2wd6d6";
    };
    doCheck = false;
    propagatedBuildInputs = with pkgs.python38Packages; [ pygame ];
  };

  graphalama = python38Packages.buildPythonPackage rec {
    pname = "graphalama";
    version = "0.0.1c";
    src = ../graphalama;
    doCheck = false;
    propagatedBuildInputs = with pkgs.python38Packages; [ pygame ];
  };

  customPython = pkgs.python38.buildEnv.override {
    extraLibs = with pkgs.python38Packages; [ 
      pygame
      click
      ptpython
      pygamegui
      pillow
      graphalama
    ];
  };
in
mkShell {
  buildInputs = [ customPython ];
}
