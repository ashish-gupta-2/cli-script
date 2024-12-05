import click
import yaml
import sys

class SpecialHelpOrder(click.Group):
    """Helper class to achieve special command ordering"""

    def __init__(self, *args, **kwargs):
        self.help_priorities = {}
        super(SpecialHelpOrder, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(SpecialHelpOrder, self).get_help(ctx)

    def list_commands_for_help(self, ctx):
        """reorder the list of commands when listing the help"""
        commands = super(SpecialHelpOrder, self).list_commands(ctx)
        return (c[1] for c in sorted(
            (self.help_priorities.get(command, 25), command)
            for command in commands))

    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except capture
        a priority for listing command names in help.
        """
        help_priority = kwargs.pop('help_priority', 1)
        help_priorities = self.help_priorities

        def decorator(f):
            cmd = super(SpecialHelpOrder, self).command(*args, **kwargs)(f)
            help_priorities[cmd.name] = help_priority
            return cmd

        return decorator

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class Util():
    @staticmethod
    def readYamlFile(settings):
        try:
            with open(settings, "r") as stream:
                enh_settings=yaml.safe_load(stream)
                return enh_settings
        except FileNotFoundError as exc:
            click.echo('Error: the file %s could not be found!' % settings)
            sys.exit(1)
            return None
        except yaml.YAMLError as exc2:
            click.echo('Error: the file %s could not be read!' % settings)
            sys.exit(1)


class Constants():
    OCP_APP_NAME="ocpappsim"
    OCP_APP_IMAGE="docker-na.artifactory.swg-devops.com/hyc-abell-devops-team-ocpappsim-docker-local/ocpappsim:latest"
    OCP_APP_IMAGE_PULL_SECRET="ewoJImF1dGhzIjogewoJCSJkb2NrZXItbmEuYXJ0aWZhY3Rvcnkuc3dnLWRldm9wcy5jb20iOiB7CgkJCSJhdXRoIjogIlpHRnVhV1ZzTG0xcFkyaGxiRUJrWlM1cFltMHVZMjl0T21OdFZtMWtSM1IxVDJwQmVFOXFSVE5OYWtrd1RYcEJNazU2VFRaT1ZVWXdZVlpLTUZWSGNGbFBSMUpIVjFkU2FGa3hUa2hQVjFvd1QwZG9RMkZ0YzNjPSIsCgkJCSJlbWFpbCI6ICJkYW5pZWwubWljaGVsQGRlLmlibS5jb20iCgkJfQoJfQp9"
    OCP_ACTIONS = ["create", "stop", "verify"]
    

