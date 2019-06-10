import subprocess
import sys # To do File input output operations
import os # for certain command for saving as file
import getopt # for better params input handling instead of directly using argv.
from collections import OrderedDict # For using Ordered dict
from ruamel.yaml import YAML #To create YAML File and Read YAML File

## Global variable
args = []
opts = []
optsdict = {}


## Global functions
# Execute command and get output as string
def exec_get_output(cmd,val=False):
	out = subprocess.Popen(cmd,
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT,shell=val)
	out.wait()
	stdout,stderr = out.communicate()
	return stdout


# Replace every string with name "string_to_replace" in a file with input .
def replace_with_input(filename,input,string_to_replace):
	# Read in the file
	with open(filename, 'r') as file :
  		filedata = file.read()
	# Replace the target string
	filedata = filedata.replace(string_to_replace, input)
	# Write the file out again
	with open(filename, 'w') as file:
	  file.write(filedata)
	

# Merge yaml file together separating with ---, 
# this is meant for constructing the access--nsname-username-accesskind.yaml by merging
# sa.yaml, role.yaml and rolebinding.yaml
def merge_files(filenames,outfile_name):
	with open(outfile_name, 'w') as outfile:
		for fname in filenames:
			with open(fname) as infile:
				outfile.write("\n---\n")
				outfile.write(infile.read())
				outfile.write("\n")


# This will create a config file using the provided name of namespace and username of the service account.
def create_config(namespace_name,namespace_username):
	# Get name of the secret format "mynamespace-user-token-xxxxx" of the created service account
	secret_name = exec_get_output(["kubectl","get","sa",namespace_username,"-n",namespace_name,"-o","jsonpath='{.secrets[0].name}'"])

	# Get service account token
	cmd_token = "kubectl get secret " + secret_name[1:len(secret_name)-1] + " -n " + namespace_name +" -o 'jsonpath={.data.token}' | base64 -d"
	token = exec_get_output(cmd_token,True)

	# Get service account certificate 
	cmd_cert = "kubectl get secret " + secret_name[1:len(secret_name)-1] + " -n " + namespace_name +" -o \"jsonpath={.data['ca\\.crt']}\""
	certificate = exec_get_output(cmd_cert,True)

	# Get IP address, NAME of the cluster, THIS MIGHT BE A PROBLEM IF THERE ARE MORE THAN ONE CLUSTER SO MAYBE THIS SHOULD BE SUPPLIED INSTEAD.
	kubernetes_api_endpoint = exec_get_output(["kubectl","config","view","--minify","-o","jsonpath='{.clusters[0].cluster.server}'"])
	cluster_name = exec_get_output(["kubectl","config","view","--minify","-o","jsonpath='{.clusters[0].name}'"])

	# Insert provided value in kubeconfigform
	config_file_name = namespace_username + "config"
	exec_get_output(["cp","./forms/kubeconfigform",config_file_name])

	replace_with_input(config_file_name,namespace_name,"NAMESPACE_NAME")
	replace_with_input(config_file_name,namespace_username,"NAMESPACE_USERNAME")

	replace_with_input(config_file_name,token,"TOKEN")
	replace_with_input(config_file_name,certificate,"CERTIFICATE")

	replace_with_input(config_file_name,kubernetes_api_endpoint,"KUBERNETES_API_ENDPOINT")
	replace_with_input(config_file_name,cluster_name,"CLUSTERNAME")

	#Success message
	print("SYSTEM MESSAGE:")
	print("Config file for namespace " + namespace_name + " at cluster " + cluster_name + " is created\n")


