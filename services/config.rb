## This file was auto-generated by CloudCoreo CLI
## This file was automatically generated using the CloudCoreo CLI
##
## This config.rb file exists to create and maintain services not related to compute.
## for example, a VPC might be maintained using:
##
## coreo_aws_vpc_vpc "my-vpc" do
##   action :sustain
##   cidr "12.0.0.0/16"
##   internet_gateway true
## end
##

coreo_aws_iam_policy "${KUBE_MASTER_NAME}" do
  action :sustain
  policy_name "${KUBE_MASTER_NAME}ServerIAMPolicy"
  policy_document <<-EOH
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1436895015000",
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInstanceStatus",
        "ec2:ModifyInstanceAttribute",
        "ec2:DescribeInstanceAttribute",
        "ec2:DescribeRegions",
        "ec2:ModifyInstanceAttribute",
        "ec2:ReplaceRoute",
        "ec2:CreateRoute",
        "ec2:ReplaceRouteTableAssociation",
        "ec2:DescribeSubnets",
        "ec2:DescribeRouteTables",
        "ec2:AssociateAddress",
        "ec2:DescribeAddresses",
        "ec2:DisassociateAddress",
        "ec2:DescribeInstances",
        "ec2:DescribeTags" 
      ],
      "Resource": [
        "*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeRouteTables"
      ],
      "Resource": "*"
    }
  ]
}
EOH
end

coreo_aws_ec2_autoscaling "${KUBE_MASTER_NAME}" do
  action :sustain 
  minimum 1
  maximum 1
  server_definition "${KUBE_MASTER_NAME}"
  subnet "${PRIVATE_SUBNET_NAME}"
  elbs ["${KUBE_MASTER_NAME}-elb"]
  health_check_grace_period ${KUBE_MASTER_HEALTH_CHECK_GRACE_PERIOD}
  upgrade({
            :replace => "in-place",
            :upgrade_on => "dirty",
            :cooldown => ${KUBE_MASTER_UPGRADE_COOLDOWN}
        })
end
