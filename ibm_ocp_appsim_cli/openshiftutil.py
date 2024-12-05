import json
import requests
from ibm_ocp_appsim_cli.profilemgmt import ProfileMgmt
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from kubernetes import client
from openshift.dynamic import DynamicClient
from openshift.helper.userpassauth import OCPLoginConfiguration
from ibm_ocp_appsim_cli.common import Constants
import click
import yaml
from texttable import Texttable

# This class uses openshift/openshift-restclient-python
# See https://github.com/openshift/openshift-restclient-python
class OpenshiftUtil:

    redHatOcpClient = None

    # Constructur
    # Creates dynamic client that is needed to interact with the OCP cluster
    def __init__(self, cli_session):
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            ocpConfig = OCPLoginConfiguration(ocp_username=cli_session.profile_cfg[ProfileMgmt.CFG_USER], ocp_password=cli_session.profile_cfg[ProfileMgmt.CFG_PWD])
            ocpConfig.host = cli_session.profile_cfg[ProfileMgmt.CFG_HOST]
            ocpConfig.verify_ssl = False
            ocpConfig.get_token()
            ocp_client = client.ApiClient(ocpConfig)
            self.redHatOcpClient = DynamicClient(ocp_client)
        except Exception as e: 
            print("OCP client creation failed with exception: ", str(e) )
            return None


    @staticmethod
    # Used to verify provided connection details
    def verifyConnection(apihost, username, password):
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            ocpConfig = OCPLoginConfiguration(ocp_username=username, ocp_password=password)
            ocpConfig.host = apihost
            ocpConfig.verify_ssl = False
            ocpConfig.get_token()
            #print('Auth token: {0}'.format(kubeConfig.api_key))
            #print('Token expires: {0}'.format(kubeConfig.api_key_expires))
            ocp_client = client.ApiClient(ocpConfig)
            dyn_client = DynamicClient(ocp_client)
        except Exception as e: 
            print("Connection verification failed with exception: ", str(e) )
            return False
        else:
            return True


    # Method used to create a namespace
    def createNamespace(self, enh_settings):
        try:
            namespace = '''
kind: Namespace
apiVersion: v1
metadata:
  name: '''+enh_settings['name_space']+'''
  labels:
    name: '''+enh_settings['name_space']+'''
    app: '''+Constants.OCP_APP_NAME+'''
    owner: '''+enh_settings['user_name']+'''
'''
            click.secho('> Creating namespace %s .. ' % enh_settings['name_space'], nl=False)
            v1_namespace = self.redHatOcpClient.resources.get(api_version='v1', kind='Namespace')
            namespace_data = yaml.safe_load(namespace)
            resp = v1_namespace.create(body=namespace_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED'+'\n'+str(e), fg='red')
            click.secho("Unable to create namespace %s." % enh_settings['name_space'], fg='yellow', bold=True)
            return False
        else:
            return True

    # Method used to create a config map
    def createConfigMap(self, enh_settings, action):
        try:
            configmap_name=Constants.OCP_APP_NAME+'-cfg'
            configmap = '''
kind: ConfigMap
apiVersion: v1
metadata:
   name: '''+configmap_name+'''
   namespace: '''+enh_settings['name_space']+'''
   labels:
      app: '''+Constants.OCP_APP_NAME+'''
data:
   action: '''+action+'''
   settings.properties: |-
      APPSIM_FS_USED_MAX='''+str(enh_settings['fs_used'])+'''
      APPSIM_PATH=/srv
      APPSIM_INIT_FILL='''+str(enh_settings['init_fill'])+'''
'''
            if str(enh_settings['hourly_new']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_NEW="+str(enh_settings['hourly_new']+"\n")
            if str(enh_settings['hourly_mod']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_MOD="+str(enh_settings['hourly_mod']+"\n")
            if str(enh_settings['hourly_del']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_DEL="+str(enh_settings['hourly_del']+"\n")
            if str(enh_settings['size_min']) != 'default':
                configmap=configmap+"      APPSIM_SIZE_MIN="+str(enh_settings['size_min']+"\n")
            if str(enh_settings['size_max']) != 'default':
                configmap=configmap+"      APPSIM_SIZE_MAX="+str(enh_settings['size_max']+"\n")
            if str(enh_settings['random']) != 'default':
                configmap=configmap+"      APPSIM_RANDOM="+str(enh_settings['random']+"\n")                                                               
            click.secho('> Creating config map %s .. ' % configmap_name, nl=False)
            v1_cfgmap = self.redHatOcpClient.resources.get(api_version='v1', kind='ConfigMap')
            configmap_data = yaml.safe_load(configmap)
            resp = v1_cfgmap.create(body=configmap_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            click.secho("Unable to create configmap.", fg='yellow', bold=True)
            return False
        else:
            return True
        
    # Method used to update the config map
    def updateConfigMap(self, enh_settings):
        try:         
            configmap_name=Constants.OCP_APP_NAME+'-cfg'
            configmap = '''
kind: ConfigMap
apiVersion: v1
metadata:
   name: '''+configmap_name+'''
   namespace: '''+enh_settings['name_space']+'''
   labels:
      app: '''+Constants.OCP_APP_NAME+'''
data:
   action: '''+enh_settings['action']+'''
   settings.properties: |-
      APPSIM_FS_USED_MAX='''+str(enh_settings['fs_used'])+'''
      APPSIM_PATH=/srv
      APPSIM_INIT_FILL='''+str(enh_settings['init_fill'])+'''
'''
            if str(enh_settings['hourly_new']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_NEW="+str(enh_settings['hourly_new']+"\n")
            if str(enh_settings['hourly_mod']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_MOD="+str(enh_settings['hourly_mod']+"\n")
            if str(enh_settings['hourly_del']) != 'default':
                configmap=configmap+"      APPSIM_HOURLY_DEL="+str(enh_settings['hourly_del']+"\n")
            if str(enh_settings['size_min']) != 'default':
                configmap=configmap+"      APPSIM_SIZE_MIN="+str(enh_settings['size_min']+"\n")
            if str(enh_settings['size_max']) != 'default':
                configmap=configmap+"      APPSIM_SIZE_MAX="+str(enh_settings['size_max']+"\n")
            if str(enh_settings['random']) != 'default':
                configmap=configmap+"      APPSIM_RANDOM="+str(enh_settings['random']+"\n")     
            click.secho('> Updating config map %s .. ' % configmap_name, nl=False)
            v1_cfgmap = self.redHatOcpClient.resources.get(api_version='v1', kind='ConfigMap')
            configmap_data = yaml.safe_load(configmap)
            resp = v1_cfgmap.patch(body=configmap_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            
        except Exception as e:
            click.secho("Config map update failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        else:
            return True    
        

    # Method used to create a pvc
    def createPVC(self, enh_settings, pvc_name=""):
        if pvc_name == "":
            pvc_name = Constants.OCP_APP_NAME + '-pvc'
        try:
            pvc = '''
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
   name: '''+pvc_name+'''
   namespace: '''+enh_settings['name_space']+'''
spec:
   accessModes:
   - '''+enh_settings['access_mode']+'''
   volumeMode: Filesystem
   resources:
      requests:
         storage: '''+enh_settings['pvc_size']+'''
   storageClassName: '''+enh_settings['storage_class']+'''
'''
            click.secho('> Creating pvc %s with size %s from storage class %s .. ' % (pvc_name,enh_settings['pvc_size'],enh_settings['storage_class']), nl=False)
            v1_pvc = self.redHatOcpClient.resources.get(api_version='v1', kind='PersistentVolumeClaim')
            pvc_data = yaml.safe_load(pvc)
            resp = v1_pvc.create(body=pvc_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            click.secho("Unable to create PVC.", fg='yellow', bold=True)
            return False
        else:
            return True


    # Method used to create a pod
    def createPOD(self, pod_name, i, enh_settings):
        try:
            pvc_name = Constants.OCP_APP_NAME + '-pvc'
            pod = '''
apiVersion: "v1"
kind: "Pod"
metadata:
 name: '''+pod_name+'''
 namespace: '''+enh_settings['name_space']+'''
 labels:
      app: '''+Constants.OCP_APP_NAME+'''
      pod: '''+pod_name+'''
spec:
 imagePullSecrets:
  - 
   name: regcred
 containers:
  -
   name: "ocpappsim-container"
   image: '''+enh_settings['container_image']+'''
   ports:
    -
     containerPort: 80
   volumeMounts:
    -
     mountPath: "/srv"
     name: "pvol"
    - 
     mountPath: "/etc/config"
     name: "config-volume"
 volumes:
  -
   name: "pvol"
   persistentVolumeClaim:
    claimName: '''+pvc_name+'''
    readOnly: false
  -
   name: "config-volume"
   configMap: 
    name: "ocpappsim-cfg"
'''
            click.secho(' > Creating pod %s .. ' % pod_name, nl=False)
            v1_pod = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            pod_data = yaml.safe_load(pod)
            resp = v1_pod.create(body=pod_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            click.secho("Unable to create pod %s." % pod_name, fg='yellow', bold=True)
            return False
        else:
            return True

    def createDeployment(self, deploy_name, i, enh_settings):
            if enh_settings['pvc_shared'] == False:
                pvc_name = Constants.OCP_APP_NAME + '-pvc-' + str(i)
            else:
                pvc_name = Constants.OCP_APP_NAME + '-pvc'
            try:
                serviceaccount_name = Constants.OCP_APP_NAME + '-sa'
                deployment = '''
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: ''' + deploy_name + '''
      namespace: ''' + enh_settings['name_space'] + '''
      labels:
          app: '''+Constants.OCP_APP_NAME+'''
          app: ''' + deploy_name + '''
    spec:
      replicas: ''' + str(enh_settings['replicas']) + '''
      selector:
        matchLabels:
          app: ''' + deploy_name + '''
      strategy: {}
      template:
       metadata:
          labels:
            app: ''' + deploy_name + '''
      # => from here down its the same as the pods metadata: and spec: sections
       spec:
          serviceAccountName: ''' + serviceaccount_name + '''
          imagePullSecrets:
           - 
            name: regcred
          containers:
           -
            name: "ocpappsim-container"
            image: ''' + enh_settings['container_image'] + '''
            ports:
             -
              containerPort: 80
            volumeMounts:
             -
              mountPath: "/srv"
              name: "pvol"
             - 
              mountPath: "/etc/config"
              name: "config-volume"
          volumes:
             -
              name: "pvol"
              persistentVolumeClaim:
                claimName: ''' + pvc_name + '''
                readOnly: false
             -
              name: "config-volume"
              configMap: 
                name: "ocpappsim-cfg"
    '''
                click.secho(' > Creating deployment %s .. ' % deploy_name,
                            nl=False)
                v1_deployment = self.redHatOcpClient.resources.get(
                    api_version='v1', kind='Deployment')
                deployment_data = yaml.safe_load(deployment)
                resp = v1_deployment.create(body=deployment_data,
                                            namespace=enh_settings[
                                                'name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                click.secho("Deployment failed with error: %s" % str(e),
                            fg='red', bold=True, err=True)
                click.secho("Unable to create deployment %s." % deploy_name, fg='yellow', bold=True)
                return False
            else:
                return True

    # Method used to create a set of pods. It calls the createPOD method
    def createDeployments(self, enh_settings):
        error_count=0
        click.secho('> Creating %s deployments(s) .. ' % enh_settings['pod_count'])
        for i in range(0, enh_settings['pod_count'], 1):
            if error_count == 0 and self.createDeployment(Constants.OCP_APP_NAME+'-'+str(i),i,enh_settings)==True:
                if self.createSVC(i, Constants.OCP_APP_NAME+'-'+str(i), enh_settings)==True:
                    if self.createRoute(i, enh_settings)==True:
                        error_count=0
                    else:
                        error_count+=1
                else:
                    error_count+=1
            else:
                error_count+=1
                
        if(error_count == 0):
            return True
        else:
            return False


    # Method used to create a service
    def createSVC(self, i, podname, enh_settings):
        try:
            svc_name = Constants.OCP_APP_NAME+str(i)+'-svc'
            svc = '''
kind: Service
apiVersion: v1
metadata:
   name: '''+svc_name+'''
   namespace: '''+enh_settings['name_space']+'''
spec:
  selector:
    app: '''+podname+'''
  ports:
    - protocol: TCP
      port: 80
'''
            click.secho('  > Creating service %s .. ' % svc_name, nl=False)
            v1_svc= self.redHatOcpClient.resources.get(api_version='v1', kind='Service')
            svc_data = yaml.safe_load(svc)
            resp = v1_svc.create(body=svc_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            click.secho("Unable to create service %s." % svc_name, fg='yellow', bold=True)
            return False
        else:
            return True        



    # Method used to create a route
    def createRoute(self, i, enh_settings):
        try:
            route_name = Constants.OCP_APP_NAME+str(i)+'-route'
            svc_name = Constants.OCP_APP_NAME+str(i)+'-svc'
            route = '''
kind: Route
apiVersion: route.openshift.io/v1
metadata:
  name: '''+route_name+'''
  namespace: '''+enh_settings['name_space']+'''
spec:
  to:
    kind: Service
    name: '''+svc_name+'''
    weight: 100
  port:
    targetPort: 80
'''
            click.secho('  > Creating route %s .. ' % route_name, nl=False)
            v1_route = self.redHatOcpClient.resources.get(api_version='v1', kind='Route')
            route_data = yaml.safe_load(route)
            resp = v1_route.create(body=route_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            click.secho("Unable to create route %s." % route_name, fg='yellow', bold=True)
            return False
        else:
            return True

    # Method to create serviceaccount
    def createServiceAccount(self, enh_settings):
            try:
                serviceaccount_name = Constants.OCP_APP_NAME + '-sa'
                serviceaccount = '''
                                    apiVersion: v1
                                    kind: ServiceAccount
                                    metadata:
                                       name: '''+serviceaccount_name+'''
                                       namespace: '''+enh_settings['name_space']+'''
                                 '''
                click.secho('  > Creating serviceaccount %s .. ' % serviceaccount_name, nl=False)
                v1_serviceaccount = self.redHatOcpClient.resources.get(api_version='v1',
                                                              kind='ServiceAccount')
                serviceaccount_data = yaml.safe_load(serviceaccount)
                resp = v1_serviceaccount.create(body=serviceaccount_data,
                                       namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                click.secho("Deployment failed with error: %s" % str(e),
                            fg='red', bold=True, err=True)
                click.secho("Unable to create service account %s." % serviceaccount_name, fg='yellow', bold=True)
                return False
            else:
                return True

    # Method to create RoleBinding
    def createRoleBinding(self, enh_settings):
            try:
                rolebinding_name = Constants.OCP_APP_NAME + ':scc:anyuid'
                serviceaccount_name = Constants.OCP_APP_NAME + '-sa'
                rolebinding = '''
                                        apiVersion: rbac.authorization.k8s.io/v1
                                        kind: RoleBinding
                                        metadata:
                                          name: '''+rolebinding_name+'''
                                        roleRef:
                                          apiGroup: rbac.authorization.k8s.io
                                          kind: ClusterRole
                                          name: system:openshift:scc:anyuid
                                        subjects:
                                        - kind: ServiceAccount
                                          name: '''+serviceaccount_name+'''
                                          namespace: '''+enh_settings['name_space']+'''
                                        '''
                click.secho('  > Creating rolebinding %s .. ' % rolebinding_name, nl=False)
                v1_rolebinding = self.redHatOcpClient.resources.get(api_version='rbac.authorization.k8s.io/v1',
                                                              kind='RoleBinding')
                rolebinding_data = yaml.safe_load(rolebinding)
                resp = v1_rolebinding.create(body=rolebinding_data, namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                click.secho("Deployment failed with error: %s" % str(e),
                            fg='red', bold=True, err=True)
                click.secho("Unable to create role binding %s." % rolebinding_name, fg='yellow', bold=True)
                return False
            else:
                return True

    # Method used to delete resources
    def deleteAllResources(self, enh_settings):
        try:    
            error_count=0
            v1_routes = self.redHatOcpClient.resources.get(api_version='v1', kind='Route')
            v1_services = self.redHatOcpClient.resources.get(api_version='v1', kind='Service')
            v1_pods = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            v1_cfgmaps = self.redHatOcpClient.resources.get(api_version='v1', kind='ConfigMap')
            v1_secrets = self.redHatOcpClient.resources.get(api_version='v1', kind='Secret')
            v1_pvcs = self.redHatOcpClient.resources.get(api_version='v1', kind='PersistentVolumeClaim')
            v1_namespace = self.redHatOcpClient.resources.get(api_version='v1', kind='Namespace')
            v1_deployment = self.redHatOcpClient.resources.get(api_version='v1', kind='Deployment')
            v1_serviceaccount = self.redHatOcpClient.resources.get(api_version='v1', kind='ServiceAccount')
            v1_rolebinding = self.redHatOcpClient.resources.get(api_version='rbac.authorization.k8s.io/v1', kind='RoleBinding')
            
            #delete all resources
            try:
                click.secho(' > Removing route(s) .. ', nl=False)
                routes = v1_routes.get(namespace=enh_settings['name_space'])
                if len(routes.items) >0:
                    for route in routes.items:
                        v1_routes.delete(name=route.metadata.name, namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')
                error_count+=1
   
            try:
                click.secho(' > Removing service(s) .. ', nl=False)
                services = v1_services.get(namespace=enh_settings['name_space'])
                if len(services.items) >0:
                    for service in services.items:
                        v1_services.delete(name=service.metadata.name, namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')
                error_count+=1

            try:
                click.secho(' > Removing deployment(s) .. ', nl=False)
                deployments = v1_deployment.get(
                    namespace=enh_settings['name_space'])
                if len(deployments.items) > 0:
                    for deployment in deployments.items:
                        v1_deployment.delete(name=deployment.metadata.name,
                                             namespace=enh_settings[
                                                 'name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                error_count += 1

            # try:
            #     click.secho(' > Removing pod(s) .. ', nl=False)
            #     pods = v1_pods.get(namespace=enh_settings['name_space'])
            #     if len(pods.items) >0:
            #         for pod in pods.items:
            #             v1_pods.delete(name=pod.metadata.name, namespace=enh_settings['name_space'])
            #     click.secho('OK', fg='green')
            # except Exception as e:
            #     click.secho('FAILED', fg='red')
            #     error_count+=1

                
            try:
                click.secho(' > Removing config map .. ', nl=False)
                v1_cfgmaps.delete(name=Constants.OCP_APP_NAME+'-cfg', namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')   
                error_count+=1  
                
            try:
                click.secho(' > Removing secret .. ', nl=False)
                v1_secrets.delete(name='regcred', namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')   
                error_count+=1  

            try:
                click.secho(' > Removing persistent volume claims .. ', nl=False)
                pvcs = v1_pvcs.get(namespace=enh_settings['name_space'])
                if len(pvcs.items) > 0:
                    for pvc in pvcs.items:
                        v1_pvcs.delete(name=pvc.metadata.name,
                                             namespace=enh_settings[
                                                 'name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')   
                error_count+=1

            try:
                click.secho(' > Removing rolebinding ..', nl=False)
                rolebinding_name = Constants.OCP_APP_NAME + ':scc:anyuid'
                v1_rolebinding.delete(name=rolebinding_name,namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                error_count+=1

            try:
                click.secho(' > Removing serviceaccount ..', nl=False)
                serviceaccount_name = Constants.OCP_APP_NAME + '-sa'
                v1_serviceaccount.delete(name=serviceaccount_name, namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e:
                click.secho('FAILED', fg='red')
                error_count+=1

            try:
                click.secho(' > Removing namespace .. ', nl=False)
                v1_namespace.delete(name=enh_settings['name_space'],namespace=enh_settings['name_space'])
                click.secho('OK', fg='green')
            except Exception as e: 
                click.secho('FAILED', fg='red')   
                error_count+=1 
                
            if(error_count>0):
                click.secho("Warning: Some resources could not be removed properly and might require some manual clean-up!", fg='yellow')

        except Exception as e: 
            click.secho("Deployment removal failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        else:
            return True

    # Method used to create a secret
    def createSecret(self, enh_settings):
        try:
            secret_name = 'regcred'
            secret = '''
apiVersion: v1
kind: Secret
metadata:
  name: '''+secret_name+'''
  namespace: '''+enh_settings['name_space']+'''
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: >-
    '''+Constants.OCP_APP_IMAGE_PULL_SECRET+'''
'''
            click.secho('> Creating secret %s .. ' % secret_name, nl=False)
            v1_secret = self.redHatOcpClient.resources.get(api_version='v1', kind='Secret')
            secret_data = yaml.safe_load(secret)
            resp = v1_secret.create(body=secret_data, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
        except Exception as e: 
            click.secho('FAILED', fg='red')
            click.secho("Deployment failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        else:
            return True


    # Method used to list existing deployments
    def list(self, enh_settings):
        try:
            v1_namespace = self.redHatOcpClient.resources.get(api_version='v1', kind='Namespace')
            v1_pods = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            v1_cfgmap = self.redHatOcpClient.resources.get(api_version='v1', kind='ConfigMap')
            v1_pvcs = self.redHatOcpClient.resources.get(api_version='v1', kind='PersistentVolumeClaim')
            if enh_settings['list_all']==True:
                namespaces = v1_namespace.get(label_selector="app="+Constants.OCP_APP_NAME)
            else:
                namespaces = v1_namespace.get(label_selector="app="+Constants.OCP_APP_NAME+",owner="+enh_settings['user_name'])
            t = Texttable()
            t.set_cols_width([40, 15, 15, 15, 15, 35, 15])
            t.set_cols_align(['l','l','l','l','l','l','l'])
            t.set_cols_dtype(['t','t','t','t','t','t','t'])
            t.header(['Namespace', 'Owner', 'Pod count', 'PVC capacity', 'PVC status', 'Storage class', 'AppSim status'])
            for ocappsim_ns in namespaces.items:
                ns_name = ocappsim_ns.metadata.labels.name
                ns_owner = ocappsim_ns.metadata.labels.owner
                try:
                    pods = v1_pods.get(namespace=ns_name)
                    pod_avail_count = 0
                    for pod in pods.items:
                        if pod.status.phase == 'Running':
                            pod_avail_count += 1
                    pod_avail_count = str(pod_avail_count)
                    pod_count = str(len(pods.items))
                    pod_status=pod_avail_count + '/' + pod_count
                except Exception as e1:
                    pod_status = '?/?'
                try:
                    cfgmap = v1_cfgmap.get(namespace=ns_name,name=Constants.OCP_APP_NAME+'-cfg')
                    if cfgmap.data.action == 'create' or cfgmap.data.action == 'start':
                        appSimStatus = 'CREATING'
                    elif cfgmap.data.action == 'verify':
                        appSimStatus = 'VERIFYING'
                    elif cfgmap.data.action == 'stop':
                        appSimStatus = 'STOPPED'
                    else:
                        appSimStatus = 'UNKNOWN'
                except Exception as e2:
                    appSimStatus = 'UNKNOWN'
                pvc_capacity = 'Unkown'
                pvc_status = 'Unknown'
                pvc_sc = 'Unknown'
                try:
                    pvc = v1_pvcs.get(namespace=ns_name,name=Constants.OCP_APP_NAME+'-pvc')
                    if pvc is not None:
                        if pvc.status is not None:
                            pvc_status = pvc.status.phase
                            if pvc.status.capacity is not None:
                                pvc_capacity = pvc.status.capacity.storage
                        if pvc.spec is not None:
                            pvc_sc = pvc.spec.storageClassName
                except Exception as e3:
                    pvc_capacity = 'Unkown'
                    pvc_status = 'Unknown'
                    pvc_sc = 'Unknown'
                t.add_row([ns_name, ns_owner, pod_status, pvc_capacity, pvc_status, pvc_sc, appSimStatus])

            click.secho(t.draw())
            click.secho('Found %i deployments.' % len(namespaces.items), fg='green', bold=True)
            
        except Exception as e: 
            click.secho("Deployment listing with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        else:
            return True


    # Method used to update existing deployments with new secret
    def updateSecret(self, enh_settings):
        try:
            v1_namespace = self.redHatOcpClient.resources.get(api_version='v1', kind='Namespace')
            v1_secrets = self.redHatOcpClient.resources.get(api_version='v1', kind='Secret')
            if enh_settings['update_all']==True:
                namespaces = v1_namespace.get(label_selector="app="+Constants.OCP_APP_NAME)
            else:
                namespaces = v1_namespace.get(label_selector="app="+Constants.OCP_APP_NAME+",owner="+enh_settings['user_name'])

            for ocappsim_ns in namespaces.items:
                enh_settings['name_space']=ocappsim_ns.metadata.labels.name
                click.secho('Updating deployment %s [owner=%s]..' % (enh_settings['name_space'], enh_settings['user_name']))
                try:
                    v1_secrets.delete(name='regcred', namespace=enh_settings['name_space'])
                except Exception as e2:
                    pass
                self.createSecret(enh_settings)
                    
            click.secho('Updated %i deployments with new secret.' % len(namespaces.items), fg='green', bold=True)
            
        except Exception as e: 
            click.secho("Secret updates failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        else:
            return True


    # Method used to validate a storage class
    def validateStorageClass(self, storageClass):
        try:
            v1_storageclass = self.redHatOcpClient.resources.get(api_version='v1', kind='StorageClass')
            storageclass = v1_storageclass.get(name=storageClass)
            return True
        except Exception as e: 
            return False
        else:
            return False
        
    # Method used to check namespace
    def checkNamespace(self, enh_settings):
        try:
            v1_namespace = self.redHatOcpClient.resources.get(api_version='v1', kind='Namespace')
            
            #check if given namespace is a ocpappsim namespace
            namespaces = v1_namespace.get(namespace=enh_settings['name_space'], label_selector="app="+Constants.OCP_APP_NAME+",name="+enh_settings['name_space'])
            if len(namespaces.items) == 0:
                click.secho("The namespace %s does not exist or it is not a valid ocpappsim namespace!" % enh_settings['name_space'], fg='red', bold=True, err=True)
                return False
            else:
                if namespaces.items[0].metadata.labels.owner:
                    ns_owner=namespaces.items[0].metadata.labels.owner
                else:
                    ns_owner="unknown"
                if enh_settings['force'] or enh_settings['user_name'] == ns_owner:
                    return True
                else:
                    click.secho("Warning: the namespace %s is owned by another user (%s)! You can force the operation by using the '--force' flag." % (enh_settings['name_space'],ns_owner), fg='yellow', bold=True, err=True)
                    return False
            
        except Exception as e:
            return False

    # Method to retrieve storage class of existing deployment
    def getConfiguredStorageClass(self, enh_settings):
        if enh_settings['pvc_shared'] == True:
            pvc_name = Constants.OCP_APP_NAME+'-pvc'
        else:
            pvc_name = Constants.OCP_APP_NAME+'-pvc-0'
        try:
            v1_pvcs = self.redHatOcpClient.resources.get(api_version='v1', kind='PersistentVolumeClaim')
            pvc = v1_pvcs.get(namespace=enh_settings['name_space'],name=pvc_name)
            storageclass = dict()
            storageclass['capacity'] = pvc.status.capacity.storage
            storageclass['name'] = pvc.spec.storageClassName
            return storageclass
        except Exception as e:
            click.secho("Storage class details could not be retrieved!", fg='red', bold=True, err=True)
            return False
  

    # Method to rescale an existing deployment
    def rescalePODs(self, enh_settings):
        try:
            v1_pods = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            repl_count = enh_settings['replicas']
            
            req_pod_count = int(enh_settings['pod_count'])
            pods = v1_pods.get(namespace=enh_settings['name_space'])
            curr_pod_count = len(pods.items)
            if req_pod_count == (curr_pod_count/repl_count):      # There are two pods per deployment
                click.secho('Requested deployment count (%i) matches current deployment count. No rescaling required!' % req_pod_count, fg='green')
                return True
            elif req_pod_count > (curr_pod_count/repl_count):
                click.secho('Current deployment count is %i, requested deployment count is %i. Upscaling ..' % (curr_pod_count/repl_count,req_pod_count), fg='green')
                error_count=0
                for i in range(int(curr_pod_count/repl_count), req_pod_count, 1):
                    # When not sharing a single PVC, upscaling requires creating new PVCs
                    if error_count == 0 and enh_settings['pvc_shared'] == False:  
                        pvc_name = Constants.OCP_APP_NAME + '-pvc-' + str(i)
                        if(self.createPVC(enh_settings, pvc_name)==False):
                            error_count+=1
                    if error_count == 0 and self.createDeployment(Constants.OCP_APP_NAME+'-'+str(i),i,enh_settings)==True:
                        if self.createSVC(i, Constants.OCP_APP_NAME+'-'+str(i), enh_settings)==True:
                            if self.createRoute(i, enh_settings)==True:
                                error_count=0
                            else:
                                error_count+=1
                        else:
                            error_count+=1
                    else:
                        error_count+=1            
                if(error_count == 0):
                    return True
                else:
                    return False      
            elif req_pod_count < (curr_pod_count/repl_count):
                click.secho('Current deployment count is %i, requested deployment count is %i. Downscaling ..' % (curr_pod_count/repl_count,req_pod_count), fg='green')              
                error_count=0
                for i in range(req_pod_count, int(curr_pod_count/repl_count), 1):
                    if error_count == 0 and self.deleteRoute(Constants.OCP_APP_NAME+str(i)+"-route", enh_settings)==True:
                        if self.deleteService(Constants.OCP_APP_NAME+str(i)+"-svc", enh_settings)==True:
                            if self.deleteDeployment(Constants.OCP_APP_NAME+'-'+str(i), enh_settings)==True:
                                if enh_settings['pvc_shared'] == False:
                                    pvc_name = Constants.OCP_APP_NAME + '-pvc-' + str(i)
                                    if self.deletePVC(pvc_name, enh_settings)==True:
                                        error_count=0
                                    else:
                                        error_count+=1
                            else:
                                error_count+=1 
                        else:
                            error_count+=1 
                    else:
                        error_count+=1 
                if(error_count == 0):
                    return True
                else:
                    return False        
        except Exception as e:
            return False
        

    # Delete route
    def deleteRoute(self, name, enh_settings):
        try:
            v1_routes = self.redHatOcpClient.resources.get(api_version='v1', kind='Route')
            click.secho('> Deleting route %s .. ' % name, nl=False)
            v1_routes.delete(name=name, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            return True
        except Exception as e:
            click.secho('FAILED', fg='red')
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
        
    # Delete service
    def deleteService(self, name, enh_settings):
        try:
            v1_services = self.redHatOcpClient.resources.get(api_version='v1', kind='Service')
            click.secho('> Deleting service %s .. ' % name, nl=False)
            v1_services.delete(name=name, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            return True
        except Exception as e:
            click.secho('FAILED', fg='red')
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False

    # Delete pod
    def deletePod(self, name, enh_settings):
        try:
            v1_pods = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            click.secho('> Deleting pod %s .. ' % name, nl=False)
            v1_pods.delete(name=name, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            return True
        except Exception as e:
            click.secho('FAILED', fg='red')
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False

     # Delete PVC
    def deletePVC(self, name, enh_settings):
        try:
            v1_pvcs = self.redHatOcpClient.resources.get(api_version='v1', kind='PersistentVolumeClaim')
            click.secho('> Deleting pvc %s .. ' % name, nl=False)
            v1_pvcs.delete(name=name, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            return True
        except Exception as e:
            click.secho('FAILED', fg='red')
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False

    # Delete deployment
    def deleteDeployment(self, name, enh_settings):
        try:
            v1_deployments = self.redHatOcpClient.resources.get(api_version='v1', kind='Deployment')
            click.secho('> Deleting deployment %s .. ' % name, nl=False)
            v1_deployments.delete(name=name, namespace=enh_settings['name_space'])
            click.secho('OK', fg='green')
            return True
        except Exception as e:
            click.secho('FAILED', fg='red')
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
    
    # Retrieve pods
    def getPODs(self, enh_settings):
        try:
            ocpappsim_pods = []
            v1_pods = self.redHatOcpClient.resources.get(api_version='v1', kind='Pod')
            pods = v1_pods.get(namespace=enh_settings['name_space'])
            for pod in pods.items:
                ocpappsim_pods.append(pod.metadata.name)
            return ocpappsim_pods
            
        except Exception as e:
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False
    
    # Get host of the route that makes the pod accessible
    def getPodRouteHost(self, podid, enh_settings):
        try:
            route_name = Constants.OCP_APP_NAME+str(podid)+'-route'
            v1_routes = self.redHatOcpClient.resources.get(api_version='v1', kind='Route')
            route = v1_routes.get(namespace=enh_settings['name_space'], name=route_name)
            return route.spec.host
            
        except Exception as e:
            click.secho("Operation failed with error: %s" % str(e), fg='red', bold=True, err=True)
            return False

    # Method to retrieve all storage classes
    def getStorageClasses(self, enh_settings):
        try:
            v1_scs = self.redHatOcpClient.resources.get(api_version='v1', kind='StorageClass')
            sc_list = v1_scs.get()
            if len(sc_list.items) > 0:
                click.secho(">> Please use one of the storage classes defined in the cluster:", fg='white', bold=False, err=False)
                for sc in sc_list.items:
                    name = "  - "+sc.metadata.name
                    click.secho(name, fg='white', bold=False, err=False)
            else:
                click.secho(">> There are no storage classes defined in the cluster", fg='white', bold=False, err=False)
            return True
        except Exception as e:
            return False
