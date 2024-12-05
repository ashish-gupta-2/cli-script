import click
import os
import re
from ibm_ocp_appsim_cli.profilemgmt import ProfileMgmt
from ibm_ocp_appsim_cli.common import SpecialHelpOrder
from ibm_ocp_appsim_cli.common import Util
from ibm_ocp_appsim_cli.common import Constants
from ibm_ocp_appsim_cli.openshiftutil import OpenshiftUtil
from texttable import Texttable
from urllib import request

# Helper class to represent CLI session
class CliSession(object):
    """This class represents a SI CLI session with the SI instance."""
    def __init__(self, cli_profile=ProfileMgmt.SESSION_FILE):
        self.profile_cfg = {}
        self.home = os.path.abspath(os.path.expanduser("~")).rstrip()
        if cli_profile != ProfileMgmt.SESSION_FILE:
            self.profile = ProfileMgmt.SESSION_FILE + "_" + cli_profile
        else:
            self.profile = ProfileMgmt.SESSION_FILE
        if ProfileMgmt.read_profile(self):
            self.with_profile = True
        else:
            self.with_profile = False


# Main ocpappsim CLI
@click.group(name="ocpappsim", cls=SpecialHelpOrder)
@click.option(
              "-p", 
              "--profile",
              envvar="OCPAPPSIM_CLI_PROFILE", 
              default=ProfileMgmt.SESSION_FILE, 
              show_default=False,
              help="The ocpappsim connection profile to be used."
            )
@click.pass_context
def cli(ctxt, profile):
    """ocpappsim commands (Use 'ocpappsim --help' for details).
    """
    ctxt.obj = CliSession(profile)



# Profile subcommand of ocpappsim CLI
@cli.group(name="profile", 
           cls=SpecialHelpOrder)
@click.pass_obj
def profile(ctxt):
    """Manages the ocpappsim connection profiles
    """
    
    

# Creates an ocpappsim connection profile
@profile.command(name="create",
                      help_priority=1)
@click.option("-n", 
              "--name",
              help="Connection profile name. Leave empty to create default profile.", 
              required=False,
              default="", 
              prompt="Enter the name of the new ocpappsim connection profile. Leave empty to create a default profile."
             )
@click.option("-u", 
              "--username",
              help="RedHat OCP user name", 
              required=True, 
              prompt="Enter a valid user name for the RedHat Openshift cluster."
             )
@click.option("-s",
              "--secret",
              help="RedHat OCP user password",
              required=True,
              hide_input=True,
              prompt="Enter a valid user password for the RedHat OpenShift cluster."
             )
@click.option("-e", 
              "--endpoint", 
              help="RedHat OCP API endpoint url", 
              required=True,
              prompt="Enter the API endpoint url for the RedHat OpenShift cluster  (for instance, https://api.spfusion.spp-ocp.tuc.stglabs.ibm.com:6443).",
             )
@click.option("-i", 
              "--ingress", 
              help="RedHat OCP ingress ip address", 
              required=False,
              prompt="Enter the private ingress ip address for the RedHat OpenShift cluster (for instance, 9.11.64.248).",
             )
@click.option('-f', 
              '--force', 
              flag_value='True',
              default=False,
              help="If present, an existing ocpappsim connection profile with the same name will be overwritten.")
@click.pass_obj
def profile_create(cli_session, name, username, secret, endpoint, ingress, force=False):
    """Creates a new ocpappsim connection profile"""
    if OpenshiftUtil.verifyConnection(endpoint,username,secret):
        click.secho("Cluster connection successfully verified", fg="green")
        cli_session.profile_cfg[ProfileMgmt.CFG_USER] = username
        cli_session.profile_cfg[ProfileMgmt.CFG_PWD] = secret
        cli_session.profile_cfg[ProfileMgmt.CFG_HOST] = endpoint
        cli_session.profile_cfg[ProfileMgmt.CFG_INGRESS] = ingress
        if name == "":
            cli_session.profile = ProfileMgmt.SESSION_FILE
        else:
            cli_session.profile = ProfileMgmt.SESSION_FILE + "_" + name
        
        if (force is None and ProfileMgmt.is_profile(cli_session)):
            click.secho("Warning: an ocpappsim connection profile with the same name already exists. Choose a different name or use the '--force' flag to overwrite the existing profile!", fg='yellow', bold=True, err=True)
            return
                  
        ProfileMgmt.write_profile(cli_session)
        cli_session.with_profile = True
        if name== "":
            click.secho("The default ocpappsim connection profile was created successfully!", fg="green")
        else:
            click.secho("The ocpappsim connection profile %s was created successfully!" % name, fg="green")
    else:
        click.secho("Cluster connection failed. Please double-check the provided data and try again!", fg="red")
        return



