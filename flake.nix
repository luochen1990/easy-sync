{
  description = "A Python development environment with poetry";

  inputs = {
    nixpkgs.url = "nixpkgs";
  };

  outputs = { nixpkgs, ... }:
  let
    supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    eachSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f rec {
      inherit system;
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python3; # use pkgs.python3.withPackages (p: []) if you need more python packages in nixpkgs
    });
  in
  {
    packages = eachSystem ({pkgs, ...}: {
      easy-sync = let
        pyproject = pkgs.lib.importTOML ./pyproject.toml;
        meta = pyproject.tool.poetry;
      in
      pkgs.python3Packages.buildPythonPackage {
        pname = meta.name;
        version = meta.version;
        pyproject = true;
        src = ./.;
        buildInputs = [ pkgs.python3Packages.poetry-core ];
        doCheck = true;
        meta = with pkgs.lib; {
          description = meta.description;
          homepage = meta.repository;
          license = licenses.asl20;
          maintainers = with maintainers; [ luochen1990 ];
        };
      };
    });

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
  };
}
