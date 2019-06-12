import subprocess
import sys # To do File input output operations
import os # for certain command for saving as file
import getopt # for better params input handling instead of directly using argv.
from collections import OrderedDict # For using Ordered dict
from ruamel.yaml import YAML #To create YAML File and Read YAML File


## Textcolors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

## Global variable
args = []
opts = []
optsdict = {}
all_access_kinds = ["admin","user","viewer"]
# this is for case8, also known as the help function or printing out the correct text at a certain error.
ErrorSyntax = {"create": "create -a access_kind namespace1 ... namespaceN",
	"createEx": "createEx -n namespace_name -a access_kind username1  ... usernameN",
	"createCustomRole": "createCustomRole -r role_file_path namespace1 ... namepspaceN",
	"createExCustomeRole": "createExCustomeRole -n namespace_name -r role_file_path username1 .... usernameN",
	"recreate": "recreate -n namespace_name username1 ... usernameN",
	"limit": "limit -l ResourceQuotafilepath namespace1 ... namespaceN"
	}
ErrorDescription = {"create": "  Description: Create config for N namespaces with N users of access_kind\n",
	"createEx": "  Description: Create config for N users of access_kind in namespace namespace_name\n",
	"createCustomRole": "  Description: Create config for N namespaces with N users of custom access\n",
	"createExCustomeRole": "  Description: Create config for N users of custom access in namespace namespace_name\n",
	"recreate": "  Description: Re-fetch config file for N users in namespace namespace_name\n",
	"limit": "  Description: Limit resource with resource-quota-yaml-file on N namespaces\n"
	}



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
# this is meant for constructing the access--nsname-username-access_kind.yaml by merging
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
	exec_get_output(["cp","./templates/kubeconfigform",config_file_name])

	replace_with_input(config_file_name,namespace_name,"NAMESPACE_NAME")
	replace_with_input(config_file_name,namespace_username,"NAMESPACE_USERNAME")

	replace_with_input(config_file_name,token,"TOKEN")
	replace_with_input(config_file_name,certificate,"CERTIFICATE")

	replace_with_input(config_file_name,kubernetes_api_endpoint,"KUBERNETES_API_ENDPOINT")
	replace_with_input(config_file_name,cluster_name,"CLUSTERNAME")

	#Success message
	print(bcolors.FAIL + "SYSTEM MESSAGE:" + bcolors.ENDC)
	print(bcolors.OKGREEN + "Config file for namespace " + namespace_name + " at cluster " + cluster_name + " is created\n" + bcolors.ENDC)