# Deletes an ocpappsim connection profile
@profile.command(name="delete",
                      help_priority=2)
@click.option("-n", 
              "--name",
              help="Connection profile name. Leave empty to delete default profile.", 
              required=False,
              default="", 
              prompt="Enter the name of the ocpappsim connection profile that is to be deleted. Leave empty to delete default profile."
             )
@click.pass_obj
def profile_delete(cli_session, name):
    """Deletes an existing ocpappsim connection profile"""
    click.secho('Deleting connection profile %s ..' % name, bold=True)
    if name == "":
        cli_session.profile = ProfileMgmt.SESSION_FILE
    else:
        cli_session.profile = ProfileMgmt.SESSION_FILE + "_" + name
        
    deleteStatus = ProfileMgmt.del_profile(cli_session)
    if deleteStatus==True:
        if name== "":
            click.secho("The default ocpappsim connection profile was deleted successfully!", fg="green")
        else:
            click.secho("The ocpappsim connection profile %s was deleted successfully!" % name, fg="green")
    else:
        click.secho("Connection profile deletion failed!", fg="red")



# Lists all ocpappsim connection profiles   
@profile.command(name="list",
                      help_priority=3)
@click.pass_obj
def profile_list(cli_session):
    """Lists all available ocpappsim connection profiles"""
    click.secho('Listing existing ocpappsim connection profiles ..', bold=True)
    ProfileMgmt.list_profiles(cli_session)
    
    

# Creates a new application workload simulation
@cli.command(help_priority=2)
@click.option("-n", 
              "--namespace", 
              help="Namespace name", 
              required=True,
              prompt="Enter a name for the namespace that will be created for the new OcpAppSim deployment.")
@click.option("-s", 
              "--settings", 
              help="Settings file", 
              required=True,
              prompt="Enter the name of your yaml file that contains the advanced workload simulation settings.")
