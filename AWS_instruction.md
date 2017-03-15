Setup an Admin node. it could be local machine or an aws EC2 instance.


install cfncluster on ADMIN https://github.com/awslabs/cfncluster or
 `sudo pip install cfncluster`
 ver cfncluster-1.3.1
 ref: https://cfncluster.readthedocs.io/en/latest/getting_started.html

2. Create custom AMI for cfncluster nodes

http://cfncluster.readthedocs.io/en/latest/ami_customization.html
Create EC2 instance using Community AMI
16.04 ami-751f5315
14.04 ami-40185420
List of AMIs https://github.com/awslabs/cfncluster/blob/master/amis.txt

Installed packages CFN_AMI11 ami-62194a02, in Community AMIs now.

Run `cfncluster configure`
or
cp /usr/local/lib/python2.7/dist-packages/cfncluster/examples/config to /home/yuncong/.cfncluster
http://cfncluster.readthedocs.io/en/latest/configuration.html
custom_ami - ami-XXXXXXX
base_os - ubuntu14.04
compute_instance_type - m4.4xlarge
master_instance_type - m4.2xlarge
ebs_settings - custom
master_root_volume_size - 30
compute_root_volume_size - 30
volume_size - 50
vpc_id - see instance description
master_subnet_id - see instance description
aws_access_key_id - use access key, not IAM
aws_secret_access_key
aws_region_name
key_name

cluster name must satisfy regular expression pattern: [a-zA-Z][-a-zA-Z0-9]

Output:"MasterPublicIP"="52.53.116.181"
Output:"MasterPrivateIP"="172.31.21.42"
Output:"GangliaPublicURL"="http://52.53.116.181/ganglia/"
Output:"GangliaPrivateURL"="http://172.31.21.42/ganglia/"


aws:cloudformation:logical-id MasterServer
Name Master
Application cfncluster-yuncongCluster
aws:cloudformation:stack-name cfncluster-yuncongCluster
aws:cloudformation:stack-id arn:aws:cloudformation:us-west-1:481653826516:stack/cfncluster-yuncongCluster/1ac6a000-07b1-11e7-9f08-500c59637e99

aws:cloudformation:logical-id ComputeFleet
aws:autoscaling:groupName cfncluster-yuncongCluster-ComputeFleet-WT43OF80V223
Name Compute
Application cfncluster-yuncongCluster
aws:cloudformation:stack-id arn:aws:cloudformation:us-west-1:481653826516:stack/cfncluster-yuncongCluster/1ac6a000-07b1-11e7-9f08-500c59637e99
aws:cloudformation:stack-name cfncluster-yuncongCluster


Then access with
`ssh -i aws/YuncongKey.pem ubuntu@ec2-54-67-87-143.us-west-1.compute.amazonaws.com`
Must specify `custom_ami` or `base_os` otherwise you cannot SSH to either master or compute nodes.

Security Group: Must enable defaultVPC and "AllowSSH22"

# Build Customized AMI #
http://cfncluster.readthedocs.io/en/latest/ami_customization.html

Must use a standalone instance. Should not use cluster's master or compute node.

The base CfnCluster AMI is often updated with new releases. This AMI has all of the components required for CfnCluster to function installed and configured. If you wish to customize an AMI for CfnCluster, you must start with this as the base.

Find the AMI which corresponds with the region you will be utilizing in the list here: https://github.com/awslabs/cfncluster/blob/master/amis.txt.
Within the EC2 Console, choose "Launch Instance".
Navigate to "Community AMIs", and enter the AMI id for your region into the search box.
Select the AMI, choose your instance type and properties, and launch your instance.
Log into your instance using the ec2-user and your SSH key.
Customize your instance as required
Run the following command to prepare your instance for AMI creation:
`sudo /usr/local/sbin/ami_cleanup.sh`
Stop the instance
Create a new AMI from the instance
Enter the AMI id in the custom_ami field within your cluster configuration.

# Performance Tuning Settings #

## NFS ##
Use master instance type - m4.2xlarge, larger memory on NFS server for a performance improvement (Runtime measured for Align step of Global Align)
Instance Type	Runtime
t2.micro	2687 seconds
m4.2xlarge	671 seconds
Set async option for NFS
Edit `/etc/exports`, change sync to async
Restart NFS server  `sudo service nfs-kernel-server restart `

## Sun Grid Engine ##
Add user ubuntu to list of all grid managers
Change to super user `sudo -i`
Set environment variable `$SGE_ROOT`: `export SGE_ROOT=/opt/sge`
Add user: `/opt/sge/bin/lx-amd64/qconf -am ubuntu`
Set minimum memory requirement to allow scheduling on a node as 5 GB: `qconf -mc` Change 0 under mem_free to 5G
Change SGE schedule interval: `qconf -msconf` Change schedule_interval to 0:0:15


https://ucsd-mousebrainatlas-scripts.s3.amazonaws.com/set_env.sh
#!/bin/bash
echo "export RAW_DATA_DIR='/shared/data/CSHL_data'
export DATA_DIR='/shared/data/CSHL_data_processed'
export VOLUME_ROOTDIR='/shared/data/CSHL_volumes2'
export SCOREMAP_VIZ_ROOTDIR='/shared/data/CSHL_lossless_scoremaps_Sat16ClassFinetuned_v2'
export SVM_ROOTDIR='/shared/data/CSHL_patch_features_Sat16ClassFinetuned_v2_classifiers/'
export PATCH_FEATURES_ROOTDIR='/shared/data/CSHL_patch_features_Sat16ClassFinetuned_v2'
export SPARSE_SCORES_ROOTDIR='/shared/data/CSHL_patch_Sat16ClassFinetuned_v2_predictions'
export SCOREMAPS_ROOTDIR='/shared/data/CSHL_lossless_scoremaps_Sat16ClassFinetuned_v2'
export HESSIAN_ROOTDIR='/shared/data/CSHL_hessians/'
export REPO_DIR='/shared/MouseBrainAtlas'
export LABELING_DIR='/shared/CSHL_data_labelings_losslessAlignCropped'" >> /home/ubuntu/.bashrc