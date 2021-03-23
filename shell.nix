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

  language-tool-python = python38Packages.buildPythonPackage rec {
    pname = "language_tool_python";
    version = "2.5.2";

    src = python38Packages.fetchPypi {
      inherit pname version;

      sha256 = "sha256-UFbi0uXRgPtuGSTMYtAXXat13I25Ye9P3j4GR/tYWqs=";
    };
    doCheck = false;
    # propagatedBuildInputs = with pkgs.python38Packages; [ pygame ];
  };

  remi = python38Packages.buildPythonPackage rec {
    pname = "remi";
    version = "2020.11.20";

    src = python38Packages.fetchPypi {
      inherit pname version;
      sha256 = "sha256-KjJlgUa2PTOoiv9zYmeYc8nfnkKp5lHJ5mQtqDSzzKE=";
    };
    doCheck = false;
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
      numpy
      numba
      pip
      setuptools
      graphalama
      matplotlib
      nltk
      remi

    ];
  };
in
  mkShell {
    buildInputs = [
      customPython
      xdotool
      # languagetool
    ];
  }