# This create namespace, service account, role , rolebindings and create a config file based on those infos.
# accesskind is either admin, user or viewer (check repo for more detailed what they do)
def generate_new_config(namespace_name,namespace_username,action,accesskind="",role_file_path="",resourcelimitfilepath=""):
	# copy from the forms then replace the name of role referred in rolebinding.yaml.
	exec_get_output(["cp","./forms/rolebinding.yaml","./"])

	# use ruamel.yaml to take the name field from role.yaml to rolebindings
	if role_file_path=="":
		role_file_path = './forms/role-' + accesskind +'.yaml'  ## Read the Yaml File
		access_file_name = "access-" + namespace_name + "-" + namespace_username + "-" + accesskind +".yaml"
	else:
		access_file_name = "access-" + namespace_name + "-" + namespace_username + "-Custom"  +".yaml"

	file1 = open(role_file_path).read()
	yaml = YAML() ## Load the yaml object

	code1 = yaml.load(file1) #Load content of YAML file to yaml object
	file2 = open("rolebinding.yaml").read()  ## Read the Yaml File

	yaml = YAML() ## Load the yaml object
	code2 = yaml.load(file2) #Load content of YAML file to yaml object

	code2["roleRef"]["name"] = code1["metadata"]["name"]
	writefile = open("rolebinding.yaml", "w")

	yaml.dump(code2,writefile)
	writefile.close()

	# After editing with ruamel.yaml merge everything to a single file and apply.
	merge_files(['./forms/sa.yaml', role_file_path, 'rolebinding.yaml'],access_file_name)

	# Replace namespace_name in access.yaml with input provided.
	replace_with_input(access_file_name,namespace_name,"NAMESPACE_NAME")
	replace_with_input(access_file_name,namespace_username,"NAMESPACE_USERNAME")


	# Create namespace and then apply the access.yaml file 
	# to create a service account bound to that namespace
	actioncheck = ["createEx","createExCustomRole"]
	if(action not in actioncheck):
		print(exec_get_output(["kubectl","create","namespace",namespace_name]))
	print(exec_get_output(["kubectl","create","-f",access_file_name]))

	# We'll now make a directory to contain all access-file for the namespace.
	# If the folder does not already exist then we create one and then move the accessfile inside.
	if(exec_get_output('[ -d '+ namespace_name + ' && echo "exist"',True)!="exist"):
		exec_get_output("mkdir " + namespace_name,True)
	exec_get_output("mv " + access_file_name + " ./" + namespace_name,True)
	create_config(namespace_name,namespace_username)

	# Cleaning up 
	exec_get_output(["rm","-rf","sa.yaml", "role.yaml", "rolebinding.yaml"])


# Given the config files this will merge everything and output it to "KUBECONFIG"
def merge_configs(files):
	cmd = "export KUBECONFIG=mergedconfig"
	for name in files:
		cmd = cmd + ":" + name
	os.environ["KUBECONFIG"] = cmd
	cmd = "kubectl config view --flatten  > mergedconfig"
	exec_get_output(cmd,True)
	os.environ["KUBECONFIG"] = "$HOME/.kube/config"


# Given a resource quota yaml file, apply it on a namespace using kubectl.
def limit_resources(resourcelimitfilepath,namespace_name):
	# we need to change the namespace in the yaml file for each namespace 
	# so that the same file can be applied
	print(exec_get_output("kubectl apply -f " + resourcelimitfilepath + " -n " + namespace_name,True))

	exec_get_output("cp " + resourcelimitfilepath + " ./" + namespace_name,True)


# Syntax "python ConstructAccess.py merge file1 file2 file3"
def case1():
	merge_configs(list(sys.argv[2:]))


# Syntax "python ConstructAccess.py create --akind access_kind namespace1 namespace2 ... namespaceN"
def case2():
	type(optsdict)
	for elem in args:
		namespace_username = elem + "-user"
		generate_new_config(elem,namespace_username,sys.argv[1],optsdict['--akind'])


# Syntax "python ConstructAccess.py createEx --nsname namespace_name --akind access_kind username1  ... usernameN"
def case3():
	for elem in args:
		generate_new_config(optsdict['--nsname'],elem,sys.argv[1],optsdict['--akind'])


# Syntax "python ConstructAccess.py createCustomRole --rpath role_file_path namespace1 namespace2 ... namepspaceN"
def case4():
	for elem in args:
		namespace_username = elem + "-user"
		generate_new_config(elem,namespace_username,sys.argv[1],role_file_path=optsdict['--rpath'])


# Syntax "python ConstructAccess.py createExCustomeRole --nsname namespace_name --rpath role_file_path username1 username2 .... usernameN"
def case5():
	for elem in args:
		generate_new_config(optsdict['--nsname'],elem,sys.argv[1],role_file_path=optsdict['--rpath'])


# Syntax "python ConstructAccess.py recreate --nsname namespace_name username1 username2 username3 ... usernameN"
def case6():
	for elem in args:
		create_config(sys.argv[2],elem)


# Syntax "python ConstructAccess.py limitRes --rlpath ResourceQuotafilepath namespace1 ... namespaceN"
def case7():
	print(args)
	for elem in args:
		limit_resources(optsdict['--rlpath'],elem)


# all flags and their shorthands, 
# --nsname -a
# --uname -b
# --akind -c
# --rpath -d
# -rlpath -e
if __name__ == '__main__':
	cases = {"merge":case1,"create":case2,"createEx":case3,"createCustomRole":case4,
	"createExCustomRole":case5,"recreate":case6,"limitRes":case7}
	try:
		opts, args = getopt.getopt(sys.argv[2:], 'a:b:c:d:e:',['nsname=', 'uname=','akind=','rpath=','rlpath='])
	except getopt.GetoptError:
		print("Input Error")
		sys.exit(2)
	optsdict = dict(opts)
	cases[sys.argv[1]]()



	



