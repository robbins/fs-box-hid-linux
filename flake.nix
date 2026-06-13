{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux"; # Change to "aarch64-darwin" for Apple Silicon M1/M2/M3
      pkgs = nixpkgs.legacyPackages.${system};
      
      # Define your custom Python environment here
      myPythonEnv = pkgs.python3.withPackages (ps: with ps; [
      ]);
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          myPythonEnv
          pkgs.hidapi
        ];

        shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.hidapi ]}:$LD_LIBRARY_PATH"
          python --version
        '';
      };
    };
}