@click.pass_obj 
def deploy(cli_session, namespace=None, settings=None):
    """Deploys a new application workload simulation"""
    ProfileMgmt.assert_profile(cli_session)
    enh_settings=Util.readYamlFile(settings)
    ocpClient = OpenshiftUtil(cli_session)
    
    #Overrides in settings.yaml take precedence. Only use namespace and appname param values if not overwritten.
    if not "name_space" in enh_settings:
        enh_settings['name_space'] = namespace
    if not "container_image" in enh_settings:
        enh_settings['container_image'] = Constants.OCP_APP_IMAGE
    if not "pvc_shared" in enh_settings:
        enh_settings['pvc_shared'] = True
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]

    #verify allowable replica settings
    if not "replicas" in enh_settings:
        if enh_settings['pvc_shared'] == True:
            enh_settings['replicas'] = 2
        else:
            enh_settings['replicas'] = 1
    elif enh_settings['replicas'] != 1 and enh_settings['replicas'] != 2:
        click.secho("Replicas %d is not either 1 or 2" % enh_settings['replicas'], fg='red', bold=True, err=True)
        return
    elif enh_settings['replicas'] > 1 and enh_settings['pvc_shared'] == False:
        click.secho("More than one replica is not allowed unless sharing a single PVC", fg='red', bold=True, err=True)
        return

    #Check if all mandatory settings exist in provided settings yaml
    if assertMandatorySettings(enh_settings)==False:
        click.secho("Mandatory setting(s) are missing in %s" % settings, fg='red', bold=True, err=True)
        return
    
    #Verify if namespace parameter value is valid
    if verifyParamNamespace(enh_settings['name_space'])==False:
        click.secho("Invalid value found for parameter namespace!", fg='red', bold=True, err=True)
        return

    #Upfront check if storage class exists
    if ocpClient.validateStorageClass(enh_settings['storage_class']) == False:
        click.secho("Storage class %s was not found on the cluster!" % enh_settings['storage_class'], fg='red', bold=True, err=True)
        ocpClient.getStorageClasses(enh_settings)
        return

    # Validate some rules around storage class and access modes
    if ( enh_settings['access_mode'] != "ReadWriteOnce" and enh_settings['access_mode'] != "ReadWriteMany" ):
        click.secho("Access mode %s is not either ReadWriteOnce or ReadWriteMany" % enh_settings['access_mode'], fg='red', bold=True, err=True)
        return
    elif ( enh_settings['access_mode'] == "ReadWriteOnce" and ( enh_settings['pod_count'] > 1 and enh_settings['pvc_shared'] == True )):
        click.secho("More than one pod is not allowed with access mode ReadWriteOnce and a shared PVC.", fg='red', bold=True, err=True)
        return

    #verify pod value in yaml file is numeric and max 2 digits
    if not verifyPodsNumber(enh_settings):
        click.secho("Invalid value found for parameter pod_count! Expected: numeric -max 2 digits-", fg='red', bold=True, err=True)
        return 

    click.secho('Starting deployment of %s in namespace %s ..' % (Constants.OCP_APP_NAME, enh_settings['name_space']), bold=True)

    error_encountered = False
    # Create the initial components required for the deployment
    if(ocpClient.createNamespace(enh_settings)==False):
        error_encountered = True
    elif (ocpClient.createServiceAccount(enh_settings) == False):
        error_encountered = True
    elif (ocpClient.createRoleBinding(enh_settings) == False):
        error_encountered = True

    # Create the PVCs needed
    if error_encountered == False:
        if enh_settings['pvc_shared'] == True:
            pvc_name = Constants.OCP_APP_NAME + '-pvc'
            if(ocpClient.createPVC(enh_settings, pvc_name)==False):
                error_encountered = True
        else:
            for i in range (0, enh_settings['pod_count']):
                pvc_name = Constants.OCP_APP_NAME + '-pvc-' + str(i)
                if(ocpClient.createPVC(enh_settings, pvc_name)==False):
                    error_encountered = True
             
    # Create remaing application components
    if error_encountered == False:
        if(ocpClient.createConfigMap(enh_settings, "create")==False):
            error_encountered = True                
        elif(ocpClient.createSecret(enh_settings)==False):
            error_encountered = True                
        elif(ocpClient.createDeployments(enh_settings)==False):
            error_encountered = True                
                    
    if error_encountered == False:
        click.secho('Deployment successfully created!', fg='green', bold=True)


# Modifies an existing application workload simulation
@cli.command(help_priority=3)
@click.option("-n", 
              "--namespace", 
              help="Namespace name", 
              required=True,
              prompt="Enter the name of the namespace that contains the OcpAppSim deployment that is to be modified.")
@click.option("-a", 
              "--action", 
              help="Action (create|stop|verify)", 
              required=True,
              prompt="Enter the action that is to be executed.")
@click.option("-s", 
              "--settings", 
              help="Settings file", 
              required=True,
              prompt="Enter the name of your yaml file that contains the advanced workload simulation settings.")
@click.option('-f', 
              '--force', 
              flag_value='True',
              default=False,
              help="If present, forces the modification of the application workload simulation regardless of ownership.")
