{ config, pkgs, ... }:

  {
    # Home Manager needs a bit of information about you and the paths it should
    # manage.
    home.username = "zyxir";
    home.homeDirectory = "/home/zyxir";

    # This value determines the Home Manager release that your configuration is
    # compatible with. This helps avoid breakage when a new Home Manager release
    # introduces backwards incompatible changes.
    #
    # You should not change this value, even if you update Home Manager. If you do
    # want to update the value, then make sure to first check the Home Manager
    # release notes.
    home.stateVersion = "23.11"; # Please read the comment before changing.

    # The home.packages option allows you to install Nix packages into your
    # environment.
    home.packages = with pkgs; [
      # # Adds the 'hello' command to your environment. It prints a friendly
      # # "Hello, world!" when run.
      # pkgs.hello

      # Command line utilities.
      curl
      fd
      fontconfig
      git
      imagemagick
      p7zip
      pm2
      ripgrep
      systemd
      vim
      zip

      # Python and accessories.
      (python3.withPackages (python-pkgs: with python-pkgs; [
        isort
        matplotlib
        numpy
        pandas
        scipy
      ]))
      black
      black-macchiato
      nodePackages.pyright

      # Emacs.
      ((emacsPackagesFor emacs).emacsWithPackages (epkgs: with epkgs; [
        # Put heavy or hard-to-build packages here.
        auctex
        evil
        magit
        org
        org-roam
        pdf-tools
        rime
        yasnippet
        yasnippet-snippets
      ]))
      rime-data
    ];

    # Setup nix-direnv.
    programs.direnv = {
      enable = true;
      enableBashIntegration = true;
      nix-direnv.enable = true;
    };

    # Git config.
    programs.git = {
      enable = true;
      userName = "Eric Zhuo Chen";
      userEmail = "ericzhuochen@outlook.com";
      extraConfig = {
        credential.helper = "/mnt/c/Program\\ Files/Git/mingw64/bin/git-credential-manager.exe";
      };
    };

    # Emacs daemon service.
    systemd.user.services.emacs = {
      Unit = {
        Description = "Emacs daemon service.";
      };
      Install = {
        WantedBy = [ "default.target" ];
      };
      Service = {
        ExecStart = "/bin/bash -l -c \"emacs --fg-daemon\"";
        Restart = "on-failure";
        SuccessExitStatus = 15;
        Type = "notify";
      };
    };

    # Home Manager is pretty good at managing dotfiles. The primary way to manage
    # plain files is through 'home.file'.
    home.file = {
      # # Building this configuration will create a copy of 'dotfiles/screenrc' in
      # # the Nix store. Activating the configuration will then make '~/.screenrc' a
      # # symlink to the Nix store copy.
      # ".screenrc".source = dotfiles/screenrc;

      # # You can also set the file content immediately.
      # ".gradle/gradle.properties".text = ''
      #   org.gradle.console=verbose
      #   org.gradle.daemon.idletimeout=3600000
      # '';
    };

    # Home Manager can also manage your environment variables through
    # 'home.sessionVariables'. If you don't want to manage your shell through Home
    # Manager then you have to manually source 'hm-session-vars.sh' located at
    # either
    #
    #  ~/.nix-profile/etc/profile.d/hm-session-vars.sh
    #
    # or
    #
    #  ~/.local/state/nix/profiles/profile/etc/profile.d/hm-session-vars.sh
    #
    # or
    #
    #  /etc/profiles/per-user/zyxir/etc/profile.d/hm-session-vars.sh
    #
    home.sessionVariables = {
      # EDITOR = "emacs";
    };

    # Let Home Manager install and manage itself.
    programs.home-manager.enable = true;
  }
