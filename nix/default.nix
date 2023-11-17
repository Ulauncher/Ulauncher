# based off https://github.com/NixOS/nixpkgs/blob/e44462d6021bfe23dfb24b775cc7c390844f773d/pkgs/applications/misc/ulauncher/default.nix#L4-L4
{ lib
, fetchFromGitHub
, gdk-pixbuf
, glib
, git
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
, nix-update-script
, python3Packages
, systemd
, webkitgtk
, wrapGAppsHook
, xvfb-run
, xdg-utils
, withXorg ? true
}:
let
  pname = "ulauncher";
  version = "v6";

  src.python = ../.;
  # putting it directly here instead of "${src.python}/preferences-src" prevents unnecessary rebuilds
  src.preferences = ../preferences-src;

  preferences = mkYarnPackage {
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
in
python3Packages.buildPythonPackage {
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

  nativeCheckInputs = with python3Packages; [
    mock
    pytest
    pytest-mock
    xvfb-run
  ];

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

    ln -s "${preferences}" data/preferences
  '';

  # https://github.com/Ulauncher/Ulauncher/issues/390
  doCheck = false;

  preCheck = ''
    export PYTHONPATH=$PYTHONPATH:$out/${python3Packages.python.sitePackages}
  '';

  # Simple translation of
  # - https://github.com/Ulauncher/Ulauncher/blob/f5a601bdca75198a6a31b9d84433496b63530e74/test
  checkPhase = ''
    runHook preCheck

    # skip tests in invocation that handle paths that
    # aren't nix friendly (i think)
    xvfb-run -s '-screen 0 1024x768x16' \
      pytest -k 'not TestPath and not test_handle_key_press_event' tests

    runHook postCheck
  '';

  # do not double wrap
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=(
     "''${gappsWrapperArgs[@]}"
     ${lib.optionalString withXorg ''--prefix LD_LIBRARY_PATH : "${lib.makeLibraryPath [ libX11 ]}"''}
     --set-default ULAUNCHER_DATA_DIR "$out/share/ulauncher"
    )
  '';

  passthru = {
    updateScript = nix-update-script { };
  };

  meta = with lib; {
    description = "A fast application launcher for Linux, written in Python, using GTK";
    homepage = "https://ulauncher.io/";
    license = licenses.gpl3;
    platforms = platforms.linux;
    maintainers = with maintainers; [ aaronjanse sebtm ];
  };
}