@click.pass_obj      
def modify(cli_session, namespace=None, action=None, settings=None, force=False):
    """Modifies an existing application workload simulation"""
    ProfileMgmt.assert_profile(cli_session)
    enh_settings=Util.readYamlFile(settings)
    ocpClient = OpenshiftUtil(cli_session)
    if not "name_space" in enh_settings:
        enh_settings['name_space'] = namespace
    if not "container_image" in enh_settings:
        enh_settings['container_image'] = Constants.OCP_APP_IMAGE
    if not "pvc_shared" in enh_settings:
        enh_settings['pvc_shared'] = True
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]
    enh_settings['action'] = action
    if force:
        enh_settings['force'] = True
    else:
        enh_settings['force'] = False
    
    #verify allowable replica settings
    if not "replicas" in enh_settings:
        if enh_settings['pvc_shared'] == True:
            enh_settings['replicas'] = 2
        else:
            enh_settings['replicas'] = 1
    elif enh_settings['replicas'] != 1 and enh_settings['replicas'] != 2:
        click.secho("Replicas %d is not either 1 or 2" % enh_settings['replicas'], fg='red', bold=True, err=True)
        return
    elif enh_settings['replicas'] > 1 and enh_settings['pvc_shared'] == False:
        click.secho("More than one replica is not allowed unless sharing a single PVC", fg='red', bold=True, err=True)
        return    
    
    #Check if all mandatory settings exist in provided settings yaml
    if assertMandatorySettings(enh_settings)==False:
        click.secho("Mandatory setting(s) are missing in %s" % settings, fg='red', bold=True, err=True)
        return
    
    #Verify if action paramter value is valid
    if verifyParamAction(action)==False:
        click.secho("Invalid value found for parameter action. Valid values are 'create', 'stop', and 'verify'!", fg='red', bold=True, err=True)
        return
    
    #Verify if namespace parameter value is valid
    if verifyParamNamespace(enh_settings['name_space'])==False:
        click.secho("Invalid value found for parameter namespace!", fg='red', bold=True, err=True)
        return
    
    #Upfront check if storage class exists
    if ocpClient.validateStorageClass(enh_settings['storage_class']) == False:
        click.secho("Storage class %s was not found on the cluster!" % enh_settings['storage_class'], fg='red', bold=True, err=True)
        ocpClient.getStorageClasses(enh_settings)
        return

    # Validate some rules around storage class and access modes
    if ( enh_settings['access_mode'] != "ReadWriteOnce" and enh_settings['access_mode'] != "ReadWriteMany" ):
        click.secho("Access mode %s is not either ReadWriteOnce or ReadWriteMany" % enh_settings['access_mode'], fg='red', bold=True, err=True)
        return
    elif ( enh_settings['access_mode'] == "ReadWriteOnce" and ( enh_settings['pod_count'] > 1 and enh_settings['pvc_shared'] == True )):
        click.secho("More than one pod is not allowed with access mode ReadWriteOnce and a shared PVC.", fg='red', bold=True, err=True)
        return

    #verify pod value in yaml file is numeric and max 2 digits
    if not verifyPodsNumber(enh_settings):
        click.secho("Invalid value found for parameter pod_count! Expected: numeric -max 2 digits-", fg='red', bold=True, err=True)
        return

    click.secho('Modifying deployment of %s in namespace %s ..' % (Constants.OCP_APP_NAME, enh_settings['name_space']), bold=True)
    
    if ocpClient.checkNamespace(enh_settings)==False:
        return
    
    click.secho('Namespace %s successfully verified as ocpappsim namespace. Performing modification ..' % enh_settings['name_space'], fg='green')
    
    storageclass = ocpClient.getConfiguredStorageClass(enh_settings)
    if storageclass==False:
        return
    if not storageclass['name'] == enh_settings['storage_class']:
        click.secho("Unsupported operation: cannot change storage class of existing PVC from %s to %s" % (storageclass['name'],enh_settings['storage_class']), fg='yellow', bold=True, err=True)
    if not storageclass['capacity'] == enh_settings['pvc_size']:
        click.secho("Unsupported operation: cannot change capacity of existing PVC from %s to %s" % (storageclass['capacity'],enh_settings['pvc_size']), fg='yellow', bold=True, err=True)
    
    if ocpClient.updateConfigMap(enh_settings)==True:
        if ocpClient.rescalePODs(enh_settings)==True:
            click.secho('Deployment successfully modified!', fg='green', bold=True)


# Updates all existing application workload simulation deployments to renew the container registry secret
@cli.command(name="update-secret",
             help_priority=4)
@click.option('-a', 
              '--all', 
              flag_value='True',
              default=False,
              help="Updates all application workload simulations regardless of ownership")
