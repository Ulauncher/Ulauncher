{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = inputs@{ self, flake-parts, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
    flake.overlays.default = final: prev: {
      ulauncher6 = final.callPackage ./. { };
      ulauncher6-noxorg = final.ulauncher6.override {
        withXorg = false;
      };
    };
    perSystem = { config, self', inputs', pkgs, system, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      };
      packages.default = pkgs.ulauncher6;
      packages.ulauncher6 = pkgs.ulauncher6;
      packages.ulauncher6-noxorg = pkgs.ulauncher6-noxorg;
    };
  };
}
