import subprocess
import sys # To do File input output operations
import os # for certain command for saving as file
import getopt # for better params input handling instead of directly using argv.
from collections import OrderedDict # For using Ordered dict
from ruamel.yaml import YAML #To create YAML File and Read YAML File
from optparse import OptionParser
from optparse import Option, OptionValueError

# multi values option parser class
class MultipleOption(Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            values.ensure_value(dest, []).append(value)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)

# --method -m
# --nsname -n
# --uname -u
# --unsname -uns
# --akind -a
# --rpath -r
# --lpath -l
def option_parse_init():
	long_commands = ('nsname','uname','akind','rpath','lpath','unsname')
	short_commands = {'a':'akind','u':'uname'}
	parser = OptionParser(option_class=MultipleOption)

	parser.add_option('-m', '--method', 
              action="extend", type="string",
              dest='method',
              help='method to use: create , createEx .. ')

	parser.add_option('-n', '--nsname', 
	              action="extend", type="string",
	              dest='nsname',
	              help='namespace name')

	parser.add_option('-u', '--uname', 
              action="extend", type="string",
              dest='uname',
              help='service account username')

	parser.add_option('-a', '--akind', 
	              action="extend", type="string",
	              dest='akind',
	              help='access kind: admin , user, viewer')

	parser.add_option('-r', '--rpath', 
	              action="extend", type="string",
	              dest='rpath',
	              help='custom role file path to use')
	parser.add_option('-l', '--lpath', 
	              action="extend", type="string",
	              dest='lpath',
	              help='lpath resource quota limit file path to use')
	parser.add_option('-s','--unsname', 
	              action="extend", type="string",
	              dest='unsname',
	              help='namespace name of the service account user')	

	return parser

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
# this is for help, also known as the help function or printing out the correct text at a certain error.
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
def replace_file_word_with_input(filename,input,string_to_replace):
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

	replace_file_word_with_input(config_file_name,namespace_name,"NAMESPACE_NAME")
	replace_file_word_with_input(config_file_name,namespace_username,"NAMESPACE_USERNAME")

	replace_file_word_with_input(config_file_name,token,"TOKEN")
	replace_file_word_with_input(config_file_name,certificate,"CERTIFICATE")

	replace_file_word_with_input(config_file_name,kubernetes_api_endpoint,"KUBERNETES_API_ENDPOINT")
	replace_file_word_with_input(config_file_name,cluster_name,"CLUSTERNAME")

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
	replace_file_word_with_input(access_file_name,namespace_name,"NAMESPACE_NAME")
	replace_file_word_with_input(access_file_name,namespace_username,"NAMESPACE_USERNAME")
	replace_file_word_with_input(access_file_name,namespace_username,"SA_USERNAME")

	# Create namespace and then apply the access.yaml file 
	# to create a service account bound to that namespace
	actioncheck = ["createEx","createExCustomRole"]
	if action not in actioncheck:
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

# Adding roles in other namespaces for an existing service account.
# No config file will be generated, the old one can be reused.
def addRoles(sa_username,sa_user_namespace_name,ns_list,akind_list) :
	if len(ns_list) != len(akind_list) :
		print ("Error number of specified namespaces and number of access kinds are not equal")
		return ""

	files_to_append = []
	access_file_name = "multiNsAccess-" + sa_username + '-' + sa_user_namespace_name + ".yaml"

	for i in range(0,len(ns_list)):
		namespace_name = ns_list.pop(0)
		namespace_username = namespace_name + "-" + str(i)
		access_kind = akind_list.pop(0)
		print(exec_get_output(["kubectl","create","namespace",namespace_name]))
		# only the first name space and the user name is enough
		# create_config(namespace_name,namespace_username)
		# copy from the templates then replace the name of role referred in rolebinding.yaml.
		role_file_path = "./role-" + str(i)
		rolebinding_file_path = "./rolebinding-" + namespace_username

		exec_get_output(["cp","./templates/rolebinding.yaml",rolebinding_file_path])
		exec_get_output(["cp",'./templates/role-' + access_kind + '.yaml', role_file_path])

		files_to_append.append(role_file_path)
		files_to_append.append(rolebinding_file_path)

		# Copy role name over to rolebinding
		file1 = open(role_file_path).read()
		yaml = YAML() ## Load the yaml object
		code1 = yaml.load(file1) #Load content of YAML file to yaml object

		file2 = open(rolebinding_file_path).read()  ## Read the Yaml File
		yaml = YAML() ## Load the yaml object
		code2 = yaml.load(file2) #Load content of YAML file to yaml object

		print(code2["subjects"][0]['name'])
		code2["roleRef"]["name"] = code1["metadata"]["name"]
		code2["subjects"][0]["name"] = sa_username
		code2["subjects"][0]["namespace"] = sa_user_namespace_name
		writefile = open(rolebinding_file_path, "w")

		yaml.dump(code2,writefile)
		writefile.close()

		# Edit the role file
		replace_file_word_with_input(role_file_path,namespace_name,"NAMESPACE_NAME")
		replace_file_word_with_input(role_file_path,namespace_username,"NAMESPACE_USERNAME")

		# Edit the rolebinding file
		replace_file_word_with_input(rolebinding_file_path,namespace_name,"NAMESPACE_NAME")
		replace_file_word_with_input(rolebinding_file_path,namespace_username,"NAMESPACE_USERNAME")

	# After editing with ruamel.yaml merge everything to a single file and apply.
	merge_files(files_to_append,access_file_name)
	if(exec_get_output('[ -d '+ "multiNsAccess-" + sa_user_namespace_name + ' && echo "exist"',True)!="exist"):
		exec_get_output("mkdir " + "multiNsAccess-" + sa_user_namespace_name,True)
	else:
		# do nothing
		print()
	print(exec_get_output(["kubectl","create","-f",access_file_name]))
	# if file exists then append it.
	if os.path.isfile("multiNsAccess-" + sa_user_namespace_name + "/" + access_file_name) :
		files = ["multiNsAccess-" + sa_user_namespace_name + "/" + access_file_name]
		files.append(access_file_name)
		merge_files(files_to_append,"multiNsAccess-" + sa_user_namespace_name + "/" + access_file_name)
	else:
		exec_get_output("mv " + access_file_name + " multiNsAccess-" + sa_user_namespace_name,True)

	# Cleaning up 
	to_be_del = ' '.join(files_to_append) 
	exec_get_output("rm -rf sa.yaml " + to_be_del,True)

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

