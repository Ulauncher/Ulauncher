# based off https://github.com/NixOS/nixpkgs/blob/e44462d6021bfe23dfb24b775cc7c390844f773d/pkgs/applications/misc/ulauncher/default.nix#L4-L4
{ lib
, fetchFromGitHub
, gdk-pixbuf
, git
, glib
, gnome
, gobject-introspection
, gtk-layer-shell
, gtk3
, intltool
, libX11
, libappindicator
, librsvg
, libwnck
, mkYarnPackage
, mypy
, nix-update-script
, python3Packages
, ruff
, stdenv
, systemd
, typos
, yarn
, webkitgtk
, wrapGAppsHook
, xdg-utils
, xvfb-run
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
        --replace "__dirname, '../data/preferences" "__dirname, 'dist"
    '';
    buildPhase = ''yarn --offline run build'';
    installPhase = ''mv -T deps/ulauncher-prefs/dist $out'';
    distPhase = "true";
  };

  # piece of shared makeWrapperArgs modifications to reuse in multiple places
  wrapperArgs = ''
    "''${makeWrapperArgs[@]}"
    "''${gappsWrapperArgs[@]}"
    ${lib.optionalString withXorg ''--prefix LD_LIBRARY_PATH : "${lib.makeLibraryPath [ libX11 ]}"''}
    --set-default ULAUNCHER_SYSTEM_PREFIX "$out"
  '';

  preferencesPackages = [ yarn ];

  testsPackages = pp: (with pp; [
    black
    mock
    pytest
    pytest-mock
  ]) ++ [
    mypy
    ruff
    typos
    xvfb-run # xvfb-run tests fail
  ];

  self = python3Packages.buildPythonPackage {
    inherit version pname;
    src = src.python;

    nativeBuildInputs = with python3Packages; [
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
    ] ++ lib.optionals withXorg [
      libwnck
    ];

    # runtime dependencies (binaries prepended to PATH)
    propagatedBuildInputs = with python3Packages; [
      levenshtein
      mock
      pycairo
      pygobject3
      requests
    ] ++ [
      git
      glib
      gtk3
      xdg-utils
    ];

    nativeCheckInputs = testsPackages python3Packages;

    patches = [
      # ./some.patch
    ];

    postPatch = ''
      patchShebangs bin/ulauncher-toggle

      substituteInPlace \
          bin/ulauncher-toggle \
          io.ulauncher.Ulauncher.desktop \
        --replace gapplication ${glib}/bin/gapplication
      substituteInPlace \
          ulauncher/modes/extensions/ExtensionRunner.py \
        --replace '"PYTHONPATH": PATHS.APPLICATION,' '"PYTHONPATH": ":".join(sys.path),'

      substituteInPlace \
          ulauncher.service \
          io.ulauncher.Ulauncher.service \
        --replace "/usr" "$out"

      ln -s "${preferencesPackage}" data/preferences
    '';

    doCheck = true;

    preCheck = ''
      patchShebangs ul
      export PYTHONPATH=$PYTHONPATH:$out/${python3Packages.python.sitePackages}

      export HOME=$TMPDIR

      substituteInPlace \
          scripts/tests.sh \
        --replace ' pytest ' ' pytest -p no:cacheprovider '

      substituteInPlace \
          tests/modes/shortcuts/test_RunScript.py \
        --replace '#!/bin/bash' '#!${stdenv.shell}'

      # this is required to run tests
      ulWrapperArgs=(${wrapperArgs})
      wrapProgram ul "''${ulWrapperArgs[@]}"
    '';

    checkPhase = ''
      runHook preCheck

      ./ul test

      runHook postCheck
    '';

    # do not double wrap
    dontWrapGApps = true;
    preFixup = ''
      makeWrapperArgs=(${wrapperArgs})
    '';

    passthru = {
      updateScript = nix-update-script { };
      env = self.passthru.pythonModule.withPackages (pp:
        [ self ]
        ++ preferencesPackages
        ++ testsPackages pp
        # debugging
        ++ (with pp; [ ipdb ])
        # Jetbrains IDEs don't like it without setuptools/pip installed
        ++ (with pp; [ setuptools pip ])
      );
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
