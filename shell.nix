{ pkgs? import <nixpkgs> {}, ... }:
with pkgs;
let 
  pythonEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
      pygame = super.pygame.overridePythonAttrs (old: rec {
        nativeBuildInputs = with pkgs; [
          pkg-config SDL
        ];

        buildInputs = [
          SDL SDL_image SDL_mixer SDL_ttf libpng libjpeg
          portmidi xorg.libX11 freetype
        ];

        # Tests fail because of no audio device and display.
        doCheck = false;
        preConfigure = ''
          sed \
            -e "s/origincdirs = .*/origincdirs = []/" \
            -e "s/origlibdirs = .*/origlibdirs = []/" \
            -e "/'\/lib\/i386-linux-gnu', '\/lib\/x86_64-linux-gnu']/d" \
            -e "/\/include\/smpeg/d" \
            -i buildconfig/config_unix.py
          ${lib.concatMapStrings (dep: ''
            sed \
              -e "/origincdirs =/a\        origincdirs += ['${lib.getDev dep}/include']" \
              -e "/origlibdirs =/a\        origlibdirs += ['${lib.getLib dep}/lib']" \
              -i buildconfig/config_unix.py
            '') buildInputs
          }
          LOCALBASE=/ ${python.interpreter} buildconfig/config.py
        '';
      });
    }); 
  };
in pkgs.mkShell {
  buildInputs = [ pythonEnv ];

  PYTHONPATH = ".";
}
