{ pkgs }: {
    deps = [
        pkgs.sqlite.bin
        pkgs.pipenv
        pkgs.vim
        pkgs.python39Packages.pip
        pkgs.python39Packages.python
    ];
}
