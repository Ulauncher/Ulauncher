# based off https://github.com/NixOS/nixpkgs/blob/e44462d6021bfe23dfb24b775cc7c390844f773d/pkgs/applications/misc/ulauncher/default.nix#L4-L4
{ lib
, bash
, buildEnv
, fetchFromGitHub
, gdk-pixbuf
, git
, glib
, gnome
, gnumake
, gnused
, gobject-introspection
, gtk-layer-shell
, gtk3
, intltool
, libX11
, libappindicator
, librsvg
, mkYarnPackage
, mypy
, nix-update-script
, procps
, python3Packages
, ruff
, stdenv
, systemd
, typos
, webkitgtk
, wrapGAppsHook
, xdg-utils
, xvfb-run
, yarn
, withXorg ? true
}:
let
  pname = "ulauncher";
  version = "v6";

  src.python = ../.;
  # putting it directly here instead of "${src.python}/preferences-src" prevents unnecessary rebuilds
  src.preferences = ../preferences-src;

  preferencesPackage = mkYarnPackage {
    name = "${pname}-${version}-ulauncher-prefs";
    src = src.preferences;

    postPatch = ''
      substituteInPlace webpack.build.conf.js \
        --replace-fail "__dirname, '../data/preferences" "__dirname, 'dist"
    '';
    buildPhase = ''yarn --offline run build'';
    installPhase = ''mv -T deps/ulauncher-prefs/dist $out'';
    distPhase = "true";
  };

  packages.preferences.dev = [ yarn ];
  packages.tests.python = pp: (with pp; [
    black
    mock
    (pygobject-stubs.overridePythonAttrs (old: { PYGOBJECT_STUB_CONFIG = "Gtk3,Gdk3,Soup2"; }))
    pytest
    pytest-mock
  ]);
  packages.tests.system = [
    mypy
    ruff
    typos
    xvfb-run # xvfb-run tests fail
  ];

  packages.tests.all = pp: packages.tests.python pp ++ packages.tests.system;

  self = python3Packages.buildPythonPackage {
    inherit version pname;
    src = src.python;

    nativeBuildInputs = [
      gdk-pixbuf
      gobject-introspection
      intltool
      wrapGAppsHook
    ];

    buildInputs = [
      glib
      gnome.adwaita-icon-theme
      gtk-layer-shell
      gtk3
      libappindicator
      librsvg
      webkitgtk
    ];

    # runtime dependencies / binaries prepended to PATH
    propagatedBuildInputs = with python3Packages; [
      levenshtein
      mock
      pycairo
      pygobject3
      requests
    ] ++ lib.optionals withXorg [
      ewmh
    ] ++ [
      git
      glib
      gtk3
      xdg-utils
    ];

    nativeCheckInputs = packages.tests.all python3Packages;

    postPatch = ''
      patchShebangs bin/ulauncher-toggle

      substituteInPlace \
          bin/ulauncher-toggle \
          io.ulauncher.Ulauncher.desktop \
        --replace-fail gapplication ${glib}/bin/gapplication

      substituteInPlace \
          ulauncher/modes/extensions/ExtensionController.py \
        --replace-fail '"PYTHONPATH": PATHS.APPLICATION,' '"PYTHONPATH": ":".join(sys.path),'

      substituteInPlace \
          ulauncher.service \
          io.ulauncher.Ulauncher.service \
        --replace-fail "/usr" "$out"

      ln -s "${preferencesPackage}" data/preferences

      substituteInPlace \
          tests/modes/shortcuts/test_RunScript.py \
        --replace-fail '#!/bin/bash' '#!${stdenv.shell}'
    '';

    # do not double wrap
    dontWrapGApps = true;
    preFixup = ''
      makeWrapperArgs+=(
        "''${gappsWrapperArgs[@]}"
        ${lib.optionalString withXorg ''--prefix LD_LIBRARY_PATH : "${lib.makeLibraryPath [ libX11 ]}"''}
        --set-default ULAUNCHER_SYSTEM_PREFIX "$out"
      )
    '';

    doCheck = true;
    # Python packages don't have a checkPhase, only an installCheckPhase:
    # - https://github.com/NixOS/nixpkgs/blob/add2bf7e523b0b1d6e192b6060cf2f0aac26bcc0/pkgs/development/interpreters/python/mk-python-derivation.nix#L274-L276
    installCheckPhase = ''
      test_dir="$PWD/.test-tmp"
      (
        mkdir -p "$test_dir/bin"
        export HOME="$test_dir"

        makeWrapper "$(command -v make)" "$test_dir/bin/make" "''${makeWrapperArgs[@]}"
        export PATH="$test_dir/bin:$PATH"
        #make test
        rm -r "$test_dir"
      )

      (
        export PATH="${lib.makeBinPath [ procps ]}:$PATH"
        trap "echo killing $BASHPID && pkill -P $BASHPID" EXIT

        mkdir -p "$test_dir"
        logfile="$test_dir/log.txt"
        env -i HOME="$test_dir" \
          "$(command -v xvfb-run)" --auto-servernum -- \
          $out/bin/ulauncher --verbose &>"$logfile" &
        ulauncher_pid=$!

        while IFS= read -r line; do
          # lowercase each line for matching
          case "''${line,,}" in
            *error*)
              echo "ERROR: ulauncher failed to start"
              exit 1
            ;;
            *info*)
              # exits successfully as soon as it sees the first info message
              # TODO: add some other successful startup indicator?
              echo "OK: ulauncher started properly"
              exit 0
            ;;
          esac
        done < <(tail --pid=$ulauncher_pid -f "$logfile" | tee /dev/stderr)
      )
    '';

    passthru = {
      # won't be updateable until release?
      # updateScript = nix-update-script { };
      env = buildEnv {
        name = "${pname}-${version}-development";
        paths = [
          # python environment
          (self.passthru.pythonModule.withPackages (pp:
            [ self ]
              ++ packages.tests.python pp
              ++ (with pp; [ ]
              # debugging
              ++ [ ipdb ]
              # present in requirements.txt
              ++ [ build ]
              # Jetbrains IDEs don't like it without setuptools/pip installed
              ++ [ setuptools pip ]
            )
          ))
        ]
        ++ packages.preferences.dev
        ++ packages.tests.system;
      };
    };

    meta = with lib; {
      description = "A fast application launcher for Linux, written in Python, using GTK";
      homepage = "https://ulauncher.io/";
      license = licenses.gpl3;
      platforms = platforms.linux;
      maintainers = with maintainers; [ nazarewk ];
    };
  };
in
self
