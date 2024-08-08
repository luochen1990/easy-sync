{
  description = "A Python development environment with poetry";

  inputs = {
    nixpkgs.url = "nixpkgs";
  };

  outputs = { self, nixpkgs }:
  let
    supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    eachSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f rec {
      inherit system;
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python3; # use pkgs.python3.withPackages (p: []) if you need more python packages in nixpkgs
    });
  in
  {
    devShells = eachSystem ({pkgs, python, ...}: rec {
      default = poetry;

      poetry = pkgs.mkShell {
        buildInputs = [
          python
          pkgs.poetry
        ];

        shellHook = ''
          export PATH=$(poetry env info --path)/bin:$PATH
        '';
      };
    });

    apps = eachSystem ({system, pkgs, ...}: {
      default = {
        type = "app";
        program = "${pkgs.writeShellScript "funix-app" ''
          source ${self.devShells.${system}.default.shellHook}
          funix .
        ''}";
      };
    });

  };
}