@click.pass_obj      
def updateSecret(cli_session, all=False):
    """Modifies an existing application workload simulation"""
    ProfileMgmt.assert_profile(cli_session)
    ocpClient = OpenshiftUtil(cli_session)
    
    enh_settings = dict()
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]
    if all:
        enh_settings['update_all'] = True
    else:
        enh_settings['update_all'] = False
    
    click.secho('Updating existing deployments with new secret..', bold=True)
    ocpClient.updateSecret(enh_settings) 
    

# Removes an existing application workload simulation
@cli.command(help_priority=5)
@click.option("-n", 
              "--namespace", 
              help="Namespace name", 
              required=True,
              prompt="Enter the name of the namespace that contains the OcpAppSim deployment that is to be deleted.")
@click.option('-f', 
              '--force', 
              flag_value='True',
              default=False,
              help="If present, forces the deletion of the application workload simulation regardless of ownership.")
@click.pass_obj
def remove(cli_session, namespace=None, force=False):
    """Deletes an existing application workload simulation"""
    ProfileMgmt.assert_profile(cli_session)
    ocpClient = OpenshiftUtil(cli_session)
    enh_settings = dict()
    enh_settings['name_space'] = namespace
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]
    if force:
        enh_settings['force'] = True
    else:
        enh_settings['force'] = False
    
    #Verify if namespace parameter value is valid
    if verifyParamNamespace(enh_settings['name_space'])==False:
        click.secho("Invalid value found for parameter namespace!", fg='red', bold=True, err=True)
        return
    
    click.secho('Deleting deployment of %s in namespace %s ..' % (Constants.OCP_APP_NAME, enh_settings['name_space']), bold=True)
    
    #Verify namespace and its ownership
    if ocpClient.checkNamespace(enh_settings)==False:
        return
    
    click.secho('Namespace %s successfully verified as ocpappsim namespace. Performing deletion ..' % enh_settings['name_space'], fg='green')
    
    if ocpClient.deleteAllResources(enh_settings)==True:
        click.secho('Deployment successfully deleted!', fg='green', bold=True)


        
# Lists existing application workload simulations
@cli.command(help_priority=6)
@click.option('-a', 
              '--all', 
              flag_value='True',
              default=False,
              help="Lists all application workload simulations regardless of ownership")
@click.pass_obj
def list(cli_session, all=False):
    """Lists existing application workload simulations"""
    ProfileMgmt.assert_profile(cli_session)
    ocpClient = OpenshiftUtil(cli_session)
    
    enh_settings = dict()
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]
    if all:
        enh_settings['list_all'] = True
    else:
        enh_settings['list_all'] = False
    
    click.secho('Listing existing deployments ..', bold=True)
    ocpClient.list(enh_settings) 


@cli.command(help_priority=7)
@click.option("-n", 
              "--namespace", 
              help="Namespace name", 
              required=True,
              prompt="Enter the name of the namespace that contains the OcpAppSim deployment that is to be viewed.")
@click.pass_obj
def get(cli_session, namespace=None):
    """Retrieves details of existing application workload simulation"""
    ProfileMgmt.assert_profile(cli_session)
    ocpClient = OpenshiftUtil(cli_session)
    enh_settings = dict()
    enh_settings['name_space'] = namespace
    enh_settings['user_name'] = cli_session.profile_cfg[ProfileMgmt.CFG_USER]
    enh_settings['force'] = True
    
    #Verify if namespace parameter value is valid
    if verifyParamNamespace(enh_settings['name_space'])==False:
        click.secho("Invalid value found for parameter namespace!", fg='red', bold=True, err=True)
        return
    
    #Verify namespace and its ownership
    if ocpClient.checkNamespace(enh_settings)==False:
        return
    
    click.secho('Namespace %s successfully verified as ocpappsim namespace. Listing pods ..' % enh_settings['name_space'], fg='green')
    pods = ocpClient.getPODs(enh_settings)
    if pods==False or len(pods) == 0:
        click.secho("No pods found for deployment %s!" % enh_settings['name_space'], fg='yellow', bold=True)
        return

    t = Texttable()
    t.header(['Pod id', 'Pod name'])
    t.set_cols_width([10, 15])
    t.set_cols_align(['l','l'])
    t.set_cols_dtype(['t','t'])
    count=0
    for pod in pods:
        t.add_row([count, pod])
        count += 1
    click.secho(t.draw())
    
    inputRequired=True
    while inputRequired==True:
        selectedpod = click.prompt('Please enter a valid pod id [0..%i]' % (len(pods)-1), type=int)
        if selectedpod >= 0 and selectedpod < len(pods):
            inputRequired=False
        else:
            click.secho("Error: '%i' is not a valid pod id." % selectedpod, err=True)    
    
    click.secho('Retrieving pod log ..', bold=True)
    host = ocpClient.getPodRouteHost(selectedpod, enh_settings)
    if host==False:
        click.secho("Log url could not be looked up for pod %s!" % pods[selectedpod], fg='red', bold=True, err=True)
        return
    
    r = request.Request('http://' + cli_session.profile_cfg[ProfileMgmt.CFG_INGRESS] + ':80/appsim.log', headers={'Host': host})
    with request.urlopen(r) as response:
        body = response.read()
        click.secho(body)
    


