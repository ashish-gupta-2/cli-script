import os
from os import walk
import shutil
import textwrap
import click
import json
import zipfile
from texttable import Texttable

# Responsible for reading and writing OcpAppSim profiles
class ProfileMgmt:

    RC_CMD_WARN = 1  # Command was executed with a warning.
    RC_SFILE_ERROR = -1  # Error reading or writing the session file.
    RC_PFILE_ERROR = -2  # Error reading or writing the profile file.
    RC_AUTH_ERROR = -3  # Error during authentication.
    RC_API_ERROR = -4  # Error during API interaction.

    CLI_FORMAT_VER = "fver"
    PROFILE_VERSION = 2
    PROFILE = "prf"
    CFG_USER = "usr"
    CFG_PWD = "pwd"
    CFG_HOST = "host"
    CFG_INGRESS = "ingress"

    SESSION_FILE = "ocpappsimcli"

    @staticmethod
    def write_profile(session):
        """Writes profile data to the file system."""
        try:
            if not os.path.exists(session.home + "/." + session.profile):
                os.makedirs(session.home + "/." + session.profile)
                os.chmod(session.home + "/." + session.profile, 0o700)
            with zipfile.ZipFile(session.home + "/." + session.profile + "/profile", 'w') as profile_file:
                p_file = zipfile.ZipInfo("profile.json")
                p_file.compress_type = zipfile.ZIP_DEFLATED
                s_data = {ProfileMgmt.CLI_FORMAT_VER: ProfileMgmt.PROFILE_VERSION, ProfileMgmt.PROFILE: session.profile_cfg}
                profile_file.writestr(p_file, json.dumps(s_data))
                os.chmod(session.home + "/." + session.profile + "/profile", 0o600)
        except Exception as ex:
            print(ex)
            click.secho("Unexpected error: %s" % str(ex), fg="bright_red")
            click.secho("Aborting...", fg="bright_red")
            click.get_current_context().exit(ProfileMgmt.RC_PFILE_ERROR)

    @staticmethod
    def read_profile(session):
        """Reads profile data from the file system."""
        try:
            if os.path.isfile(session.home + "/." + session.profile + "/profile"):
                with zipfile.ZipFile(session.home + "/." + session.profile + "/profile", 'r') as profile_file:
                    s = profile_file.read("profile.json")
                s_data = json.loads(s)
                session.profile_cfg = s_data[ProfileMgmt.PROFILE]
                if s_data[ProfileMgmt.CLI_FORMAT_VER] < ProfileMgmt.PROFILE_VERSION:
                    click.secho("The profile version is outdated. Consider recreating the connection profile to benefit from new features!", fg="yellow")
                    if s_data[ProfileMgmt.CLI_FORMAT_VER] < 2:
                        session.profile_cfg[ProfileMgmt.CFG_INGRESS] = "127.0.0.1"
                return True
            else:
                return False
        except Exception as ex:
            click.secho("Unexpected error: %s" % str(ex), fg="bright_red")
            click.secho("Aborting...", fg="bright_red")
            click.get_current_context().exit(ProfileMgmt.RC_PFILE_ERROR)


    @staticmethod
    def list_profiles(session):
        """Lists profiles from the file system."""
        try:
            profiles = []
            for (dirpath, dirnames, filenames) in walk(session.home):
                for x in range(len(dirnames)):
                    #print(dirnames[x])
                    if dirnames[x].startswith("." + ProfileMgmt.SESSION_FILE):
                        profiles.append(dirnames[x])
                break
            
            t = Texttable()
            t.set_cols_width([30, 20, 80, 25, 25, 20, 20])
            t.set_cols_align(['l','l','l','l','l','l','l'])
            t.set_cols_dtype(['t','t','t','t','t','t','t'])
            t.header(['Profile name', 'Default profile?', 'RedHat OCP API endpoint', 'RedHat OCP user name', 'RedHat OCP user password', 'Ingress ip address', 'Profile version'])
            for x in range(len(profiles)):
                with zipfile.ZipFile(session.home + "/" + profiles[x] + "/profile", 'r') as profile_file:
                    s = profile_file.read("profile.json")
                profile_data = json.loads(s)
                profile_cfg = profile_data[ProfileMgmt.PROFILE]                
                rhApiEndpoint = profile_cfg['host']
                rhUser = profile_cfg['usr']
                if profile_data[ProfileMgmt.CLI_FORMAT_VER] < 2:
                    rhIngress = "-"
                else:
                    rhIngress = profile_cfg['ingress']
                profileVersion = profile_data[ProfileMgmt.CLI_FORMAT_VER]
                if profiles[x] == "." + ProfileMgmt.SESSION_FILE:
                    isDefaultProfile = "Yes"
                else:
                    isDefaultProfile = "No"
                if len(profile_cfg['pwd']) > 4:
                    rhPwd = profile_cfg['pwd'][:2] + "..."
                else:
                    rhPwd = "..."
                if profiles[x] == "." + ProfileMgmt.SESSION_FILE:
                    t.add_row(["*", isDefaultProfile, rhApiEndpoint, rhUser, rhPwd, rhIngress, profileVersion])
                else:
                    t.add_row([profiles[x].replace("." + ProfileMgmt.SESSION_FILE + "_", ""), isDefaultProfile, rhApiEndpoint, rhUser, rhPwd, rhIngress, profileVersion])

            click.secho(t.draw())
            click.secho('Found %i ocpappsim connection profiles.' % len(profiles), fg='green', bold=True)
            
        except Exception as ex:
            click.secho("Unexpected error: %s" % str(ex), fg="bright_red")
        
        
    @staticmethod
    def del_profile(session):
        """Deletes a profile from the file system."""
        try:
            if os.path.isfile(session.home + "/." + session.profile + "/profile"):
                shutil.rmtree(session.home + "/." + session.profile)
                return True
            else:
                return False
        except Exception as ex:
            click.secho("Unexpected error: %s" % str(ex), fg="bright_red")
            return False

     
    @staticmethod
    def is_profile(session):
        """Checks if a profile with the given name exists."""
        if os.path.isfile(session.home + "/." + session.profile + "/profile"):
            return True
        else:
            return False

    @staticmethod
    def assert_profile(session):
        if session.with_profile == False:
            click.secho("ocpappsim connection profile could not be loaded!", fg="red")
            click.get_current_context().exit(ProfileMgmt.RC_PFILE_ERROR)


