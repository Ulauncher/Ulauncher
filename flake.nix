{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = inputs@{ self, flake-parts, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
    flake.overlays.default = final: prev: {
      ulauncher6 = final.callPackage ./. { };
    };
    perSystem = { config, self', inputs', pkgs, system, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      };
      packages.default = pkgs.ulauncher6;
      packages.ulauncher6 = pkgs.ulauncher6;
      packages.development = pkgs.ulauncher6.passthru.env;
    };
  };
}