# Creates a new OCP connection profile for the ocpappsim cli
#@cli.command(help_priority=1)
#@click.option("-u", 
#              "--username",
#              help="RedHat OCP user name", 
#              required=True, 
#              prompt="A valid RedHat Openshift cluster user name"
#             )
#@click.option("-s",
#              "--secret",
#              help="RedHat OCP user password",
#              required=True,
#              hide_input=True,
#              prompt="A valid RedHat OpenShift cluster user password"
#             )
#@click.option("-e", 
#              "--endpoint", 
#              help="RedHat OCP API endpoint", 
#              required=True,
#              prompt="A RedHat OpenShift cluster API endpoint (for instance, https://api.spfusion.spp-ocp.tuc.stglabs.ibm.com:6443)",
#             )
#@click.option("-i", 
#              "--ingress", 
#              help="Ingress ip address", 
#              required=False,
#              prompt="RedHat OpenShift cluster ingress ip address (for instance, 9.11.64.248)",
#             )
#@click.pass_obj
#def profile(cli_session, username, secret, endpoint, ingress):
#    """Creates a new OCP connection profile"""
#    if OpenshiftUtil.verifyConnection(endpoint,username,secret):
#        click.secho("Cluster connection successfully verified", fg="green")
#        cli_session.profile_cfg[ProfileMgmt.CFG_USER] = username
#        cli_session.profile_cfg[ProfileMgmt.CFG_PWD] = secret
#        cli_session.profile_cfg[ProfileMgmt.CFG_HOST] = endpoint
#        cli_session.profile_cfg[ProfileMgmt.CFG_INGRESS] = ingress
#        ProfileMgmt.write_profile(cli_session)
#        cli_session.with_profile = True
#        click.secho("The profile %s was created successfully!" % cli_session.profile, fg="green")
#    else:
#        click.secho("Cluster connection failed. Please double-check the provided data and try again!", fg="red")
#        return



# Checking mandatory settings
def assertMandatorySettings(enh_settings):
    if not "storage_class" in enh_settings:
        return False
    if not "access_mode" in enh_settings:
        return False
    if not "pvc_size" in enh_settings:
        return False
    if not "pod_count" in enh_settings:
        return False
    if not "app_name" in enh_settings:
        return False
    if not "fs_used" in enh_settings:
        return False
    
    return True



# Verifying namespace value
def verifyParamNamespace(namespace):
    pattern = "[a-z0-9]{1}[a-z0-9\-\.]{0,251}[a-z0-9]{1}"
    match = re.match(pattern,namespace)
    if match and match.group(0) == namespace:
        return True
    else:
        return False


# Verifying action value
def verifyParamAction(action):
    if action in Constants.OCP_ACTIONS:
        return True
    else:
        return False
    

# Checking pod_count in settings file
def verifyPodsNumber(enh_settings):
    num = str(enh_settings['pod_count'])
    pattern = '^[0-9]{1}$|^[0-9]{2}$'
    if num.isnumeric():
        if int(num)<=0: 
            return False
        if not re.match(pattern,num):
            return False 
    else:
        return False

    return True