# Syntax "python ConstructAccess.py help " 
# This print all commands syntax for you
def help():
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

# Syntax "python ConstructAccess.py merge file1 file2 file3"
def merge():
	merge_configs(list(sys.argv[2:]))


# Syntax "python ConstructAccess.py create --akind access_kind namespace1 namespace2 ... namespaceN"
def create():
	access_kind = optsdict.get('akind')[0]
	action = optsdict.get('method')[0]
	if access_kind not in all_access_kinds:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("create"))
		print(ErrorDescription.get("create"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			namespace_username = elem + "-user"
			generate_new_config(elem,namespace_username,action,access_kind)


# Syntax "python ConstructAccess.py createEx --nsname namespace_name --akind access_kind username1  ... usernameN"
def createEx():
	access_kind = optsdict.get('akind')[0]
	action = optsdict.get('method')[0]
	namespace_name = optsdict.get('nsname')[0]
	# If namespace_name is None then we assume that it's the shorthand kind of input
	if namespace_name==None:
		namespace_name = optsdict.get('-n')
	if(access_kind not in all_access_kinds or namespace_name==None):
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createEx"))
		print(ErrorDescription.get("createEx"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			generate_new_config(namespace_name,elem,action,access_kind)


# Syntax "python ConstructAccess.py createCustomRole --rpath role_file_path namespace1 namespace2 ... namepspaceN"
def createCustomRole():
	rpath=optsdict.get('rpath')[0]
	action = optsdict.get('method')[0]
	if rpath==None:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createCustomRole"))
		print(ErrorDescription.get("createCustomRole"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			namespace_username = elem + "-user"
			generate_new_config(elem,namespace_username,action,role_file_path=rpath)


# Syntax "python ConstructAccess.py createExCustomeRole --nsname namespace_name --rpath role_file_path username1 username2 .... usernameN"
def createExCustomRole():
	namespace_name = optsdict.get('nsname')[0]
	rpath=optsdict.get('rpath')[0]
	action = optsdict.get('method')[0]
	if(rpath==None or namespace_name==None):
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("createExCustomeRole"))
		print(ErrorDescription.get("createExCustomeRole"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			generate_new_config(namespace_name,elem,action,role_file_path=rpath)


# Syntax "python ConstructAccess.py recreate --nsname namespace_name username1 username2 username3 ... usernameN"
def recreate():
	for elem in args:
		create_config(sys.argv[2],elem)


# Syntax "python ConstructAccess.py limit --lpath ResourceQuotafilepath namespace1 ... namespaceN"
def limit():
	lpath=optsdict.get('lpath')
	action = optsdict.get('method')[0]
	if lpath==None:
		## print help
		print("Do you mean this ?\n")
		print(ErrorSyntax.get("limit"))
		print(ErrorDescription.get("limit"))
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		for elem in args:
			limit_resources(lpath,elem)

# Syntax python ConstructAccess.py -m addRoles -u sa_user_name -s sa_user_namespace -n namespace_1 -n namespace_2 -a access_kind_for_namespace_2 
def addRoles():
	sa_username = optsdict['uname'][0]
	sa_user_namespace_name = optsdict['unsname'][0]
	ns_list = optsdict['nsname']
	akind_list = optsdict['akind']
	addRoles(sa_username,sa_user_namespace_name,ns_list,akind_list)


# all flags and their shorthands, 
# --nsname -n
# --uname -u
# --unsname -uns
# --akind -a
# --rpath -r
# --lpath -l
if __name__ == '__main__':
	methods = {"help":help,"merge":merge,"create":create,"createEx":createEx,"createCustomRole":createCustomRole,
	"createExCustomRole":createExCustomRole,"recreate":recreate,"limit":limit,"addRoles":addRoles}

	parser = option_parse_init()
	OPTIONS, args = parser.parse_args()
	optsdict = vars(OPTIONS)
	method_input = optsdict["method"] or ['']
	print(optsdict)
	if method_input[0] not in methods:
		## print help
		help()
		print(bcolors.FAIL + "Invalid input, please double check syntax with the output above" + bcolors.ENDC)
	else:
		methods[optsdict["method"][0]]()