# This create namespace, service account, role , rolebindings and create a config file based on those infos.
# access_kind is either admin, user or viewer (check repo for more detailed what they do)
def generate_new_config(namespace_name,namespace_username,action,access_kind="",role_file_path="",resourcelimitfilepath=""):
	# copy from the templates then replace the name of role referred in rolebinding.yaml.
	exec_get_output(["cp","./templates/rolebinding.yaml","./"])

	# use ruamel.yaml to take the name field from role.yaml to rolebindings
	if role_file_path=="":
		role_file_path = './templates/role-' + access_kind +'.yaml'  ## Read the Yaml File
		access_file_name = "access-" + namespace_name + "-" + namespace_username + "-" + access_kind +".yaml"
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
	merge_files(['./templates/sa.yaml', role_file_path, 'rolebinding.yaml'],access_file_name)

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
	access_kind = optsdict.get('--akind')
	# If access_kind is None then we assume that it's the shorthand kind of input
	if access_kind not in all_access_kinds:
		access_kind = optsdict.get('-a')
	if access_kind not in all_access_kinds:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("create"))
		print(ErrorDescription.get("create"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			namespace_username = elem + "-user"
			generate_new_config(elem,namespace_username,sys.argv[1],access_kind)


# Syntax "python ConstructAccess.py createEx --nsname namespace_name --akind access_kind username1  ... usernameN"
def case3():
	access_kind = optsdict.get('--akind')
	# If access_kind is None then we assume that it's the shorthand kind of input
	if access_kind not in all_access_kinds:
		access_kind = optsdict.get('-a')

	namespace_name = optsdict.get('--nsname')
	# If namespace_name is None then we assume that it's the shorthand kind of input
	if namespace_name==None:
		namespace_name = optsdict.get('-n')
	if(access_kind not in all_access_kinds or namespace_name==None):
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createEx"))
		print(ErrorDescription.get("createEx"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	for elem in args:
		generate_new_config(namespace_name,elem,sys.argv[1],access_kind)


# Syntax "python ConstructAccess.py createCustomRole --rpath role_file_path namespace1 namespace2 ... namepspaceN"
def case4():
	rpath=optsdict.get('--rpath')
	# If rpath is None then we assume that it's the shorthand kind of input
	if rpath==None:
		rpath=optsdict.get('-r')
	if rpath==None:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createCustomRole"))
		print(ErrorDescription.get("createCustomRole"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	for elem in args:
		namespace_username = elem + "-user"
		generate_new_config(elem,namespace_username,sys.argv[1],role_file_path=rpath)


# Syntax "python ConstructAccess.py createExCustomeRole --nsname namespace_name --rpath role_file_path username1 username2 .... usernameN"
def case5():
	namespace_name = optsdict.get('--nsname')
	# If namespace_name is None then we assume that it's the shorthand kind of input
	if namespace_name==None:
		namespace_name = optsdict.get('-n')
	rpath=optsdict.get('--rpath')
	# If rpath is None then we assume that it's the shorthand kind of input
	if rpath==None:
		rpath=optsdict.get('-r')
	if(rpath==None or namespace_name==None):
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createExCustomeRole"))
		print(ErrorDescription.get("createExCustomeRole"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	for elem in args:
		generate_new_config(namespace_name,elem,sys.argv[1],role_file_path=rpath)


# Syntax "python ConstructAccess.py recreate --nsname namespace_name username1 username2 username3 ... usernameN"
def case6():
	for elem in args:
		create_config(sys.argv[2],elem)


# Syntax "python ConstructAccess.py limit --lpath ResourceQuotafilepath namespace1 ... namespaceN"
def case7():
	lpath=optsdict.get('--lpath')
	# If lpath is None then we assume that it's the shorthand kind of input
	if lpath==None:
		lpath=optsdict.get('-l')
	if lpath==None:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("limit"))
		print(ErrorDescription.get("limit"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	for elem in args:
		limit_resources(lpath,elem)


# Syntax "python ConstructAccess.py help " 
# This print all commands syntax for you
def case8():
	print(bcolors.FAIL + "All commands: with python ConstructAccess.py plus these commands below\n" + bcolors.ENDC)
	print(ErrorSyntax.get("create"))
	print(ErrorDescription.get("create"))
	print(ErrorSyntax.get("createEx"))
	print(ErrorDescription.get("createEx"))
	print(ErrorSyntax.get("createCustomRole"))
	print(ErrorDescription.get("createCustomRole"))
	print(ErrorSyntax.get("createExCustomeRole"))
	print(ErrorDescription.get("createExCustomeRole"))
	print(ErrorSyntax.get("recreate"))
	print(ErrorDescription.get("recreate"))
	print(ErrorSyntax.get("limit"))
	print(ErrorDescription.get("limit"))

# all flags and their shorthands, 
# --nsname -n
# --uname -u
# --akind -a
# --rpath -r
# --lpath -l
if __name__ == '__main__':
	cases = {"merge":case1,"create":case2,"createEx":case3,"createCustomRole":case4,
	"createExCustomRole":case5,"recreate":case6,"limit":case7,"help":case8}
	try:
		opts, args = getopt.getopt(sys.argv[2:], 'n:u:a:r:l:',['nsname=', 'uname=','akind=','rpath=','lpath='])
	except getopt.GetoptError:
		print(bcolors.FAIL + "Input Error" + bcolors.ENDC)
		sys.exit(2)
	optsdict = dict(opts)
	if sys.argv[1] not in cases:
		## print help
		case8()
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	cases[sys.argv[1]]()



	



